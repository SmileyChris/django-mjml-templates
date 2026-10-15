"""The plain-text part, for a template with no ``.txt`` sibling: ``html2text`` of the HTML.

MJML lays everything out in tables, which ``html2text`` would print as Markdown tables --
rows of ``|`` and ``---`` around every paragraph. MJML marks its layout tables
``role="presentation"``, so those are unwrapped first and only a real table (an
``<mj-table>``) is left to print as one. A button, a link that is a whole layout cell,
becomes ``Label: url`` on a line of its own, rather than ``[Label](url)``.
"""

import html
import re
from html.parser import HTMLParser

import html2text

_ROWS = {"tr", "td", "th"}
_LAYOUT = _ROWS | {"table", "thead", "tbody", "tfoot"}

# html2text backslash-escapes a line that could read as a Markdown list item ("1\. ", "\- ",
# "\+ "). This is not Markdown, so the backslash is noise.
_LIST_ESCAPE = re.compile(r"^(\s*)(?:(\d+)\\(?=\.)|\\(?=[-+]))")


def to_text(rendered: str) -> str:
    converter = html2text.HTML2Text()
    converter.body_width = 0
    converter.ignore_images = True
    converter.unicode_snob = True  # &eacute; and &mdash; stay themselves, not "e" and "--"
    converter.ignore_emphasis = True  # no **bold** or _italic_: this is plain text, not Markdown
    converter.pad_tables = True  # a real table lines up its columns, for a text client
    text = converter.handle(_unwrap(rendered))
    # html2text ends lines with two spaces for a Markdown hard break: noise in plain text.
    return "\n".join(_LIST_ESCAPE.sub(r"\1\2", line.rstrip()) for line in text.splitlines()).strip("\n") + "\n"


def _link_text(label: str, url: str) -> str:
    """An inline link as plain text: ``label (url)``. Just the label when there is nowhere to go
    or the label already is the address (a URL, an email address, a phone number)."""
    if not label or not url or url.startswith("#"):
        return label
    bare = url.split(":", 1)[1].split("?", 1)[0] if url.startswith(("mailto:", "tel:")) else url
    if label in (url, bare) or label.rstrip("/") == bare.rstrip("/"):
        return label
    return f"{label} ({url})"


def _unwrap(rendered: str) -> str:
    parser = _Unwrap()
    parser.feed(rendered)
    parser.close()
    return "".join(parser.out)


class _Unwrap(HTMLParser):
    """Rewrites layout tables as ``<div>``s, leaving any other table whole. The open tables
    are a stack, so a cell's tags go or stay with the table they belong to."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.out = []
        self.tables = []  # per open table: True for a layout one
        self.cell_start = False  # a layout cell has just opened, nothing in it yet
        self.button = None  # a link's href while its label is read (a button's, or an inline one's)
        self.is_button = False
        self.label = []

    def _in_layout(self) -> bool:
        return bool(self.tables) and self.tables[-1]

    def handle_starttag(self, tag, attrs):
        at_cell_start, self.cell_start = self.cell_start, False
        if self.button is not None:
            return  # a tag inside a link's label: the words are enough
        if tag == "a":
            self.button, self.label = dict(attrs).get("href") or "", []
            self.is_button = at_cell_start  # a link that is a whole layout cell is a button
            return
        if tag == "table":
            self.tables.append(dict(attrs).get("role") == "presentation")
            if self.tables[-1]:
                return
        elif tag in _LAYOUT and self._in_layout():
            if tag in _ROWS:
                self.out.append("<div>")
                self.cell_start = tag != "tr"
            return
        self.out.append(self.get_starttag_text())

    def handle_startendtag(self, tag, attrs):
        self.cell_start = False
        if self.button is None:
            self.out.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        self.cell_start = False
        if self.button is not None:
            if tag == "a":
                label = " ".join("".join(self.label).split())
                if self.is_button:
                    self.out.append(f"<p>{html.escape(label)}: {html.escape(self.button)}</p>")
                else:
                    self.out.append(html.escape(_link_text(label, self.button)))
                self.button = None
            return
        if tag == "table" and self.tables:
            if self.tables.pop():
                return
        elif tag in _LAYOUT and self._in_layout():
            if tag in _ROWS:
                self.out.append("</div>")
            return
        self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if data.strip():
            self.cell_start = False
        (self.label if self.button is not None else self.out).append(data)

    def handle_entityref(self, name):
        self.handle_data(f"&{name};" if self.button is None else html.unescape(f"&{name};"))

    def handle_charref(self, name):
        self.handle_data(f"&#{name};" if self.button is None else html.unescape(f"&#{name};"))

    def handle_comment(self, data):
        self.out.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.out.append(f"<!{decl}>")
