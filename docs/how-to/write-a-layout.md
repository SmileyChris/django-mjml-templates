# Write a shared layout

Put the chrome (head, logo, footer) in a base template and fill blocks from each email. An
`.mjml` file is a Django template first, so `{% extends %}` and `{% include %}` work as usual:

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

`<mj-title>` is the subject, so the `title` block above sets it.

## Write the plain text by hand

Put a `.txt` template next to the `.mjml` file with the same name (`email/receipt.txt`). It
renders with the same context, plus `mjml_base` (see [Make links absolute](absolute-urls.md)).

A `.txt` is still a Django template, so autoescaping applies: a name like `A&B` would come out as
`A&amp;B`. Wrap it in `{% autoescape off %}…{% endautoescape %}`.

Without a `.txt`, the text is [generated from the HTML](../reference/plain-text.md).

## Override the subject

Pass `subject=` to `render_email()`; it wins over `<mj-title>`. See the
[API reference](../reference/api.md#the-subject).
