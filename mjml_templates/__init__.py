"""A drop-in Django template engine that also renders ``.mjml`` email templates."""

from mjml_templates.django import DjangoTemplates, EmailParts, MJMLTemplate

__all__ = ["DjangoTemplates", "EmailParts", "MJMLTemplate"]
