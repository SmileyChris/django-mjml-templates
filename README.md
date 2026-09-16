# django-mjml-templates

A drop-in replacement for Django's template engine that also understands `.mjml` files,
so an email template is an ordinary Django template that happens to compile to email HTML.

```sh
uv add django-mjml-templates   # or pip install
```

## Setup

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

Every other template renders exactly as before. Only a template whose name ends in
`.mjml` — or a `from_string` whose code starts with `<mjml` — is treated as email.

## Writing an email

An `.mjml` file is a Django template first: `{% extends %}`, loops, `{% url %}` and
autoescaping all run as usual, and the MJML that produces is compiled on render. See
[the MJML docs](https://documentation.mjml.io/) for the components themselves.

```html
{# templates/email/welcome.mjml #}
<mjml>
  <mj-head><mj-title>Welcome, {{ user.first_name }}</mj-title></mj-head>
  <mj-body>
    <mj-section><mj-column>
      <mj-text>Hi {{ user.first_name }}, thanks for signing up.</mj-text>
      <mj-button href="{% url 'start' %}">Get started</mj-button>
    </mj-column></mj-section>
  </mj-body>
</mjml>
```

`<mj-title>` doubles as the subject line. A sibling `email/welcome.txt`, if you write one,
becomes the plain-text body; without it the HTML is run through `html2text`.

## Sending

```python
from django.template.loader import get_template

get_template("email/welcome.mjml").render_email({"user": user}, request, to=[user.email]).send()
```

`render_email(context, request=None, *, subject="", **kwargs)` returns an *unsent*
`EmailMultiAlternatives` with both bodies attached, so you can still `attach()` a file
first. `kwargs` go straight to `EmailMultiAlternatives`: `to`, `from_email`, `bcc`,
`reply_to`, `headers`, and so on.

`render_email_parts(context, request=None, *, subject="")` gives the raw
`(subject, text, html)` named tuple instead. Both methods exist on `.mjml` templates only.
The subject is the one you pass, else the rendered `<mj-title>`, else a `ValueError`.

## Absolute URLs

A relative link is dead in an email — there is no page for the mail client to resolve it
against. So every `.mjml` render rewrites `href`, `src`, `background` and CSS `url()`
against a base URL, and `{% url %}`, `{% static %}` and hand-written paths all come out
absolute. Anything already carrying a scheme, a protocol-relative `//host/…` or a bare
`#fragment` is left alone.

The base comes from the request if you pass one, and otherwise from `MJML_BASE_URL`:

```python
MJML_BASE_URL = "https://example.com"   # a full URL, used as-is
MJML_BASE_URL = "https://"              # scheme only (the default) — paired with the current Site
```

The default means projects with `django.contrib.sites` installed need no setting at all.
With no request, no full URL and no sites app there is no base to work from, and URLs are
left relative rather than raising — so sending from a Celery task or a management command
wants one of the two. (A `MJML_BASE_URL` with no scheme at all is an `ImproperlyConfigured`.)

The rewrite only reaches URLs in markup. Where a template writes one out as text, and in
the `.txt` sibling where there is no markup at all, use `mjml_base`:

```
{# email/welcome.txt #}
Sign up: {{ mjml_base }}{% url "signup" %}
```

Pass your own `mjml_base` in the context and it wins over the derived one.

## How it works

MJML is compiled with [mjml-python](https://pypi.org/project/mjml-python/), the Rust
`mrml` port, so there is no Node dependency. The plain-text fallback uses
[html2text](https://pypi.org/project/html2text/).

MIT licensed.
