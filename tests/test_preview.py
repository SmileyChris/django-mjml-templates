"""The preview page: what an inbox shows, and that the page carries the message."""

import re

import pytest
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template import engines
from django.test import override_settings
from django.utils.safestring import SafeString

from mjml_templates.preview import _inbox_line as inbox_line
from mjml_templates.preview import preview_fragment, preview_response

SRC = """<mjml><mj-head><mj-title>Hi</mj-title>{preview}</mj-head>
<mj-body><mj-section><mj-column><mj-text>Hello <b>there</b>.</mj-text><mj-text>Second line.</mj-text>
</mj-column></mj-section></mj-body></mjml>"""


def _html(preview=""):
    return engines["django"].from_string(SRC.format(preview=preview)).render()


def test_inbox_line_is_the_preview_then_the_body_words():
    line = inbox_line(_html("<mj-preview>Your receipt</mj-preview>"))
    assert line.startswith("Your receipt Hello there. Second line.")


def test_inbox_line_without_a_preview_is_the_body_words():
    assert inbox_line(_html()) == "Hello there. Second line."


def test_inbox_line_stops_at_a_padded_preview():
    padded = "Your receipt" + "‌͏" * 20
    assert inbox_line(_html(f"<mj-preview>{padded}</mj-preview>")) == "Your receipt"


def _message(subject="Mine", text="t", html="<html><head></head><body>x</body></html>", **kwargs):
    message = EmailMultiAlternatives(subject, text, **{"from_email": "a@b.test", "to": ["c@d.test"]} | kwargs)
    if html:
        message.attach_alternative(html, "text/html")
    return message


def _render(message, **kwargs) -> str:
    return preview_fragment(message, **kwargs)


def _tabs(body) -> list[tuple[str, bool]]:
    """The tab radios on the page, in order, with whether each is the open one."""
    return [(m[1], bool(m[2])) for m in re.finditer(r'<input type="radio"[^>]*data-tab="(\w+)"( checked)?>', body)]


def _names(body) -> list[str]:
    return [name for name, _ in _tabs(body)]


def _open(body) -> str:
    return next(name for name, checked in _tabs(body) if checked)


def _row_target(body) -> str:
    """The tab a click on the message's inbox row opens, or "" when the row is not a link."""
    found = re.search(r'<label class="mp-row" for="[^"]*-(\w+)">', body)
    return found[1] if found else ""


def test_a_fragment_is_safe_markup_not_a_document():
    fragment = _render(_message())
    assert isinstance(fragment, SafeString)
    assert fragment.startswith('<div class="mjml-preview"') and "<html" not in fragment and "<body" not in fragment


def test_the_message_is_read_from_itself_and_escaped():
    message = _message("Subj <x>", "plain & text", "<html><head></head><body><p>Hi</p></body></html>",
                       from_email='"Acme" <hi@acme.test>', to=["a@b.test"], bcc=["z@b.test"])
    body = _render(message)
    assert "Subj &lt;x&gt;" in body and "plain &amp; text" in body
    assert "&lt;p&gt;Hi&lt;/p&gt;" in body  # the HTML part sits escaped in srcdoc
    assert '<b class="mp-who">Acme</b>' in body and "a@b.test" in body and "z@b.test" in body


def test_an_html_only_message_has_no_text_tab():
    message = EmailMessage("S", "<p>only html</p>", "a@b.test", ["c@d.test"])
    message.content_subtype = "html"
    body = _render(message)
    assert "text" not in _names(body) and "&lt;p&gt;only html&lt;/p&gt;" in body and "<pre>" not in body


def test_a_text_only_message_without_the_inbox_is_one_tab_and_the_row_is_hidden():
    body = _render(_message(text="just text", html=""), inbox=False)
    assert "<pre>just text</pre>" in body and _tabs(body) == [("text", True)]
    assert 'class="mp-tabs mp-single"' in body


def test_tabs_are_inbox_html_text_with_the_first_open_by_default():
    assert _tabs(_render(_message())) == [("inbox", True), ("html", False), ("text", False)]
    assert _open(_render(_message(), inbox=False)) == "html"


def test_tab_chooses_the_open_one_without_reordering_and_falls_back():
    assert _tabs(_render(_message(), tab="text")) == [("inbox", False), ("html", False), ("text", True)]
    assert _open(_render(_message(text="t", html=""), tab="html")) == "text"  # content before the mock
    assert _open(_render(_message(text="t", html=""))) == "inbox"  # no tab asked: the first


def test_attachments_show_name_type_and_size_and_link_only_when_given_a_url():
    message = _message()
    message.attach("inv.pdf", b"x" * 2048, "application/pdf")
    message.attach("notes.txt", "hello", "text/plain")
    body = _render(message, attachment_urls={"inv.pdf": "/inv.pdf", "notes.txt": "javascript:alert(1)"})
    assert '<a href="/inv.pdf" target="_blank" rel="noopener" title="application/pdf">inv.pdf · 2.0\xa0KB</a>' in body
    assert "<span" in body and "notes.txt" in body and "javascript:" not in body


