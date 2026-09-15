"""Relative URLs are no use in an email: nothing resolves them once the message leaves.

``base_url`` works out the scheme and host to resolve against -- from the request if
there is one, else from ``MJML_BASE_URL``, which is either a full URL or just a scheme
to pair with the current ``django.contrib.sites`` Site. ``absolutise`` rewrites the
rendered HTML against it, and does nothing at all without one.
"""

import re
from urllib.parse import urljoin, urlsplit

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

_ATTR = re.compile(r'\b(href|src|background)="([^"]*)"')
_CSS_URL = re.compile(r"""url\(\s*(['"]?)([^'")]*)\1\s*\)""")
# A scheme, a protocol-relative host, a bare fragment or nothing at all: already as
# absolute as it is going to get, or not a location to resolve.
_SKIP = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|#|$)", re.I)

DEFAULT_SCHEME = "https://"


def absolutise(html: str, base: str) -> str:
    if not base:
        return html
    root = base.rstrip("/") + "/"

    def attr(match: re.Match) -> str:
        name, url = match.groups()
        return match.group(0) if _SKIP.match(url) else f'{name}="{urljoin(root, url)}"'

    def css(match: re.Match) -> str:
        quote, url = match.groups()
        return match.group(0) if _SKIP.match(url) else f"url({quote}{urljoin(root, url)}{quote})"

    return _CSS_URL.sub(css, _ATTR.sub(attr, html))


def base_url(request=None) -> str:
    if request is not None:
        return request.build_absolute_uri("/").rstrip("/")
    setting = getattr(settings, "MJML_BASE_URL", DEFAULT_SCHEME)
    parts = urlsplit(setting)
    if parts.netloc and parts.scheme:
        return f"{parts.scheme}://{parts.netloc}"
    scheme = parts.scheme or parts.path.rstrip(":")
    if not scheme or "." in scheme or "/" in scheme:
        raise ImproperlyConfigured(
            f"MJML_BASE_URL is {setting!r}: give a full URL ('https://example.com') or "
            "just a scheme ('https://') to pair with the current Site."
        )
    if not apps.is_installed("django.contrib.sites"):
        return ""
    from django.contrib.sites.models import Site

    try:
        return f"{scheme}://{Site.objects.get_current().domain}"
    except (ImproperlyConfigured, Site.DoesNotExist):
        return ""
