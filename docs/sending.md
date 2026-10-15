# Sending

```python
from django.template.loader import get_template

get_template("email/welcome.mjml").render_email({"user": user}, request, to=[user.email]).send()
```

## `render_email`

```python
render_email(context=None, request=None, *, subject="", **kwargs) -> EmailMultiAlternatives
```

Returns an **unsent** `EmailMultiAlternatives` with the text body set and the HTML attached as
an alternative, so you can still add to it before sending:

```python
message = template.render_email({"invoice": invoice}, to=[invoice.client.email])
message.attach(invoice.pdf_name, invoice.pdf_bytes, "application/pdf")
message.send()
```

`kwargs` go straight to `EmailMultiAlternatives`: `to`, `from_email`, `bcc`, `cc`, `reply_to`,
`headers`, `connection` and so on. Without `from_email`, Django's `DEFAULT_FROM_EMAIL` is used.

## `render_email_parts`

```python
render_email_parts(context=None, request=None, *, subject="") -> EmailParts
```

The three pieces without building a message: a named tuple of `subject`, `text` and `html`. Use
it when you build the message yourself, or hand the parts to another system.

```python
subject, text, html = template.render_email_parts({"user": user})
```

## Notes

- Both methods exist on `.mjml` templates only, not on every template the engine loads.
- `request` is optional. When given it is passed to the template (so context processors run) and
  its host is used to make links absolute; without it, `MJML_BASE_URL` is used. See
  [Absolute URLs](absolute-urls.md).
- Sending from a Celery task or a management command has no request, so set `MJML_BASE_URL`.
- The subject is `subject=` if given, else the rendered `<mj-title>`, else a `ValueError`.
