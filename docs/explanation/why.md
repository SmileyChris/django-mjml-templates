# Why this package

There is already a well-known MJML package for Django, [django-mjml](https://pypi.org/project/django-mjml/),
and it is a good one. This package exists for a different aim: **as few moving parts as
possible, and as little work per email as possible.**

## The short version

- **No Node.** MJML is compiled in-process by [mjml-python](https://pypi.org/project/mjml-python/),
  the Rust [`mrml`](https://github.com/jdrouet/mrml) port. There is no `mjml` binary to install,
  no subprocess to spawn and no server to keep running.
- **One line to adopt.** Swap the backend in `TEMPLATES`. An `.mjml` file is then an ordinary
  Django template that happens to compile to email HTML, so `{% extends %}`, `{% include %}`,
  `{% url %}`, `get_template()` and autoescaping work as they always did.
- **The rest of sending an email is covered.** The subject comes from `<mj-title>`, the plain-text
  body from a sibling `.txt` or a generated fallback, and relative links are made absolute.
  `render_email()` hands back an unsent `EmailMultiAlternatives`.

## Compared with django-mjml

| | django-mjml | django-mjml-templates |
|---|---|---|
| Integration | `{% mjml %}…{% endmjml %}` tag inside a template | Template backend: `.mjml` files are templates (`{% extends %}`, `get_template()`) |
| Compiler | Official `mjml` (Node): `cmd`, TCP server or HTTP API | `mjml-python` (Rust `mrml`), in-process |
| Setup | Install Node and mjml, `INSTALLED_APPS`, pick a backend mode | Swap `BACKEND` in `TEMPLATES` |
| Sending | Not covered | `render_email()` returns an unsent `EmailMultiAlternatives` |
| Subject | Not covered | Taken from `<mj-title>` |
| Plain-text body | Not covered | Sibling `.txt`, or an `html2text` fallback with layout tables unwrapped |
| Absolute URLs | Not covered | Relative `href`/`src`/`url()` rewritten against the request or `MJML_BASE_URL` |
| Preview | Not covered | [`preview_response`](../reference/preview.md), an inbox row plus the HTML and text parts |
| Fidelity to MJML | Reference implementation | `mrml` port, can lag official MJML on newer components |
| Options | Minify, validation level, hosted API | None yet |

## Where this one is a better fit

- **Deploys without Node.** A slim Python image, a serverless function, or a worker that has no
  business running a JavaScript toolchain.
- **Sending from a task or command.** There is no server or subprocess to be up, and no network
  hop per email.
- **Tests.** Rendering an email in a test needs nothing installed beyond Python packages.
- **You want email to feel like the rest of your templates.** Template inheritance, loops, URL
  reversing and your own tags and filters, with no second syntax.

## Where django-mjml is the better pick

- You need the **official** compiler, because `mrml` is a port and can lag on newer MJML
  components. If your design uses something it doesn't render, that settles it.
- You want its **options**: minification, validation level, or the hosted MJML API.
- You already run Node in your stack and are happy with it.

Both are fine tools. This one trades the reference implementation for being small enough to
forget about.
