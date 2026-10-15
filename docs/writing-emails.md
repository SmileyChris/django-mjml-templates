# Writing an email

An `.mjml` file is a Django template first. `{% extends %}`, `{% include %}`, loops,
`{% url %}`, `{% static %}` and autoescaping all run as usual, and the MJML that produces is
compiled to email HTML when the template renders. See [the MJML docs](https://documentation.mjml.io/)
for the components themselves.

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

Only a template whose name ends in `.mjml` is treated as email, or one from `from_string()` whose
code starts with `<mjml`. Every other template renders exactly as it did.

## A shared layout

Put the chrome (head, logo, footer) in a base template and fill blocks from each email:

```html
{# email/base.mjml #}
<mjml>
  <mj-head><mj-title>{% block title %}{% endblock %}</mj-title></mj-head>
  <mj-body>
    <mj-section><mj-column>{% block body %}{% endblock %}</mj-column></mj-section>
  </mj-body>
</mjml>
```

```html
{# email/receipt.mjml #}
{% extends "email/base.mjml" %}
{% block title %}Receipt {{ number }}{% endblock %}
{% block body %}<mj-text>Thanks for your payment.</mj-text>{% endblock %}
```

## The subject

`<mj-title>` is the subject line, rendered with your context. The `subject=` argument to
`render_email()` wins over it, and with neither you get a `ValueError` rather than a message
with no subject.

## The plain-text part

Put a `.txt` template next to the `.mjml` file with the same name (`email/welcome.txt`) to
write the text by hand. It renders with the same context, plus `mjml_base`
(see [Absolute URLs](absolute-urls.md)).

Without one, the text is [generated from the HTML](plain-text.md).

A `.txt` is still a Django template, so autoescaping applies: a name like `A&B` would come out
as `A&amp;B`. Wrap it in `{% autoescape off %}…{% endautoescape %}`.

## Good to know

- MJML comments (`<!-- … -->`) are stripped from the output.
- Styling lives in MJML (`<mj-attributes>`, `<mj-style>`), the same as any MJML project.
