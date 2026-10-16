# Build a simple design

MJML does the hard part of email layout (tables, Outlook quirks, responsive columns); this page
is about setting it up so every email shares one look. For the components themselves, see the
[MJML documentation](https://documentation.mjml.io/).

The idea: one base template holds the design, and each email fills in a block.

## The base

```html
{# email/base.mjml #}
<mjml>
  <mj-head>
    <mj-title>{% block title %}{% endblock %}</mj-title>
    <mj-preview>{% block preview %}{% endblock %}</mj-preview>
    <mj-attributes>
      <mj-all font-family="Helvetica, Arial, sans-serif" />
      <mj-text font-size="16px" line-height="1.5" color="#1f2933" />
      <mj-button background-color="#2563eb" border-radius="6px" font-size="16px" />
    </mj-attributes>
    <mj-style>
      a { color: #2563eb; }
    </mj-style>
  </mj-head>
  <mj-body background-color="#f3f4f6">
    <mj-section padding="24px 0 8px">
      <mj-column>
        <mj-text align="center" font-size="20px" font-weight="bold">Example</mj-text>
      </mj-column>
    </mj-section>
    <mj-section background-color="#ffffff" border-radius="8px" padding="16px 24px">
      <mj-column>{% block body %}{% endblock %}</mj-column>
    </mj-section>
    <mj-section>
      <mj-column>
        <mj-text align="center" font-size="13px" color="#6b7280">
          {% block footer %}You are receiving this because you have an account at Example.{% endblock %}
        </mj-text>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>
```

- **`<mj-attributes>`** sets defaults per component, so the emails themselves stay free of
  styling. Change a colour here and every email follows.
- **`<mj-preview>`** is the grey text an inbox shows after the subject.
- **`<mj-title>`** is the subject.
- **Comments** (`<!-- -->`) in the MJML are removed from the output; use `{# #}` for notes
  to yourself.

## An email

```html
{# email/welcome.mjml #}
{% extends "email/base.mjml" %}
{% block title %}Welcome, {{ user.first_name }}{% endblock %}
{% block preview %}Here is how to get started.{% endblock %}
{% block body %}
  <mj-text>Hi {{ user.first_name }}, thanks for signing up.</mj-text>
  <mj-button href="{% url 'start' %}">Get started</mj-button>
{% endblock %}
```

The button's `href` is rewritten to an absolute URL, so `{% url %}` works as it does in a page.
See [Make links absolute](absolute-urls.md) if you send from a task or command.

## Images

Email clients can't use your static files by path. Use a full URL, which `{% static %}` becomes
once it is made absolute:

```html
<mj-image src="{% static 'email/logo.png' %}" alt="Example" width="120px" />
```

Always give an `alt`: many clients block images until the reader allows them.

## Before you send

Open it with [a preview](preview-an-email.md) to check the layout, the inbox row and the text
version. Real mail clients differ, so send a test to a couple of them for anything that matters.
