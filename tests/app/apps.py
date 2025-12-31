"""App config for tests.app."""

from django.apps import AppConfig


class TestsAppConfig(AppConfig):
    """Configuration for tests.app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.app"
    verbose_name = "Test App"

