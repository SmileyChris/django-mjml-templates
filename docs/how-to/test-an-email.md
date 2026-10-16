# Test an email

Rendering needs nothing beyond Python packages, so an email test is an ordinary Django test.
Django's test runner swaps in an in-memory email backend, and sent messages collect in
`mail.outbox`.

## Test what was sent

```python
from django.core import mail
from django.test import TestCase


class ReceiptTests(TestCase):
    def test_receipt_is_sent(self):
        payment = make_payment()

        send_receipt(payment.pk)

        [message] = mail.outbox
        assert message.to == [payment.customer.email]
        assert message.subject == f"Receipt {payment.number}"
        assert payment.number in message.body           # the plain-text part
        html, mimetype = message.alternatives[0]        # the HTML part
        assert "https://example.com/pay/" in html
```

With pytest-django the same works through its `mailoutbox` fixture.

## Test a template on its own

`render_email_parts()` gives you the subject, text and HTML without building a message:

```python
from django.template.loader import get_template


def test_welcome_parts():
    subject, text, html = get_template("email/welcome.mjml").render_email_parts({"user": user})

    assert subject == "Welcome, Ann"
    assert "Get started: https://example.com/start/" in text
```

## Things to know

- **Set `MJML_BASE_URL` in your test settings** (or pass a request), so links are absolute and you
  can assert on them. Without either they stay relative.
- **A missing subject fails.** A template with no `<mj-title>` and no `subject=` raises a
  `ValueError`, which makes a forgotten subject a test failure.
- **Look at it, too.** A passing assertion says the words are there, not that the email looks
  right. Open it with [a preview](preview-an-email.md) while you build it.
