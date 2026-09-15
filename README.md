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

MJML is compiled with [mjml-python](https://pypi.org/project/mjml-python/) (the Rust `mrml`
port), so there is no Node dependency. Plain-text fallback uses `html2text`.
