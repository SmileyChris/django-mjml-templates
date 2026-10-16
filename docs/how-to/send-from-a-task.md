# Send from a task or command

A Celery task or a management command has no request, so two things differ from a view: links
need a base URL, and you build the context yourself.

## Set the base URL

```python
# settings.py
MJML_BASE_URL = "https://example.com"
```

Without a request this setting (or `django.contrib.sites`) is the only way links become
absolute. See [Make links absolute](absolute-urls.md).

## A task

Pass ids to the task and load the objects inside it, as with any task:

```python
from celery import shared_task
from django.template.loader import get_template


@shared_task
def send_receipt(payment_id):
    payment = Payment.objects.select_related("customer").get(pk=payment_id)
    message = get_template("email/receipt.mjml").render_email(
        {"payment": payment}, to=[payment.customer.email]
    )
    message.send()
```

Rendering is in-process, so there is no server or `mjml` binary to have running on the worker.

## Attach a file

`render_email()` returns an unsent message, so attach before sending:

```python
message.attach(f"receipt-{payment.pk}.pdf", pdf_bytes, "application/pdf")
```

## One email per recipient

Render once per person so each gets their own context. Share one connection to avoid reopening it
for every message:

```python
from django.core.mail import get_connection

template = get_template("email/newsletter.mjml")
with get_connection() as connection:
    messages = [
        template.render_email({"member": member}, to=[member.email], connection=connection)
        for member in members
    ]
    connection.send_messages(messages)
```

For a list that is large, send in batches (or one task per recipient) rather than building every
message up front.
