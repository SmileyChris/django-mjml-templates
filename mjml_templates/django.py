"""A drop-in replacement for Django's template engine that also understands ``.mjml``.

Every template renders exactly as it would under ``DjangoTemplates``. One whose name
ends in ``.mjml`` (or, from a string, whose code starts with ``<mjml``) is a Django
template first -- ``{% extends %}``, loops, ``{% url %}`` and autoescaping all run as
usual -- and the MJML that produces is compiled to email HTML on render.

``render_email_parts`` hands back the three pieces of a message: subject, plain text
and HTML. The subject comes from ``<mj-title>`` unless given; the text comes from a
``.txt`` template of the same name, or from the HTML when there isn't one.
``render_email`` builds an unsent ``EmailMultiAlternatives`` from them.
"""

import html
import re
from typing import NamedTuple

import html2text
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.backends import django as django_backend
from django.template.backends.django import Template, reraise
from django.template.loader import get_template
from mjml import mjml2html


class EmailParts(NamedTuple):
    subject: str
    text: str
    html: str


class MJMLTemplate(Template):
    def render(self, context=None, request=None) -> str:
        return mjml2html(super().render(context, request), disable_comments=True)

    def render_email_parts(self, context=None, request=None, *, subject: str = "") -> EmailParts:
        context = context or {}
        rendered = self.render(context, request)
        name = self.template.name or "<string>"
        if not subject:
            match = re.search(r"<title>(.*?)</title>", rendered, re.S)
            subject = html.unescape(match.group(1)).strip() if match else ""
        if not subject:
            raise ValueError(f"{name}: no subject given and no <mj-title> in the template")
        return EmailParts(subject, self._text(name, context, request, rendered), rendered)

    def render_email(self, context=None, request=None, *, subject: str = "", **kwargs) -> EmailMultiAlternatives:
        """The message, unsent, so a caller can still attach to it. ``kwargs`` go to
        ``EmailMultiAlternatives``: ``to``, ``from_email``, ``bcc``, ``reply_to``, ``headers``..."""
        parts = self.render_email_parts(context, request, subject=subject)
        msg = EmailMultiAlternatives(parts.subject, parts.text, **kwargs)
        msg.attach_alternative(parts.html, "text/html")
        return msg

    @staticmethod
    def _text(name: str, context, request, rendered: str) -> str:
        if name.endswith(".mjml"):
            try:
                return get_template(name[: -len(".mjml")] + ".txt").render(context, request)
            except TemplateDoesNotExist:
                pass
        converter = html2text.HTML2Text()
        converter.body_width = 0
        converter.ignore_images = True
        return converter.handle(rendered)


class DjangoTemplates(django_backend.DjangoTemplates):
    """Django's engine, with ``.mjml`` support.

    Same class and module name as Django's on purpose: it is a drop-in, and Django takes
    an engine's default ``NAME`` from the module segment of ``BACKEND``, so this one is
    still called "django" without anyone having to say so.
    """

    def from_string(self, template_code):
        cls = MJMLTemplate if template_code.lstrip().startswith("<mjml") else Template
        return cls(self.engine.from_string(template_code), self)

    def get_template(self, template_name):
        cls = MJMLTemplate if template_name.endswith(".mjml") else Template
        try:
            return cls(self.engine.get_template(template_name), self)
        except TemplateDoesNotExist as exc:
            reraise(exc, self)
