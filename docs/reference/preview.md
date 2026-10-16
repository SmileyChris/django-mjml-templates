# Preview reference

```python
from mjml_templates.preview import preview_fragment, preview_response
```

## Arguments

```python
preview_response(message, *, heading="", **options)

preview_fragment(
    message, *, attachment_urls=None, inbox=True,
    tab=None, tabs=None, links=False, css="",
    template="mjml_templates/preview_fragment.html", context=None,
)
```

`preview_response` takes `heading` and passes every other option to `preview_fragment`, so the
table below covers both.

| Argument | Default | Meaning |
|---|---|---|
| `message` | required | The email. A `ValueError` if it has neither an HTML nor a text body. |
| `heading` | `""` | A page heading (`preview_response` only). There is none unless you give one. |
| `attachment_urls` | `None` | `{filename: url}` to link an attachment's chip. |
| `inbox` | `True` | `True` for placeholder rows, a list of your own, or falsey for no Inbox tab. |
| `tab` | `None` | The tab that is open. `None` is the first. |
| `tabs` | `None` | Which tabs to offer. `None` is all of them. |
| `links` | `False` | Make links live. See [Links](../how-to/preview-an-email.md#make-the-links-live). |
| `css` | `""` | Extra CSS, after the page's own. See [Restyling](../how-to/customise-preview.md). |
| `template` | the packaged one | Your own template that extends the fragment. See [Your own stylesheet or markup](../how-to/customise-preview.md#replace-part-of-the-markup). |
| `context` | `None` | Extra variables for that template. |

## Tabs

`tab` chooses the open one (`"inbox"`, `"html"` or `"text"`). If the message has no such tab it
falls back to the message's own content (HTML, then Text) before the Inbox mock.

`tabs` limits which are offered, and never changes their order. An `"html"` the message lacks
becomes its `"text"`, so `tabs=("inbox", "html")` still gives a plain-text email a way in:

```python
preview_response(message, tabs=("html", "text"))   # no Inbox
preview_response(message, tabs=("inbox",))         # only the Inbox: its row goes nowhere
preview_response(message, tabs=())                 # no tab row: just the open view
```

With one tab left the tab row is not shown. Clicking your message's row in the Inbox switches to
the HTML view (or Text, when there is no HTML), if that tab is on the page.

## The inbox

`inbox=True` fills the tab with a few generic rows, dated back from now so they never look stale.
Pass your own as `(sender, subject, snippet, when)` tuples:

```python
preview_response(message, inbox=[("Mum", "Sunday lunch?", "Are you free this weekend?", "Oct 12")])
```

Your message is always the first row. Anything falsey (`False`, `None`, `()`) turns the Inbox tab
off. The generated placeholder rows are blurred and can't be selected, so the eye stays on your
message; rows you pass yourself are shown plainly.

## Custom properties

Set on any ancestor, or through `css=`.

| Property | Default (light) | What it sets |
|---|---|---|
| `--mjml-font` | `system-ui, sans-serif` | The page's font |
| `--mjml-bg` | `#f3f4f6` | Page background |
| `--mjml-text` | `#1f2933` | Body text, the open tab, and links in the text part |
| `--mjml-muted` | `#6b7280` | Labels and inactive tabs |
| `--mjml-card` | `#fff` | The card |
| `--mjml-border` | `#d9dce1` | Borders |
| `--mjml-accent` | `#2563eb` | The open tab's underline and focus ring |
| `--mjml-radius` | `.5rem` | The card's corners |

## Blocks

Blocks of `mjml_templates/preview_fragment.html`, for an extending template.

| Block | Holds |
|---|---|
| `style` | Extra `<style>`, after the built-in rules and before `css=` |
| `envelope` | Subject, From, To, Bcc and attachment chips (empty it to drop them) |
| `tab_label` | One tab's label text (`tab` is `inbox`, `html` or `text`), e.g. `{% if tab == "text" %}Plain text{% else %}{{ block.super }}{% endif %}` |
| `tab_aside` | At the end of the tab bar (`.mp-bar`, with the labels); `mp-aside` pushes it to the right |
| `panel_html` | The HTML part's frame |
| `panel_text` | The text part |
| `inbox_row` | Your message's row in the Inbox |
| `inbox_others` | The other rows: the placeholders, or your own `inbox=` list |

## Safety

- The email's HTML is never marked safe. It is escaped into the frame's `srcdoc`, and the frame
  has `sandbox` with scripts off, and never `allow-same-origin`.
- The text part is escaped; with `links=True` it is escaped first and then linkified.
- `css=` is written into the page unescaped, on purpose. It must come from your code, never from a
  message or from user input.
- The page does not check who is looking. Put the view behind your own permission check, and
  remember that with `links=True` a click is a real request: one-time links in the email work.

## Not included

- No URL, view or admin page. The preview is a function you call.
- No sending or resending, and no recipient picking: it shows a message you've already built.
- No fidelity claim about any one mail client. The Inbox tab is a plausible inbox row, not
  a Gmail or Apple Mail screenshot.
