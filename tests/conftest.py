from django.conf import settings


def pytest_configure():
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        TEMPLATES=[{"BACKEND": "mjml_templates.django.DjangoTemplates", "DIRS": [], "APP_DIRS": False}],
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
