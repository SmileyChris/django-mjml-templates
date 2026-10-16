# django-mjml-templates

Write email as `.mjml` templates with the Django template language, and send it from a normal
view. A drop-in replacement for Django's template backend: no Node, no new template engine to
learn. MJML is compiled by [mjml-python](https://pypi.org/project/mjml-python/) and the
plain-text part comes from [html2text](https://pypi.org/project/html2text/).

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

## Write an email

A Django template first (`{% extends %}`, `{% url %}`, autoescaping), then
[MJML](https://documentation.mjml.io/) for the layout. `<mj-title>` is the subject.

```html
{# templates/email/welcome.mjml #}
<mjml>
  <mj-head>
    <mj-title>Welcome to Paperplane, {{ user.first_name }}</mj-title>
    <mj-preview>Your account is ready.</mj-preview>
    <mj-attributes>
      <mj-all font-family="Helvetica, Arial, sans-serif" />
      <mj-text font-size="16px" line-height="1.6" color="#374151" />
      <mj-button background-color="#4f46e5" border-radius="8px" font-size="16px" font-weight="600" />
    </mj-attributes>
  </mj-head>
  <mj-body background-color="#f3f4f6">
    <mj-section background-color="#4f46e5" padding="28px 0">
      <mj-column>
        <mj-text align="center" color="#ffffff" font-size="22px" font-weight="700">Paperplane</mj-text>
      </mj-column>
    </mj-section>
    <mj-section background-color="#ffffff" padding="32px 24px">
      <mj-column>
        <mj-text font-size="24px" font-weight="700" color="#111827">Welcome, {{ user.first_name }}!</mj-text>
        <mj-text>Your account is ready. Pick a template, add your team and send your first
          message in under a minute.</mj-text>
        <mj-button href="{% url 'start' %}" padding-top="12px">Get started</mj-button>
      </mj-column>
    </mj-section>
    <mj-section padding="16px 0 32px">
      <mj-column>
        <mj-text align="center" font-size="13px" color="#9ca3af">You are receiving this because you signed up at Paperplane.</mj-text>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>
```

## Send it

```python
from django.template.loader import get_template

message = get_template("email/welcome.mjml").render_email({"user": user}, request, to=[user.email])
message.send()
```

`render_email` returns an unsent `EmailMultiAlternatives`: the subject from `<mj-title>`, the HTML
from the MJML, and a plain-text part made for you. Attach files, set `reply_to`, or send it from a
Celery task like any other Django message. Links are made absolute from the request, or from
`MJML_BASE_URL` when there isn't one.

And the reader gets:

![The welcome email: an indigo header, a greeting, a button and a footer](https://smileychris.github.io/django-mjml-templates/images/welcome-email.png)

## Documentation

- [Get started](https://smileychris.github.io/django-mjml-templates/): the template, the view and a preview view
- How-to: [a simple design](https://smileychris.github.io/django-mjml-templates/how-to/build-a-design/), [sending from a task](https://smileychris.github.io/django-mjml-templates/how-to/send-from-a-task/), [testing](https://smileychris.github.io/django-mjml-templates/how-to/test-an-email/), [a shared layout](https://smileychris.github.io/django-mjml-templates/how-to/write-a-layout/), [absolute links](https://smileychris.github.io/django-mjml-templates/how-to/absolute-urls/), [previewing](https://smileychris.github.io/django-mjml-templates/how-to/preview-an-email/), [customising the preview](https://smileychris.github.io/django-mjml-templates/how-to/customise-preview/)
- Reference: [API](https://smileychris.github.io/django-mjml-templates/reference/api/), [plain-text fallback](https://smileychris.github.io/django-mjml-templates/reference/plain-text/), [preview](https://smileychris.github.io/django-mjml-templates/reference/preview/)
- Explanation: [why this](https://smileychris.github.io/django-mjml-templates/explanation/why/), [how a render works](https://smileychris.github.io/django-mjml-templates/explanation/how-a-render-works/), [how the preview is designed](https://smileychris.github.io/django-mjml-templates/explanation/preview-design/)
