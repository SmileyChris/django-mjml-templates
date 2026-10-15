"""The plain-text fallback: MJML's layout tables unwrapped, real tables kept, buttons as Label: url."""

import pytest
from mjml import mjml2html

from mjml_templates.plain import to_text


def _text(body: str) -> str:
    return to_text(mjml2html(f"<mjml><mj-body><mj-section><mj-column>{body}</mj-column></mj-section></mj-body></mjml>"))


def test_layout_tables_leave_no_markdown_table_behind():
    text = _text("<mj-text>Kia ora Ann,</mj-text><mj-text>Your invoice is attached.</mj-text>")
    assert text == "Kia ora Ann,\n\nYour invoice is attached.\n"


def test_a_real_table_is_still_a_table():
    text = _text("<mj-table><tr><th>Item</th><th>Amount</th></tr><tr><td>Hosting</td><td>$50.00</td></tr></mj-table>")
    assert text == "| Item    | Amount |\n|---------|--------|\n| Hosting | $50.00 |\n"


def test_a_tables_columns_line_up_whatever_the_cell_widths():
    text = _text(
        "<mj-table><tr><th>Item</th><th>Amount</th></tr>"
        "<tr><td>Extra seats x2</td><td>$30.00</td></tr><tr><td>Pro</td><td>$99.00</td></tr></mj-table>"
    )
    widths = {len(line) for line in text.splitlines()}
    assert len(widths) == 1, text  # every row is the same width, so the pipes align


def test_bold_and_italic_are_plain_words_not_markdown():
    text = _text("<mj-text>Receipt <strong>#10482</strong>, <em>paid</em> and <b>filed</b>.</mj-text>")
    assert text == "Receipt #10482, paid and filed.\n"


def test_a_button_is_its_label_and_url():
    text = _text('<mj-button href="https://x.test/i/1">View <b>your</b> invoice</mj-button>')
    assert text == "View your invoice: https://x.test/i/1\n"


def test_an_inline_link_is_its_label_and_url_in_parens():
    text = _text('<mj-text>see <a href="https://x.test/">here</a> for more</mj-text>')
    assert text == "see here (https://x.test/) for more\n"


def test_a_links_url_is_not_backslash_escaped():
    text = _text('<mj-text><a href="https://x.test/a_(b)">docs [v2]</a></mj-text>')
    assert text == "docs [v2] (https://x.test/a_(b))\n"


def test_a_link_whose_label_is_its_address_is_just_the_address():
    assert _text('<mj-text><a href="https://x.test/">https://x.test/</a></mj-text>') == "https://x.test/\n"
    assert _text('<mj-text><a href="mailto:hi@x.test">hi@x.test</a></mj-text>') == "hi@x.test\n"
    assert _text('<mj-text><a href="tel:+64211234567">+64211234567</a></mj-text>') == "+64211234567\n"


def test_a_mailto_link_with_another_label_keeps_the_address():
    text = _text('<mj-text><a href="mailto:hi@x.test">email us</a></mj-text>')
    assert text == "email us (mailto:hi@x.test)\n"


def test_a_link_with_no_label_or_no_destination_is_not_a_url_on_its_own():
    assert _text('<mj-text>a<a href="https://x.test/"> </a>b</mj-text>') == "ab\n"
    assert _text('<mj-text><a href="#top">back to top</a></mj-text>') == "back to top\n"
    assert _text("<mj-text><a>no href</a></mj-text>") == "no href\n"


def test_named_entities_keep_their_characters():
    text = _text("<mj-text>caf&eacute; &copy; 2026 &mdash; M&amacr;ori &hellip;</mj-text>")
    assert text == "café © 2026 — Māori …\n"


def test_no_trailing_spaces():
    text = _text("<mj-text>Ngā mihi,<br>Chris</mj-text>")
    assert text == "Ngā mihi,\nChris\n"


def test_escaped_characters_in_a_button_or_text_come_out_plain():
    # &#x27; is how Django's autoescaping writes an apostrophe.
    text = _text(
        "<mj-text>Terms &amp; conditions</mj-text>"
        '<mj-button href="https://x.test/t">Ann&#x27;s terms &amp; conditions</mj-button>'
    )
    assert text == "Terms & conditions\n\nAnn's terms & conditions: https://x.test/t\n"


@pytest.mark.parametrize(
    ("line", "expected"),
    [("1. First", "1. First"), ("12. Twelve", "12. Twelve"), ("- Dash", "- Dash"), ("+ Plus", "+ Plus")],
)
def test_a_line_that_looks_like_a_markdown_list_is_not_escaped(line, expected):
    assert to_text(f"<p>{line}</p>") == expected + "\n"


def test_headings_are_underlined_for_h1_and_h2_and_plain_below():
    text = to_text("<h1>Your <em>invoice</em></h1><h2>Payment</h2><h3>Notes</h3><p>Body</p>")
    assert text == "Your invoice\n============\n\nPayment\n-------\n\nNotes\n\nBody\n"
