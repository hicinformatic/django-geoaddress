"""Django settings for testing django-geoaddress."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv  # type: ignore[import-not-found]

    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Environment variables loaded from {env_path}")
except ImportError:
    print("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")


def _env(key: str, default: str = "") -> str:
    """Shortcut to fetch environment variables with defaults."""
    return os.getenv(key, default)


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key-for-django-geoaddress")
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "djgeoaddress",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_boosted",
    "django_extensions",
    "tests.app",  # Test app with Location model using GeoaddressField
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tests.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates')],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Address autocomplete view configuration
GEOADDRESS_PROVIDERVIEW = True
GEOADDRESS_PROVIDERVIEW_AUTH = True
GEOADDRESS_ADDRESSVIEW = True
GEOADDRESS_ADDRESSVIEW_AUTH = True