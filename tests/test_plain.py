"""The plain-text fallback: MJML's layout tables unwrapped, real tables kept, buttons as Label: url."""

from mjml import mjml2html

from mjml_templates.plain import to_text


def _text(body: str) -> str:
    return to_text(mjml2html(f"<mjml><mj-body><mj-section><mj-column>{body}</mj-column></mj-section></mj-body></mjml>"))


def test_layout_tables_leave_no_markdown_table_behind():
    text = _text("<mj-text>Kia ora Ann,</mj-text><mj-text>Your invoice is attached.</mj-text>")
    assert text == "Kia ora Ann,\n\nYour invoice is attached.\n"


def test_a_real_table_is_still_a_table():
    text = _text("<mj-table><tr><th>Item</th><th>Amount</th></tr><tr><td>Hosting</td><td>$50.00</td></tr></mj-table>")
    assert "Item| Amount\n---|---\nHosting| $50.00" in text


def test_a_button_is_its_label_and_url():
    text = _text('<mj-button href="https://x.test/i/1">View <b>your</b> invoice</mj-button>')
    assert text == "View your invoice: https://x.test/i/1\n"


def test_a_link_in_text_is_left_to_html2text():
    text = _text('<mj-text>see <a href="https://x.test/">here</a></mj-text>')
    assert text == "see [here](https://x.test/)\n"


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
