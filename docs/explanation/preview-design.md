# How the preview is designed

The preview shows an email the way a person will meet it. A few choices follow from what it is
for, and from what it could go wrong.

## A function, not a view

There is no URL to include, no setting and no admin page. `preview_response(message)` is a
function your own view calls.

- **Who may look is your decision.** A preview of a real email can contain a person's name, an
  address and a one-time link. Only your project knows who is allowed to see which message, so it
  is your view that checks, with the decorator or mixin you already use.
- **It reads the message, not the template.** It takes the `EmailMultiAlternatives` you would
  `.send()`, so it works for any Django email, and what you see is what would be sent.
- **It shows, it doesn't send.** No resend button, no recipient picker: those are decisions about
  your data and your workflow.

## The email is untrusted

An email can contain anything, including content from users (an invoice line, a comment). It
should not be able to run in the page that previews it.

- **The HTML is never marked safe.** It is escaped into an `iframe`'s `srcdoc`.
- **The frame is sandboxed.** Scripts are off, and `allow-same-origin` is never added, which is
  what keeps the email away from your page's cookies and session. This also matches a mail client,
  which doesn't run an email's scripts either.
- **Links are dead by default.** A click does nothing and hovering shows where it points. A
  preview should not confirm an address or spend a one-time token. `links=True` is the opt-in, and
  it loosens the sandbox only as far as popups, not scripts.
- **`css=` is the one thing not escaped.** It is for your code to restyle the page, so it must
  never come from a message or from user input.

If you need scripts in the frame, you take that over yourself by replacing the `panel_html` block.
The package won't do it for you.

## Fragment first

`preview_response` is a page wrapped around `preview_fragment`, not the other way round. The
fragment is the real thing, scoped under one class so it can't restyle (or be restyled by) the
page it sits in, and `preview_response` just gives it a document of its own. That means:

- An admin screen or a template editor can embed the preview without an iframe of its own.
- Dark mode belongs to the page, not the fragment: a fragment follows its host's colours, so it
  never turns light-on-light inside a host that isn't dark.
- Restyling is a set of CSS custom properties, and a few template blocks for changing markup,
  rather than options for each thing someone might want to change.

## The inbox is a mock

The Inbox tab imitates a mail client's row: sender, subject, then the preview text and the
start of the body, run together. Its other rows are placeholders, blurred so the eye stays on
yours. It is a plausible inbox, not a screenshot of Gmail or Apple Mail, and the preview makes no
claim about how any one client will show the email.
