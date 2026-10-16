# Customise the preview

## Change the colours or font

Both are styled with CSS custom properties, so a brand colour or font is one block of `css=`
(for the fragment, you can also set them in your own stylesheet; your values win over the defaults):

```python
preview_response(message, css=":root { --mjml-accent: #c026d3; --mjml-font: Georgia, serif; }")
```

The properties are listed in the [preview reference](../reference/preview.md#custom-properties).

The inbox mock keeps its own light look in both colour schemes, since it imitates a mail client.

## Dark mode

`preview_response`'s page redefines the colour properties under `prefers-color-scheme: dark` (all
but the font, accent and radius), since the page owns its background. `preview_fragment` does not:
it uses whatever your page sets, so it never turns light-on-light inside a host that is not dark.
If you change one of those colours on the page, set a dark value too; the accent keeps its light
value unless you give it one:

```python
css = """
:root { --mjml-accent: #7c3aed; }
@media (prefers-color-scheme: dark) { :root { --mjml-accent: #a78bfa; } }
"""
```

## Use your own stylesheet

`preview_response` is its own HTML document, so your site's stylesheets are not loaded on it;
pass the rules as `css=`, or read them from a file: `css=Path("static/brand.css").read_text()`.
(`preview_fragment` lives in your page, so your stylesheets already apply.)

## Replace part of the markup

There are two templates, and each can be overridden by one of the same name in your own
templates directory:


| Template | Is | Blocks |
|---|---|---|
| `mjml_templates/preview_fragment.html` | The preview itself (what `preview_fragment` renders, and the page includes) | none |
| `mjml_templates/preview.html` | The page that `preview_response` wraps it in | `head` (after the built-in styles), `content` |

To change part of the preview rather than all of it, name your own template and extend the
fragment, filling only the blocks you want. `context=` adds variables for it (the preview's own
win over a clashing key), and `message`, `from_addr` and the rest of the fragment's variables
are there too:

```python
preview_fragment(message, template="billing/email_preview_fragment.html", context={"note": "Nothing is sent"})
```

```html
{% extends "mjml_templates/preview_fragment.html" %}
{% block tab_aside %}<span class="mp-aside">{{ note }}</span>{% endblock %}
```

The blocks are listed in the [preview reference](../reference/preview.md#blocks).

The blocks sit inside the panels, which keep their `mp-` classes, so the tab switching still
works however much you replace. Replacing `panel_html` is where you take responsibility for the
frame's `sandbox`: the stock one has scripts off, so a message cannot run code, which is also
what a mail client does. If you need scripts (a script of your own that talks to your page, say),
write the `<iframe sandbox="allow-scripts …">` yourself here, and never add `allow-same-origin`
alongside it.

The packaged templates are always there as a fallback, and the backend lets your own templates
`{% extends "mjml_templates/preview.html" %}` instead of copying it, with nothing to install or
add to `INSTALLED_APPS`.
