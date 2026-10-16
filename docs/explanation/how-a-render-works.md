# How a render works

An `.mjml` template is rendered in four steps, in this order:

1. **Django renders the template.** `{% extends %}`, `{% include %}`, `{% if %}`, `{% for %}`,
   `{% url %}` and `{{ variables }}` all run, exactly as in any other template. What comes out is
   MJML.
2. **mjml-python compiles that MJML** to email HTML, in-process, with MJML comments dropped.
3. **Relative URLs are made absolute** in the HTML (`href`, `src`, `background`, CSS `url()`).
4. **The plain-text part is made**, from a sibling `.txt` if there is one, otherwise from the
   finished HTML.

The subject is read from the compiled HTML's `<title>`, which is where `<mj-title>` ends up.

## What the order means

**Template tags can wrap MJML.** Django has finished before MJML starts, so a tag can add or drop
whole components, and a loop can repeat a row:

```html
{% for line in invoice.lines %}
  <mj-table>...</mj-table>
{% endfor %}
```

MJML never sees `{% for %}`; it sees the MJML the loop produced.

**Autoescaping happens before compilation.** `{{ name }}` is escaped as HTML wherever it sits, in
text or in an attribute, so a name like `A&B` reaches MJML as `A&amp;B` and shows as `A&B`. Mark
a value `|safe` only when it really is markup (a rendered fragment of your own).

**The URL rewrite sees markup, not templates.** It runs on the compiled HTML, so `{% url %}`,
`{% static %}` and hand-written paths are all covered, wherever they came from. But a URL you
write out as text is not an attribute, and the rewrite can't find it. That's why `mjml_base`
exists, for text and for the `.txt` sibling.

**The generated text reads the final HTML.** It is produced after step 3, so the links in it are
already absolute. A hand-written `.txt` is a separate template that never sees the HTML, which is
why it gets `mjml_base` too.

## Why a template backend

The other way to do this is a tag, `{% mjml %}…{% endmjml %}`, around the MJML inside a template.
This package swaps the engine instead, for two reasons:

- **An email is a template.** `get_template("email/welcome.mjml")`, `{% extends %}` between
  emails, template loaders and your own tags and filters all work because it is an ordinary
  template. There is nothing to wrap.
- **Only `.mjml` changes.** The backend is Django's own, so every other template renders as it did.
  Adopting it is one line in `TEMPLATES`, and removing it is the same line.

Plain `template.render(context)` on an `.mjml` template returns the compiled HTML. The email
methods, `render_email()` and `render_email_parts()`, run the same four steps and add the subject
and the text.
