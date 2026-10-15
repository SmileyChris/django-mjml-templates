"""A page for looking at an email before it goes: its HTML, its plain text, and a row in an inbox.

Nothing here is wired up for you -- no URL, no setting. A view of your own builds the message
(``render_email``), decides who may see it, and hands it to ``preview_response``.
"""

import html
import re
import secrets
from collections.abc import Collection, Mapping, Sequence
from datetime import timedelta
from email.utils import parseaddr
from pathlib import Path
from typing import Literal, TypedDict, Unpack

from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.template import Context, Engine, TemplateDoesNotExist
from django.template.defaultfilters import filesizeformat
from django.template.loader import select_template
from django.utils import timezone
from django.utils.html import escape, strip_tags, urlize
from django.utils.safestring import SafeString, mark_safe

_PAGE = "mjml_templates/preview.html"
_FRAGMENT = "mjml_templates/preview_fragment.html"
# Our own engine, so the packaged page is always there to fall back on, with nothing installed.
_ENGINE = Engine(dirs=[str(Path(__file__).parent / "templates")])

# MJML's <mj-preview> comes out as a hidden div at the top of the body.
_PREVIEW_DIV = re.compile(r'<div style="display:none;[^"]*">([^<]*)</div>')
_BLOCK_END = re.compile(r"</(?:div|p|td|th|table|h\d)>|<br\s*/?>")
_ANCHOR_HREF = re.compile(r'(<a\b[^>]*?)\shref="([^"]*)"')
_NEW_TAB = ' target="_blank" rel="noopener"'

Tab = Literal["inbox", "html", "text"]
InboxRow = tuple[str, str, str, str]  # sender, subject, snippet, when


def _inbox_line(rendered: str) -> str:
    """What an inbox shows after the subject: the ``<mj-preview>``, then the body's own words,
    which a client runs on into when the preview is short. A preview padded with invisible
    characters (to stop the body leaking in) leaves the client nothing to run on into."""
    body = rendered.split("<body", 1)[-1]
    found = _PREVIEW_DIV.search(body)
    if found:
        body = body.replace(found[0], "", 1)
    body = _BLOCK_END.sub(" ", body)  # a block ends a word; an inline tag doesn't
    words = " ".join(html.unescape(strip_tags("<body" + body)).split())
    preview = html.unescape(found[1]) if found else ""
    if "‌" in preview:
        return preview.replace("͏", "").replace("‌", "").strip()
    return f"{preview.strip()} {words}".strip()[:200]


def _html_and_text(message: EmailMessage) -> tuple[str, str]:
    """The HTML and plain parts of a Django email: an ``EmailMultiAlternatives``' text/html
    alternative, or the body itself when the message is HTML only."""
    if message.content_subtype == "html":
        return message.body, ""
    for content, mimetype, *_ in getattr(message, "alternatives", ()):
        if mimetype == "text/html":
            return content, message.body
    return "", message.body


def _attachment(item) -> tuple[str, str, int]:
    """``(name, mimetype, size)`` of an attachment, whether it is a tuple or a MIME part."""
    if isinstance(item, (tuple, list)):
        name, content, mimetype = item[:3]
        return name, mimetype or "", len(content.encode() if isinstance(content, str) else content)
    payload = item.get_payload(decode=True) or b""
    return item.get_filename() or "", item.get_content_type(), len(payload)


def _neighbours() -> list[InboxRow]:
    """Generic placeholder mail for the Inbox tab, dated back from now so it never looks stale."""
    now = timezone.localtime()
    earlier = now - min(timedelta(hours=2), (now - now.replace(hour=0, minute=0, second=0, microsecond=0)) / 2)
    day = lambda back: (lambda d: f"{d:%b} {d.day}")(now - timedelta(days=back))  # noqa: E731
    return [
        ("Harbour Hardware", "Your order has shipped", "Good news, your parcel is on its way.",
         f"{earlier.hour % 12 or 12}:{earlier:%M} {earlier:%p}"),
        ("Mum", "Sunday lunch?", "Are you free this weekend? Dad wants to try the new place by the wharf.", day(2)),
        ("City Council", "Rates instalment notice", "Your next instalment is due soon. Pay online.", day(4)),
        ("GitHub", "Pull request merged", "Your pull request was merged into main by a collaborator.", day(6)),
        ("Spark Mobile", "Your bill is ready", "Your latest bill is now available in the app.", day(9)),
    ]


def _render(name: str, context: dict) -> str:
    """Rendered through the project's template engines first, so a project overrides a template the
    way it overrides any other (a file of the same name in its own templates); else ours."""
    try:
        template = select_template([name])
    except TemplateDoesNotExist:
        return _ENGINE.get_template(name).render(Context(context))
    return template.render(context)  # outside the try: a broken override should say so, not fall back


class PreviewOptions(TypedDict, total=False):
    attachment_urls: Mapping[str, str] | None
    inbox: bool | Sequence[InboxRow] | None
    tab: Tab | None
    tabs: Collection[Tab] | None
    links: bool
    css: str
    template: str
    context: Mapping[str, object] | None


