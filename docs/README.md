# django-mjml-templates

Write email as `.mjml` templates, render and send them from a normal Django view. No Node, no
new template engine: it's Django's template backend with `.mjml` files compiled to email HTML,
and a plain-text part made for you.

## Setup

```python
# settings.py
TEMPLATES = [{
    "BACKEND": "mjml_templates.django.DjangoTemplates",  # was django.template.backends.django.DjangoTemplates
    ...
}]
```

Only templates ending in `.mjml` are treated as email; everything else renders as before.

## The template

```html
{# templates/email/invite.mjml #}
<mjml>
  <mj-head><mj-title>{{ inviter.get_full_name }} invited you to {{ team.name }}</mj-title></mj-head>
  <mj-body>
    <mj-section><mj-column>
      <mj-text>Hi {{ invite.name }}, join {{ team.name }} on Example.</mj-text>
      <mj-button href="{% url 'accept_invite' invite.token %}">Accept</mj-button>
    </mj-column></mj-section>
  </mj-body>
</mjml>
```

A Django template first (`{% extends %}`, `{% url %}`, autoescaping), then MJML. `<mj-title>` is
the subject.

## The view

```python
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import get_template


def send_invite(request, team_id):
    team = get_object_or_404(Team, pk=team_id, owner=request.user)
    invite = Invite.objects.create(team=team, email=request.POST["email"])

    message = get_template("email/invite.mjml").render_email(
        {"invite": invite, "team": team, "inviter": request.user},
        request,                      # absolute URLs come from the request
        to=[invite.email],
    )
    message.send()
    return redirect("team", team.pk)
```

`render_email` gives back a Django `EmailMultiAlternatives`: subject from `<mj-title>`, HTML
from the MJML, plain text generated from it. Attach files, set `reply_to`, or send it in a
Celery task like any other Django message.

## Looking at it before it goes

Another view returns the same message as a page: an inbox row, the HTML and the text.

```python
from django.contrib.admin.views.decorators import staff_member_required
from mjml_templates.preview import preview_response


@staff_member_required
def invite_preview(request):
    message = get_template("email/invite.mjml").render_email(
        {"invite": sample_invite(), "team": sample_team(), "inviter": request.user}, request
    )
    return preview_response(message)
```

## More

- [Writing an email](writing-emails.md): layouts with `{% extends %}`, the subject, the plain-text part
- [Sending](sending.md): `render_email`, `render_email_parts` and what they return
- [Absolute URLs](absolute-urls.md): how relative links are made absolute, and `MJML_BASE_URL`
- [The plain-text fallback](plain-text.md): what the generated text looks like
- [Previewing](preview.md): the preview page and the embeddable fragment
- [Why this, and not django-mjml](why.md): how it differs, and when to pick which
