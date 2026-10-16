# Make links absolute

Relative links are dead in an email. With a request they are made absolute for you; without one
(a Celery task, a management command) you have to say where the site lives.

## From a task or command

Set the site's URL:

```python
# settings.py
MJML_BASE_URL = "https://example.com"
```

A project with `django.contrib.sites` needs no setting; the current `Site` is used.

## URLs written as text

The rewrite reaches only markup. Where a template writes a URL out as text, and in the `.txt`
sibling, where there is no markup at all, use `mjml_base`:

```
{# email/welcome.txt #}
Sign up: {{ mjml_base }}{% url "signup" %}
```

The rules for what is rewritten and what is left alone are in the
[API reference](../reference/api.md#absolute-urls).
