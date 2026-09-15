# django-mjml-templates

A drop-in replacement for Django's template engine that also understands `.mjml` files.

```sh
uv add django-mjml-templates   # or pip install
```

Swap the backend; everything else about `TEMPLATES` stays as it was. The engine is still
named `django` (Django takes the default name from the module segment of `BACKEND`), so
`engines["django"]` and `using="django"` keep working.

```python
TEMPLATES = [{
    "BACKEND": "mjml_templates.django.DjangoTemplates",   # was django.template.backends.django.DjangoTemplates
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [...]},
}]
```

Every other template renders exactly as before. A template whose name ends in `.mjml`
(or a `from_string` whose code starts with `<mjml`) is a Django template first —
`{% extends %}`, loops, `{% url %}`, autoescaping — and the MJML that produces is
compiled to email HTML on render.

```html
{# templates/email/welcome.mjml #}
<mjml>
  <mj-head><mj-title>Welcome, {{ user.first_name }}</mj-title></mj-head>
  <mj-body>
    <mj-section><mj-column>
      <mj-text>Hi {{ user.first_name }}, thanks for signing up.</mj-text>
      <mj-button href="{{ link }}">Get started</mj-button>
    </mj-column></mj-section>
  </mj-body>
</mjml>
```

```python
from django.template.loader import get_template

get_template("email/welcome.mjml").render_email({"user": user, "link": link}, to=[user.email]).send()
```

`render_email(context, request=None, *, subject="", **kwargs)` returns an unsent
`EmailMultiAlternatives` with the plain-text body and the HTML alternative attached, so
you can still `attach()` a file before sending. `kwargs` go to `EmailMultiAlternatives`:
`to`, `from_email`, `bcc`, `reply_to`, `headers`, and so on.

For the raw pieces, `render_email_parts(context, request=None, *, subject="")` returns
a `(subject, text, html)` named tuple. Both are on `.mjml` templates only:

- **subject** — as given, else the rendered `<mj-title>`, else `ValueError`.
- **text** — `email/welcome.txt` rendered with the same context if it exists, else
  the HTML run through `html2text`.
- **html** — the compiled email.

## Absolute URLs

A relative link is dead in an email — there is no page for the mail client to resolve it
against. Every `.mjml` render rewrites `href`, `src`, `background` and CSS `url()` values
against a base URL, so `{% url %}`, `{% static %}` and hand-written paths all come out
absolute. Anything already carrying a scheme (`https:`, `mailto:`, `tel:`, `cid:`,
`data:`), a protocol-relative `//host/...`, or a bare `#fragment` is left alone.

The base is worked out in this order:

1. **The request**, if you passed one — `render_email(context, request, ...)`.
2. **`MJML_BASE_URL`** as a full URL, e.g. `"https://example.com"`.
3. **`MJML_BASE_URL` as a scheme alone** (the default, `"https://"`) paired with
   `django.contrib.sites` — so with the sites app installed there is nothing to
   configure.

If none of those give a base — no request, no sites app, no full URL — URLs are left
relative and nothing is raised. Sending outside a request cycle, from a Celery task or a
management command, therefore wants either `django.contrib.sites` installed or
`MJML_BASE_URL` set to a full URL. A `MJML_BASE_URL` with no scheme at all
(`"example.com"`) is an `ImproperlyConfigured`.

The rewrite only reaches URLs in markup. For one a template writes out as text — and for
the sibling `.txt`, which has no markup to rewrite — use `mjml_base`:

```html
<mj-text>Trouble with the button? Paste {{ mjml_base }}{% url "signup" %}</mj-text>
```

```
{# email/welcome.txt #}
Sign up: {{ mjml_base }}{% url "signup" %}
```

A `mjml_base` you pass in the context yourself wins over the derived one.

MJML is compiled with [mjml-python](https://pypi.org/project/mjml-python/) (the Rust `mrml`
port), so there is no Node dependency. Plain-text fallback uses `html2text`.
