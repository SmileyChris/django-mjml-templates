# The plain-text fallback

With no sibling `.txt`, the text part is made from the rendered HTML with
[html2text](https://pypi.org/project/html2text/), tuned so it reads as an email and not as
Markdown.

| In the HTML | In the text |
|---|---|
| MJML's layout tables | Unwrapped: paragraphs, no `\|` and `---` around everything |
| An `<mj-table>` | A real table, with its columns padded to line up |
| `<mj-button href="…">Label</mj-button>` | `Label: https://…`, on a line of its own |
| `<a href="https://x/">here</a>` | `here (https://x/)`; just the address if the label is the address |
| `<a href="#top">…</a>` or no `href` | Just the label |
| `<strong>`, `<em>` | The plain words, with no `**` or `*` |
| `<h1>`, `<h2>` and so on | The two shallowest levels used are underlined with `=` then `-`; deeper ones are plain lines |
| `&eacute; &copy; &mdash;` | `é © —`, not an ASCII approximation |
| `<img>` | Dropped |
| A paragraph starting `1. ` or `- ` | Kept as written, with no backslash |

Lines are not wrapped (the mail client does that) and there are no trailing spaces.

## When to write your own

The fallback is good for transactional mail. Write a `.txt` when you want something a person
would write by hand: a signature block, a short summary, different wording. See
[Writing an email](writing-emails.md#the-plain-text-part).
