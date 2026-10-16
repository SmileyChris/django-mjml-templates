# API reference

## `render_email`

```python
template.render_email(context=None, request=None, *, subject="", **kwargs) -> EmailMultiAlternatives
```

Returns an **unsent** `EmailMultiAlternatives` with the text body set and the HTML attached as an
alternative, so you can still add to it before sending:

```python
message = template.render_email({"invoice": invoice}, to=[invoice.client.email])
message.attach(invoice.pdf_name, invoice.pdf_bytes, "application/pdf")
message.send()
```

`kwargs` go straight to `EmailMultiAlternatives`: `to`, `from_email`, `bcc`, `cc`, `reply_to`,
`headers`, `connection` and so on. Without `from_email`, Django's `DEFAULT_FROM_EMAIL` is used.

## `render_email_parts`

```python
template.render_email_parts(context=None, request=None, *, subject="") -> EmailParts
```

The three pieces without building a message: a named tuple of `subject`, `text` and `html`.

```python
subject, text, html = template.render_email_parts({"user": user})
```

## Notes on both

- They exist on `.mjml` templates only, not on every template the engine loads.
- `request` is optional. When given it is passed to the template (so context processors run) and
  its host is used to make links absolute.

## Which templates are email

A template whose name ends in `.mjml`, or one from `from_string()` whose code starts with
`<mjml`. Every other template renders exactly as it did.

## The subject

`subject=` if given, else the rendered `<mj-title>`, else a `ValueError`.

## The plain-text part

A sibling `.txt` with the same name as the `.mjml`, rendered with the same context plus
`mjml_base`; otherwise [generated from the HTML](plain-text.md).

## Absolute URLs

`href`, `src`, `background` and CSS `url()` are rewritten against a base URL. Anything already
carrying a scheme (`https:`, `mailto:`, `tel:`, `data:`), a protocol-relative `//host/…`, or a
bare `#fragment` is left alone.

The base URL comes from the request if you pass one, and otherwise from the setting:

| `MJML_BASE_URL` | Meaning |
|---|---|
| `"https://example.com"` | A full URL, used as-is |
| `"https://"` (the default) | Scheme only, paired with the current `Site` (`django.contrib.sites`) |
| `"example.com"` | `ImproperlyConfigured`: a scheme is required |

With no request, no full URL and no sites app, URLs are **left relative** rather than raising.

`mjml_base` is in the context of every `.mjml` render and its `.txt`. Pass your own `mjml_base`
in the context and it wins over the derived one.

## Other behaviour

- MJML comments (`<!-- … -->`) are stripped from the output.
- Styling lives in MJML (`<mj-attributes>`, `<mj-style>`), the same as any MJML project.
