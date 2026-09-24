# Changelog

## Unreleased

- The plain-text fallback no longer prints MJML's layout as Markdown tables (rows of
  `|` and `---` around every paragraph): tables marked `role="presentation"` are
  unwrapped before `html2text` runs, so only a real table -- an `<mj-table>` -- prints
  as one.
- A button comes out as `Label: url` on a line of its own, rather than `[Label](url)`.
- No trailing spaces on the plain-text lines.

## 1.1.0 (2026-09-16)

- Relative URLs in rendered `.mjml` output are made absolute, so links and images work
  once the message has left. The base comes from the request, or from `MJML_BASE_URL` --
  a full URL, or just a scheme (default `https://`) to pair with the current
  `django.contrib.sites` Site. Without either, output is unchanged.
- `mjml_base` is available in the template context, and in the sibling `.txt` template,
  for URLs a template has to write out itself.

## 1.0.0 (2026-09-16)

Initial release.

- `mjml_templates.django.DjangoTemplates`: drop-in Django template backend that compiles
  `.mjml` templates (and `from_string` code starting with `<mjml`) to email HTML.
- `render_email()` and `render_email_parts()` on `.mjml` templates, with subject from
  `<mj-title>` and plain-text from a sibling `.txt` template or `html2text`.
