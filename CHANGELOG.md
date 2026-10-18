# Changelog

## 1.3.1 (2026-10-19)

- The backend adds the packaged templates as a last template directory, so a project's own
  preview template can `{% extends "mjml_templates/preview_fragment.html" %}` without
  `mjml_templates` in `INSTALLED_APPS`.
- Docs: a documentation site (https://smileychris.github.io/django-mjml-templates/) and a
  shorter README.

## 1.3.0 (2026-10-16)

- Plain-text fallback: `**bold**` and `*italic*` come out as plain words, and a real
  table's columns are padded so the pipes line up.
- Plain-text fallback: HTML entities keep their characters (`é © — Māori …`) rather than
  an ASCII approximation (`cafe (C) 2026 -- Maori ...`).
- Plain-text fallback: an inline link is written `label (url)`; a link whose label is
  its address (a URL, `mailto:` or `tel:`) is just the address, and a `#` or missing
  `href` is just the label.
- Fix: the plain-text fallback no longer backslash-escapes a line that begins like a
  Markdown list item, so a paragraph starting `1. First` or `- Dash` is no longer
  written `1\. First` or `\- Dash`.
- Plain-text fallback: headings are underlined rather than prefixed with `#`: the two
  shallowest levels an email uses get `=` then `-` (so an email that starts at `<h2>` still
  has a hierarchy), and any deeper heading is a plain line.
- `mjml_templates.preview`: `preview_fragment(message, ...)` and `preview_response(message, ...)`
  show a built email the way a person meets it -- an inbox row, the HTML part and the
  plain-text part -- read from the Django message itself. The fragment is scoped markup to
  embed in a page of your own, with blocks to extend and `--mjml-*` custom properties; the
  response wraps it in a page. Links are dead and scripts are off. Nothing is wired up and
  nothing is imported unless you use it: see `docs/preview.md`.

## 1.2.0 (2026-09-24)

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