def test_the_inbox_has_placeholder_neighbours_by_default_after_the_message():
    body = _render(_message())
    assert body.index("Mine") < body.index("Harbour Hardware") and "Sunday lunch?" in body


def test_your_own_inbox_rows_replace_the_placeholders():
    body = _render(_message(), inbox=[("Zed", "Lunch?", "Sunday", "Sep 27")])
    assert body.index("Mine") < body.index("Lunch?") and "Sep 27" in body and "Harbour Hardware" not in body


def test_a_falsey_inbox_turns_the_tab_off():
    for off in (False, None, ()):
        body = _render(_message(), inbox=off)
        assert "inbox" not in _names(body) and "mp-p-inbox" not in body.split("</style>")[-1]


def test_the_placeholder_rows_are_blurred_but_your_own_are_not():
    rows = [("Mum", "Lunch?", "Sunday", "Sep 27")]
    assert "mp-p-inbox mp-blur" in _render(_message())
    assert "mp-p-inbox mp-blur" not in _render(_message(), inbox=rows)


def test_the_message_row_opens_the_html_view_or_the_text_without_html():
    assert _row_target(_render(_message())) == "html"
    assert _row_target(_render(_message(text="just text", html=""))) == "text"


LINKED = dict(
    text="See https://x.test/a?b=1&c=2 now",
    html='<html><head></head><body><a href="https://x.test/go">Go</a></body></html>',
)


def _pre(body) -> str:
    return body.split("<pre>", 1)[1].split("</pre>")[0]


def test_links_are_off_by_default_but_still_show_where_they_point():
    body = _render(_message(**LINKED))
    assert "href=&quot;#&quot; title=&quot;https://x.test/go&quot;" in body
    assert 'href="https://x.test/go"' not in body and "&lt;base" not in body
    assert 'sandbox=""' in body and "<a " not in _pre(body)


def test_links_on_makes_them_live_in_a_new_tab_in_both_parts():
    body = _render(_message(**LINKED), links=True)
    assert "href=&quot;https://x.test/go&quot;" in body and "&lt;base target=&quot;_blank&quot;&gt;" in body
    assert 'href="https://x.test/a?b=1&amp;c=2"' in _pre(body) and 'target="_blank" rel="noopener"' in _pre(body)
    assert 'sandbox="allow-popups allow-popups-to-escape-sandbox"' in body


def test_a_script_in_the_text_stays_inert_with_links_on():
    assert "<script>" not in _pre(_render(_message(text="<script>alert(1)</script> http://a.test"), links=True))


def test_tabs_limits_which_are_offered_in_the_fixed_order():
    body = _render(_message(), tabs=("text", "html"), tab="text")
    assert _tabs(body) == [("html", False), ("text", True)]


def test_empty_tabs_shows_just_the_open_view_with_no_tab_row():
    body = _render(_message(), tabs=(), tab="text")
    assert _tabs(body) == [("text", True)] and 'class="mp-tabs mp-single"' in body


def test_tabs_that_leave_nothing_fall_back_to_the_text_not_the_inbox():
    text_only = dict(text="just text", html="")
    assert _open(_render(_message(**text_only), tabs=("html",))) == "text"
    assert _open(_render(_message(**text_only), tabs=(), tab="html")) == "text"


def test_html_asked_for_on_a_text_only_message_gives_its_text():
    body = _render(_message(text="just text", html=""), tabs=("inbox", "html"))
    assert _names(body) == ["inbox", "text"] and _row_target(body) == "text"


def test_the_message_row_is_not_a_link_to_a_tab_that_is_not_there():
    body = _render(_message(), tabs=("inbox",))
    assert _names(body) == ["inbox"] and _row_target(body) == "" and '<div class="mp-row">' in body


def test_a_message_with_no_body_at_all_is_an_error():
    with pytest.raises(ValueError, match="neither an HTML nor a text body"):
        _render(_message(text="", html=""))


def test_everything_is_scoped_and_the_public_properties_have_fallbacks():
    body = _render(_message())
    styles = body.split("<style>", 1)[1].split("</style>")[0]
    selectors = [ln.strip() for ln in styles.splitlines() if ln.strip().startswith((".", "@media")) and "{" in ln]
    unscoped = [ln for ln in selectors if not ln.startswith((".mjml-preview", "@media"))]
    assert not unscoped, unscoped
    assert "--_accent: var(--mjml-accent, #2563eb)" in styles  # a host's own value wins over the default


