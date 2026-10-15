# django-mjml-templates

Write email templates as `.mjml` files with the Django template language. A drop-in
replacement for Django's template backend: no Node, no new template engine to learn.
MJML is compiled by [mjml-python](https://pypi.org/project/mjml-python/) and the plain-text
part comes from [html2text](https://pypi.org/project/html2text/).

## Setup

```sh
uv add django-mjml-templates   # or pip install
```

Swap the backend in `TEMPLATES`; everything else stays as it was:

```python
TEMPLATES = [{
    "BACKEND": "mjml_templates.django.DjangoTemplates",  # was django.template.backends.django.DjangoTemplates
    ...
}]
```

Only templates ending in `.mjml` are treated as email; every other template renders as before.

## Writing an email

An `.mjml` file is a Django template first (`{% extends %}`, `{% url %}` and autoescaping all
work), compiled to email HTML on render. See the [MJML docs](https://documentation.mjml.io/)
for components.

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

`<mj-title>` is the subject. Add a sibling `email/welcome.txt` for a hand-written plain-text
body; without one it's generated from the HTML.

## Sending

```python
from django.template.loader import get_template

get_template("email/welcome.mjml").render_email({"user": user}, request, to=[user.email]).send()
```

`render_email(context, request=None, *, subject="", **kwargs)` returns an unsent
`EmailMultiAlternatives` (so you can still `attach()`); `kwargs` go to it (`to`, `from_email`,
`bcc`, ...). `render_email_parts(...)` returns the raw `(subject, text, html)` instead.

## Absolute URLs

Relative links are dead in an email, so `href`, `src`, `background` and CSS `url()` are made
absolute against the request, or `MJML_BASE_URL`:

```python
MJML_BASE_URL = "https://example.com"
```

Projects with `django.contrib.sites` need no setting. With no request, setting or sites app,
URLs are left relative (so set it for Celery tasks and management commands). Where markup
doesn't reach, such as the `.txt` sibling, write `{{ mjml_base }}{% url "signup" %}`.

## Previewing

`mjml_templates.preview` can show a built email as a person meets it (an inbox row, the HTML
and the plain text), as a page or as markup to embed in your own. See
[the preview docs](https://github.com/SmileyChris/django-mjml-templates/blob/main/docs/preview.md).
