# Absolute URLs

A relative link is dead in an email: there is no page for the mail client to resolve it against.
So every `.mjml` render rewrites `href`, `src`, `background` and CSS `url()` against a base URL, and
`{% url %}`, `{% static %}` and hand-written paths all come out absolute.

Anything already carrying a scheme (`https:`, `mailto:`, `tel:`, `data:`), a protocol-relative
`//host/…`, or a bare `#fragment` is left alone.

## The base URL

It comes from the request if you pass one to `render_email()`, and otherwise from `MJML_BASE_URL`:

```python
MJML_BASE_URL = "https://example.com"   # a full URL, used as-is
MJML_BASE_URL = "https://"              # scheme only (the default): paired with the current Site
```

- The default means a project with `django.contrib.sites` installed needs no setting at all.
- With no request, no full URL and no sites app there is no base to work from, and URLs are
  **left relative** rather than raising. Sending from a Celery task or a management command wants
  one of the two.
- A `MJML_BASE_URL` with no scheme at all (`"example.com"`) is an `ImproperlyConfigured`.

## URLs written as text

The rewrite reaches only markup. Where a template writes a URL out as text (and in the `.txt`
sibling, where there is no markup at all), use `mjml_base`:

```
{# email/welcome.txt #}
Sign up: {{ mjml_base }}{% url "signup" %}
```

`mjml_base` is in the context of every `.mjml` render and its `.txt`. Pass your own `mjml_base` in
the context and it wins over the derived one.
