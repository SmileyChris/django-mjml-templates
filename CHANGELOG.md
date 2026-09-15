# Changelog

## 1.0.0 (2026-09-16)

Initial release.

- `mjml_templates.django.DjangoTemplates`: drop-in Django template backend that compiles
  `.mjml` templates (and `from_string` code starting with `<mjml`) to email HTML.
- `render_email()` and `render_email_parts()` on `.mjml` templates, with subject from
  `<mj-title>` and plain-text from a sibling `.txt` template or `html2text`.
