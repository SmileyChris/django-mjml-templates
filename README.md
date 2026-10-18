# django-mjml-templates

**Email that's just another Django template.** [MJML](https://mjml.io/) is a markup that compiles
to responsive email HTML. Write it in `.mjml` files with `{% extends %}`, `{% url %}` and your own
tags and filters, and get back a message ready to send: the HTML, a plain-text part, a subject and
absolute links, with no Node or server needed. Swap a line in `TEMPLATES` and everything else
keeps rendering as normal.

## Setup

```sh
uv add django-mjml-templates   # or pip install
```

Swap the backend:

```python
TEMPLATES = [{
    "BACKEND": "mjml_templates.django.DjangoTemplates",  # was django.template.backends.django.DjangoTemplates
    ...
}]
```

Only templates ending in `.mjml` are treated as email; every other template renders as before.
MJML is compiled by [mjml-python](https://pypi.org/project/mjml-python/) (a prebuilt Rust port) and the
plain-text part comes from [html2text](https://pypi.org/project/html2text/).

## Write an email

A Django template first (`{% extends %}`, `{% url %}`, autoescaping), then
[MJML](https://documentation.mjml.io/) for the layout. `<mj-title>` is the subject.

```html
{# templates/email/welcome.mjml #}
<mjml>
  <mj-head><mj-title>Welcome to Paperplane, {{ user.first_name }}</mj-title></mj-head>
  <mj-body>
    <mj-section><mj-column>
      <mj-text>Hi {{ user.first_name }}, your account is ready.</mj-text>
      <mj-button href="{% url 'start' %}">Get started</mj-button>
    </mj-column></mj-section>
  </mj-body>
</mjml>
```

<details>
<summary>The styled version in the screenshot below</summary>

```html
<mjml>
  <mj-head>
    <mj-title>Welcome to Paperplane, {{ user.first_name }}</mj-title>
    <mj-attributes><mj-all font-family="Helvetica, Arial, sans-serif" /></mj-attributes>
  </mj-head>
  <mj-body background-color="#f3f4f6">
    <mj-section background-color="#4f46e5">
      <mj-column>
        <mj-text align="center" color="#ffffff" font-size="22px" font-weight="bold">Paperplane</mj-text>
      </mj-column>
    </mj-section>
    <mj-section background-color="#ffffff">
      <mj-column>
        <mj-text font-size="24px" font-weight="bold">Welcome, {{ user.first_name }}!</mj-text>
        <mj-text>Your account is ready. Pick a template and send your first message.</mj-text>
        <mj-button href="{% url 'start' %}" background-color="#4f46e5">Get started</mj-button>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>
```

</details>

## Send it

```python
from django.template.loader import get_template

template = get_template("email/welcome.mjml")
message = template.render_email(
    {"user": user},
    request,
    to=[user.email],
)
message.send()
```

`get_template` is Django's own loader, so it finds `.mjml` files the same way it finds any
template, and the one it hands back also has `render_email`. That returns an unsent
`EmailMultiAlternatives`: the subject from `<mj-title>`, the HTML from the MJML, and a plain-text
part made for you. Attach files, set `reply_to`, or send it from a Celery task like any other
Django message. Links are made absolute from the request, or from `MJML_BASE_URL` when there isn't
one.

With the styled template, the reader gets:

![The welcome email: an indigo header, a greeting, a button and a footer](https://smileychris.github.io/django-mjml-templates/images/welcome-email.png)

## Documentation

- [Get started](https://smileychris.github.io/django-mjml-templates/): the template, the view and a preview view
- How-to: [a simple design](https://smileychris.github.io/django-mjml-templates/how-to/build-a-design/), [sending from a task](https://smileychris.github.io/django-mjml-templates/how-to/send-from-a-task/), [testing](https://smileychris.github.io/django-mjml-templates/how-to/test-an-email/), [a shared layout](https://smileychris.github.io/django-mjml-templates/how-to/write-a-layout/), [absolute links](https://smileychris.github.io/django-mjml-templates/how-to/absolute-urls/), [previewing](https://smileychris.github.io/django-mjml-templates/how-to/preview-an-email/), [customising the preview](https://smileychris.github.io/django-mjml-templates/how-to/customise-preview/)
- Reference: [API](https://smileychris.github.io/django-mjml-templates/reference/api/), [plain-text fallback](https://smileychris.github.io/django-mjml-templates/reference/plain-text/), [preview](https://smileychris.github.io/django-mjml-templates/reference/preview/)
- Explanation: [why this](https://smileychris.github.io/django-mjml-templates/explanation/why/), [how a render works](https://smileychris.github.io/django-mjml-templates/explanation/how-a-render-works/), [how the preview is designed](https://smileychris.github.io/django-mjml-templates/explanation/preview-design/)
