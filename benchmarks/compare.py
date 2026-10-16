#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""Time one small email through this package and through django-mjml (cmd and TCP-server modes).

    uv run benchmarks/compare.py [runs]

Needs `uv`, `node` and `npm` (for the official MJML). The two Python packages both install a
top-level `mjml` module, so each is timed in its own throwaway uv environment, from this one
script (re-run as `--worker`). Nothing is installed into the project.
"""

import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

MJML = """<mjml>
  <mj-head>
    <mj-title>Welcome to Paperplane, {{ first }}</mj-title>
    <mj-attributes><mj-all font-family="Helvetica, Arial, sans-serif" /></mj-attributes>
  </mj-head>
  <mj-body background-color="#f3f4f6">
    <mj-section background-color="#4f46e5"><mj-column>
      <mj-text align="center" color="#ffffff" font-size="22px">Paperplane</mj-text>
    </mj-column></mj-section>
    <mj-section background-color="#ffffff"><mj-column>
      <mj-text font-size="24px">Welcome, {{ first }}!</mj-text>
      <mj-text>Your account is ready. Pick a template and send your first message.</mj-text>
      <mj-button href="/start/">Get started</mj-button>
    </mj-column></mj-section>
  </mj-body>
</mjml>
"""

# django-mjml's TCP server protocol: 9-digit length + mjml in; "0"/"1" + 9-digit length + html out.
TCP_SERVER = """const net = require('net'), mjml2html = require('mjml');
net.createServer(sock => {
  let buf = Buffer.alloc(0);
  sock.on('data', async d => {
    buf = Buffer.concat([buf, d]);
    if (buf.length < 9) return;
    const n = parseInt(buf.slice(0, 9).toString());
    if (buf.length < 9 + n) return;
    const src = buf.slice(9, 9 + n).toString(); buf = Buffer.alloc(0);
    let ok = '0', out;
    try { out = (await mjml2html(src)).html; } catch (e) { ok = '1'; out = String(e); }
    const b = Buffer.from(out);
    sock.write(ok + String(b.length).padStart(9, '0')); sock.write(b);
  });
}).listen(28101, '127.0.0.1');
"""


def timed(fn, runs):
    fn()  # warm up
    start = time.perf_counter()
    for _ in range(runs):
        fn()
    return (time.perf_counter() - start) / runs * 1000


def worker(kind, runs, work):
    import django
    from django.conf import settings

    templates = [{"BACKEND": "mjml_templates.django.DjangoTemplates", "DIRS": [work]}]
    if kind == "ours":
        settings.configure(TEMPLATES=templates, ROOT_URLCONF="urls", MJML_BASE_URL="https://example.com")
    else:
        mode = "cmd" if kind == "cmd" else "tcpserver"
        settings.configure(
            INSTALLED_APPS=["mjml"],
            MJML_BACKEND_MODE=mode,
            MJML_EXEC_CMD=f"{work}/node_modules/.bin/mjml",
            TEMPLATES=[
                {"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [work], "APP_DIRS": True}
            ],
        )
    django.setup()
    from django.template.loader import get_template

    if kind == "ours":
        from django.urls import path

        sys.modules["urls"] = type(sys)("urls")
        sys.modules["urls"].urlpatterns = [path("start/", lambda r: None)]
        from mjml import mjml2html

        template = get_template("welcome.mjml")
        compile_ms = timed(lambda: mjml2html(MJML.replace("{{ first }}", "Ann")), runs)
        full_ms = timed(lambda: template.render_email({"first": "Ann"}, to=["a@b.c"]), runs)
        print(f"{compile_ms:.3f} {full_ms:.3f}")
    else:
        template = get_template("welcome_tag.html")
        print(f"{timed(lambda: template.render({'first': 'Ann'}), runs):.3f}")


def uv_run(*with_args, args, env=None):
    cmd = [
        "uv",
        "run",
        "--quiet",
        "--no-project",
        *with_args,
        "python",
        str(Path(__file__).resolve()),
        "--worker",
        *args,
    ]
    return subprocess.run(
        cmd, capture_output=True, text=True, check=True, env={**os.environ, **(env or {})}
    ).stdout.split()


def main(runs):
    for tool in ("uv", "node", "npm"):
        if subprocess.run(["which", tool], capture_output=True).returncode:
            sys.exit(f"{tool} is needed")
    with tempfile.TemporaryDirectory() as work:
        work = str(Path(work).resolve())
        (Path(work) / "welcome.mjml").write_text(MJML)
        (Path(work) / "welcome_tag.html").write_text("{% load mjml %}{% mjml %}" + MJML + "{% endmjml %}")
        (Path(work) / "tcp.js").write_text(TCP_SERVER)
        print("installing the official mjml (npm) ...", file=sys.stderr)
        subprocess.run(["npm", "install", "--silent", "mjml"], cwd=work, check=True)

        compile_ms, full_ms = uv_run(
            "--with", "django", "--with", "mjml-python", "--with-editable", str(ROOT), args=["ours", str(runs), work]
        )
        django_mjml = ("--with", "django", "--with", "django-mjml")
        cmd_runs = max(5, runs // 40)
        (cmd_ms,) = uv_run(*django_mjml, args=["cmd", str(cmd_runs), work])
        try:
            socket.create_connection(("127.0.0.1", 28101), timeout=0.2).close()
            sys.exit("port 28101 is already in use (a leftover mjml TCP server?)")
        except OSError:
            pass
        server = subprocess.Popen(["node", "tcp.js"], cwd=work)
        try:
            for _ in range(50):  # wait for the port
                try:
                    socket.create_connection(("127.0.0.1", 28101), timeout=0.2).close()
                    break
                except OSError:
                    time.sleep(0.1)
            (tcp_ms,) = uv_run(*django_mjml, args=["tcp", str(runs), work])
        finally:
            server.terminate()

    rows = [
        ("this package: compile only (mrml, in-process)", compile_ms, runs),
        ("this package: full render_email()", full_ms, runs),
        ("django-mjml {% mjml %}: TCP server (node already running)", tcp_ms, runs),
        ("django-mjml {% mjml %}: cmd (a node process per email)", cmd_ms, cmd_runs),
    ]
    print(f"\nOne small email, {runs} runs ({cmd_runs} for cmd). Ms per email, lower is faster:\n")
    for label, ms, _ in rows:
        print(f"  {float(ms):9.2f}  {label}")
    print("\nThe full render_email() also builds the subject, the plain text and absolute URLs;")
    print("django-mjml's tag does only the template render and compile.")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--worker"]:
        worker(sys.argv[2], int(sys.argv[3]), sys.argv[4])
    else:
        main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