def test_css_is_added_after_the_fragments_own_styles():
    body = _render(_message(), css=":root { --mjml-accent: #c026d3; }")
    assert body.index("--_accent: var(--mjml-accent, #2563eb)") < body.index("--mjml-accent: #c026d3")


def test_two_previews_on_one_page_do_not_share_ids_or_radio_groups():
    one, two = _render(_message()), _render(_message())
    for attribute in ("id", "name"):
        found = [set(re.findall(rf'\b{attribute}="([^"]+)"', b)) for b in (one, two)]
        assert not found[0] & found[1], attribute


def test_the_envelope_is_closed_on_the_inbox_tab():
    assert "input[data-tab=inbox]:checked) .mp-envelope { grid-template-rows: 0fr; }" in _render(_message())


def test_the_inbox_row_carries_the_attachments():
    message = _message()
    message.attach("inv.pdf", b"x" * 100, "application/pdf")
    row = _render(message).split('class="mp-panel mp-p-inbox', 1)[1].split("mp-older", 1)[0]
    assert '<em title="application/pdf">inv.pdf · 100\xa0bytes</em>' in row


def test_the_page_wraps_the_fragment_and_has_no_heading_unless_one_is_given():
    page = preview_response(_message()).content.decode()
    assert page.startswith("<!doctype html>") and 'class="mjml-preview"' in page and "<h1>" not in page
    assert "<title>Preview: Mine</title>" in page
    assert "<h1>Staff preview</h1>" in preview_response(_message(), heading="Staff preview").content.decode()


def test_the_page_passes_the_options_through():
    page = preview_response(_message(), tab="text", inbox=False, css=":root { --x: 1; }").content.decode()
    assert _tabs(page) == [("html", False), ("text", True)] and "--x: 1" in page


def _templates(tmp_path, **extra):
    backend = {"BACKEND": "mjml_templates.django.DjangoTemplates", "DIRS": [str(tmp_path)], "APP_DIRS": True}
    return override_settings(TEMPLATES=[backend], **extra)


def _write(tmp_path, name, content):
    (tmp_path / "mjml_templates").mkdir(exist_ok=True)
    (tmp_path / "mjml_templates" / name).write_text(content)


def test_a_project_template_of_the_same_name_replaces_the_fragment(tmp_path):
    _write(tmp_path, "preview_fragment.html", "OURS {{ subject }}")
    with _templates(tmp_path):
        assert _render(_message()) == "OURS Mine"


def test_a_project_template_of_the_same_name_replaces_the_page(tmp_path):
    _write(tmp_path, "preview.html", "PAGE {{ fragment }}")
    with _templates(tmp_path):
        page = preview_response(_message()).content.decode()
    assert page.startswith('PAGE <div class="mjml-preview"')


def test_a_page_override_can_extend_the_packaged_page(tmp_path):
    _write(
        tmp_path, "preview.html",
        '{% extends "mjml_templates/preview.html" %}{% block head %}<style>/*mine*/</style>{% endblock %}',
    )
    with _templates(tmp_path):
        page = preview_response(_message()).content.decode()
    assert "/*mine*/" in page and "<title>Preview: Mine</title>" in page


def test_a_broken_override_is_an_error_not_a_silent_fallback(tmp_path):
    from django.template import TemplateDoesNotExist

    _write(tmp_path, "preview.html", '{% extends "mjml_templates/missing.html" %}')
    with _templates(tmp_path), pytest.raises(TemplateDoesNotExist):
        preview_response(_message())


def test_your_own_template_fills_the_fragments_blocks_with_extra_context(tmp_path):
    (tmp_path / "mine.html").write_text(
        '{% extends "mjml_templates/preview_fragment.html" %}'
        "{% block tab_aside %}<span>{{ note }} / {{ from_addr }}</span>{% endblock %}"
        "{% block inbox_others %}<i>OLDER</i>{% endblock %}"
        "{% block panel_text %}<pre>{{ message.subject }}</pre>{% endblock %}"
    )
    with _templates(tmp_path):
        out = preview_fragment(_message(), template="mine.html", context={"note": "Nothing is sent"})
    assert "<span>Nothing is sent / " in out and "<i>OLDER</i>" in out and "<pre>Mine</pre>" in out
    assert 'class="mp-row' in out and "mp-envelope" in out  # blocks left alone are the stock ones


def test_the_previews_own_variables_win_over_extra_context():
    assert 'mp-subject">Mine<' in preview_fragment(_message(), context={"subject": "Spoofed"})


def test_the_frame_has_no_scripts_and_never_the_same_origin():
    assert 'sandbox=""' in preview_fragment(_message())
    live = preview_fragment(_message(), links=True)
    assert 'sandbox="allow-popups allow-popups-to-escape-sandbox"' in live
    assert "allow-scripts" not in live and "allow-same-origin" not in live
