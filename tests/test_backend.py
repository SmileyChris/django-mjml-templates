"""The MJML template engine: a drop-in Django engine where ``.mjml`` files render
through Django then MJML, and can hand back the pieces of an email."""

import pytest
from django.core import mail
from django.template import engines
from django.template.loader import get_template, render_to_string

MJML = (
    "<mjml><mj-head>{% block head %}{% endblock %}</mj-head>"
    "<mj-body><mj-text>{% block body %}{% endblock %}</mj-text></mj-body></mjml>"
)


@pytest.fixture
def templates(settings, tmp_path):
    (tmp_path / "base.mjml").write_text(MJML)
    (tmp_path / "hello.mjml").write_text(
        '{% extends "base.mjml" %}{% block head %}<mj-title>Hi {{ name }} &amp; co</mj-title>{% endblock %}'
        '{% block body %}Hello <a href="https://x.test/">{{ name }}</a>{% endblock %}'
    )
    (tmp_path / "hello.txt").write_text("Plain hello {{ name }}\n")
    (tmp_path / "untitled.mjml").write_text('{% extends "base.mjml" %}{% block body %}no title{% endblock %}')
    (tmp_path / "linked.mjml").write_text(
        '{% extends "base.mjml" %}{% block body %}see <a href="https://x.test/">here</a>{% endblock %}'
    )
    (tmp_path / "plain.html").write_text("<p>{{ name }}</p>")
    settings.TEMPLATES = [t | {"DIRS": [tmp_path]} for t in settings.TEMPLATES]
    return tmp_path


def test_it_is_the_only_engine_and_leaves_other_files_alone(templates):
    assert len(list(engines)) == 1
    assert render_to_string("plain.html", {"name": "Ann"}) == "<p>Ann</p>"
    assert not hasattr(get_template("plain.html"), "render_email_parts")


def test_mjml_file_renders_django_tags_then_compiles_to_html(templates):
    html = render_to_string("hello.mjml", {"name": "Ann"})
    assert html.startswith("<!doctype html>")
    assert "<title>Hi Ann &amp; co</title>" in html
    assert 'href="https://x.test/">Ann</a>' in html
    assert "<mj-" not in html


def test_a_string_compiles_only_when_it_is_mjml(templates):
    engine = engines["django"]
    assert engine.from_string("<p>{{ name }}</p>").render({"name": "Ann"}) == "<p>Ann</p>"
    assert engine.from_string(MJML).render({}).startswith("<!doctype html>")


def test_render_email_parts_reads_the_subject_from_the_title(templates):
    subject, text, html = get_template("hello.mjml").render_email_parts({"name": "Ann"})
    assert subject == "Hi Ann & co"
    assert text == "Plain hello Ann\n"
    assert "<title>Hi Ann &amp; co</title>" in html


def test_render_email_parts_prefers_a_given_subject(templates):
    subject, _, _ = get_template("hello.mjml").render_email_parts({"name": "Ann"}, subject="Given")
    assert subject == "Given"


def test_render_email_parts_without_any_subject_is_an_error(templates):
    with pytest.raises(ValueError, match="untitled.mjml"):
        get_template("untitled.mjml").render_email_parts({})


def test_render_email_parts_falls_back_to_html2text_without_a_txt_file(templates):
    _, text, _ = get_template("untitled.mjml").render_email_parts({}, subject="s")
    assert text.strip() == "no title"
    # Links survive the conversion; the plain part has to be usable on its own.
    _, text, _ = get_template("linked.mjml").render_email_parts({}, subject="s")
    assert "https://x.test/" in text


def test_render_email_builds_an_unsent_message_with_both_parts(templates):
    msg = get_template("hello.mjml").render_email({"name": "Ann"}, to=["ann@x.test"], bcc=["me@x.test"])
    assert msg.subject == "Hi Ann & co"
    assert msg.body == "Plain hello Ann\n"
    assert msg.to == ["ann@x.test"] and msg.bcc == ["me@x.test"]
    html, mimetype = msg.alternatives[0]
    assert mimetype == "text/html" and html.startswith("<!doctype html>")
    assert mail.outbox == []