def preview_fragment(
    message: EmailMessage,
    *,
    attachment_urls: Mapping[str, str] | None = None,
    inbox: bool | Sequence[InboxRow] | None = True,
    tab: Tab | None = None,
    tabs: Collection[Tab] | None = None,
    links: bool = False,
    css: str = "",
    template: str = _FRAGMENT,
    context: Mapping[str, object] | None = None,
) -> SafeString:
    """The preview of ``message``, a Django email (``render_email``'s result, or any ``EmailMessage``):
    what ``.send()`` would send, read from the message itself, as markup to put in a page of your own.

    The tabs are always Inbox, HTML, Text, in that order, minus any the message has nothing for.
    ``tab`` is the one open (``"inbox"``, ``"html"`` or ``"text"``); by default, or when the message
    has no such tab, the first there is (a missing HTML falls back to the text before the inbox).
    ``tabs`` limits which are offered, e.g. ``("html", "text")`` (an ``"html"`` a text-only message
    lacks becomes its ``"text"``), and ``tabs=()`` (falsey, but not ``None``) offers none: just the
    open view, with no tab row. With only one tab, the tab row is not shown either.

    ``inbox`` is the Inbox tab's other mail, shown beneath your message, which is always the first
    row. ``True`` (the default) is a few generic placeholder rows; a list of
    ``(sender, subject, snippet, when)`` tuples is your own; anything falsey leaves the Inbox tab off.
    The generated placeholders are blurred, so the eye stays on your row; your own rows are not.

    Attachments show as a name, type and size; ``attachment_urls`` maps a filename to a URL to
    link it, since the preview does not carry the file.

    ``css`` is added after the fragment's own styles, typically to set its ``--mjml-*`` custom
    properties (see the docs); it is your own markup, not escaped.
    ``links`` makes the links in the HTML and text parts live, opening in a new tab. Off, a click does
    nothing and hovering a link shows where it points: a preview should not confirm an address or
    spend a one-time token. Only the displayed copy changes, never the message.

    ``template`` names the template to render, normally one of your own that
    ``{% extends "mjml_templates/preview_fragment.html" %}`` and fills its blocks (see the docs);
    ``context`` is extra variables for it. The preview's own variables win over a clashing key.

    Raises ``ValueError`` for a message with neither an HTML nor a text body."""
    rendered, plain = _html_and_text(message)
    if not rendered.strip() and not plain.strip():
        raise ValueError(f"{message.subject!r}: the message has neither an HTML nor a text body to preview")
    from_email = message.from_email or ""
    from_name = from_email.rpartition("<")[0].strip().strip('"') or from_email
    if links:
        shown = rendered.replace("<head>", '<head><base target="_blank">', 1)
        # urlize escapes the text itself when told to; its result is markup, so it is safe to mark so.
        linked = urlize(plain, autoescape=True).replace(' rel="nofollow"', "")  # older Django adds its own rel
        text = mark_safe(linked.replace("<a ", f"<a{_NEW_TAB} "))
        sandbox = "allow-popups allow-popups-to-escape-sandbox"
    else:
        shown = _ANCHOR_HREF.sub(r'\1 href="#" title="\2"', rendered)
        text, sandbox = escape(plain), ""
    has = {"inbox": bool(inbox), "html": bool(rendered.strip()), "text": bool(plain.strip())}
    available = [t for t in ("inbox", "html", "text") if has[t]]
    # What a request for a tab the message lacks falls back to: the message itself, not the inbox mock.
    content = [t for t in ("html", "text") if has[t]]
    if tabs is None:
        shown_tabs = available
    elif tabs:
        wanted = set(tabs)
        if "html" in wanted and not has["html"]:
            wanted.add("text")  # the message's own content, whichever form it has
        shown_tabs = [t for t in available if t in wanted] or content[:1] or available[:1]
    else:  # tabs=(): just the open view
        shown_tabs = [tab] if tab in available else (content[:1] if tab else available[:1])
    others = _neighbours() if inbox is True else list(inbox or ())
    urls = attachment_urls or {}
    chips = []
    for name, mimetype, size in map(_attachment, message.attachments):
        url = urls.get(name, "")
        if not url.startswith(("/", "http://", "https://")):
            url = ""  # nothing a preview should link: javascript:, data:, ...
        chips.append((name, mimetype, filesizeformat(size), url))
    variables = {
        **(context or {}),
        "message": message, "from_addr": parseaddr(from_email)[1],
        # Unique per call, so two previews on one page do not share a radio group or an id.
        "uid": f"mp{secrets.token_hex(4)}",
        "subject": message.subject, "text": text, "html": shown, "sandbox": sandbox, "css": css,
        "from_email": from_email, "from_name": from_name, "to": list(message.to),
        "bcc": list(message.bcc), "attachments": chips, "snippet": _inbox_line(rendered or plain),
        "inbox": others, "blur": inbox is True, "tabs": shown_tabs, "bar": len(shown_tabs) > 1,
        "opened": tab if tab in shown_tabs else next(
            (t for t in content if t in shown_tabs and tab), (shown_tabs or [""])[0]
        ),
        # What a click on the message row opens: a tab that is on the page, or nothing to click.
        "open_tab": next((t for t in ("html", "text") if t in shown_tabs), ""),
    }
    return mark_safe(_render(template, variables))


def preview_response(
    message: EmailMessage, *, heading: str = "", **options: Unpack[PreviewOptions]
) -> HttpResponse:
    """``preview_fragment`` as a page of its own, with an optional ``heading``."""
    context = {"fragment": preview_fragment(message, **options), "heading": heading, "subject": message.subject}
    return HttpResponse(_render(_PAGE, context))
