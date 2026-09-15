"""Relative URLs in rendered email HTML become absolute, so links work in a mail client."""

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import get_template
from django.test import RequestFactory

from mjml_templates.absolute import absolutise, base_url


def test_absolutise_rewrites_a_root_relative_href():
    html = '<a href="/signup">go</a>'
    assert absolutise(html, "https://x.test") == '<a href="https://x.test/signup">go</a>'


@pytest.mark.parametrize(
    "url",
    [
        "https://other.test/x",
        "http://other.test/x",
        "mailto:a@b.test",
        "tel:+6421000000",
        "data:image/png;base64,AAAA",
        "cid:logo.png",
        "//cdn.test/x.png",
        "#anchor",
        "",
    ],
)
def test_absolutise_leaves_non_relative_urls_alone(url):
    html = f'<a href="{url}">go</a>'
    assert absolutise(html, "https://x.test") == html


def test_absolutise_rewrites_src_and_background_too():
    html = '<td background="/bg.png"><img src="/logo.png"></td>'
    assert absolutise(html, "https://x.test") == (
        '<td background="https://x.test/bg.png"><img src="https://x.test/logo.png"></td>'
    )


def test_absolutise_rewrites_css_url_values_quoted_or_bare():
    html = "<style>a{background:url('/a.png')} b{background:url(/b.png)}</style>"
    assert absolutise(html, "https://x.test") == (
        "<style>a{background:url('https://x.test/a.png')} b{background:url(https://x.test/b.png)}</style>"
    )


def test_base_url_comes_from_the_request_when_there_is_one():
    request = RequestFactory().get("/some/page/", secure=True)
    assert base_url(request) == "https://testserver"


def test_base_url_is_empty_when_the_current_site_cannot_be_resolved(settings):
    settings.MJML_BASE_URL = "https://"
    settings.SITE_ID = None
    assert base_url() == ""


def test_base_url_falls_back_to_a_full_url_setting(settings):
    settings.MJML_BASE_URL = "https://mail.test/"
    assert base_url() == "https://mail.test"


def test_base_url_prefers_the_request_over_the_setting(settings):
    settings.MJML_BASE_URL = "https://mail.test"
    assert base_url(RequestFactory().get("/", secure=True)) == "https://testserver"


@pytest.mark.django_db
@pytest.mark.parametrize("scheme", ["https://", "https:", "https"])
def test_base_url_combines_a_scheme_only_setting_with_the_current_site(settings, scheme):
    settings.MJML_BASE_URL = scheme
    assert base_url() == "https://example.com"


@pytest.mark.django_db
def test_base_url_defaults_to_https_over_the_current_site(settings):
    del settings.MJML_BASE_URL
    assert base_url() == "https://example.com"


def test_base_url_is_empty_when_the_sites_app_is_not_installed(settings):
    settings.MJML_BASE_URL = "https://"
    settings.INSTALLED_APPS = [a for a in settings.INSTALLED_APPS if a != "django.contrib.sites"]
    assert base_url() == ""


@pytest.mark.parametrize("setting", ["example.com", "//example.com", "", "/x"])
def test_a_base_url_setting_without_a_scheme_is_an_error(settings, setting):
    settings.MJML_BASE_URL = setting
    with pytest.raises(ImproperlyConfigured, match="MJML_BASE_URL"):
        base_url()


@pytest.fixture
def relative(settings, tmp_path):
    (tmp_path / "relative.mjml").write_text(
        "<mjml><mj-head><mj-title>Hi</mj-title></mj-head><mj-body><mj-section><mj-column>"
        '<mj-text>See <a href="/signup">signup</a></mj-text>'
        '<mj-image src="/logo.png" />'
        "<mj-text>Or paste {{ mjml_base }}/signup</mj-text>"
        "</mj-column></mj-section></mj-body></mjml>"
    )
    (tmp_path / "relative.txt").write_text("Sign up: {{ mjml_base }}/signup\n")
    (tmp_path / "nosibling.mjml").write_text(
        "<mjml><mj-body><mj-section><mj-column>"
        '<mj-text>See <a href="/signup">signup</a></mj-text>'
        "</mj-column></mj-section></mj-body></mjml>"
    )
    settings.TEMPLATES = [t | {"DIRS": [tmp_path]} for t in settings.TEMPLATES]
    return tmp_path


def test_rendering_with_a_request_makes_links_absolute(relative):
    html = get_template("relative.mjml").render({}, RequestFactory().get("/", secure=True))
    assert 'href="https://testserver/signup"' in html
    assert 'src="https://testserver/logo.png"' in html


def test_the_plain_text_part_inherits_the_absolute_urls(relative):
    parts = get_template("nosibling.mjml").render_email_parts({}, RequestFactory().get("/", secure=True), subject="s")
    assert "https://testserver/signup" in parts.text


def test_rendering_leaves_urls_alone_when_no_base_can_be_derived(relative, settings):
    settings.MJML_BASE_URL = "https://"
    settings.INSTALLED_APPS = [a for a in settings.INSTALLED_APPS if a != "django.contrib.sites"]
    html = get_template("relative.mjml").render({})
    assert 'href="/signup"' in html


def test_the_mjml_base_variable_is_available_to_the_template(relative):
    html = get_template("relative.mjml").render({}, RequestFactory().get("/", secure=True))
    assert "Or paste https://testserver/signup" in html


def test_the_mjml_base_variable_is_available_to_the_text_sibling(relative):
    _, text, _ = get_template("relative.mjml").render_email_parts({}, RequestFactory().get("/", secure=True))
    assert text == "Sign up: https://testserver/signup\n"


def test_a_caller_supplied_mjml_base_wins(relative):
    html = get_template("relative.mjml").render(
        {"mjml_base": "https://brand.test"}, RequestFactory().get("/", secure=True)
    )
    assert "Or paste https://brand.test/signup" in html


def test_absolutise_without_a_base_changes_nothing():
    html = '<img src="logo.png"><a href="/signup">go</a>'
    assert absolutise(html, "") == html
