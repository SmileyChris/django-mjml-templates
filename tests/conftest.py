from django.conf import settings


def pytest_configure():
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "django.contrib.sites"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        SITE_ID=1,
        # Pinned so tests that are not about URL derivation never reach the Site table.
        MJML_BASE_URL="https://x.test",
        TEMPLATES=[{"BACKEND": "mjml_templates.django.DjangoTemplates", "DIRS": [], "APP_DIRS": False}],
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
