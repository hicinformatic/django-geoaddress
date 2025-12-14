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
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "djgeoaddress",
    "tests",  # Test app with TestLocation model
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
        "DIRS": [],
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

# =============================================================================
# Address verification backends configuration
# =============================================================================

GEOADDRESS_BACKENDS = [
    {
        "class": "geoaddress.backends.nominatim.NominatimAddressBackend",
        "config": {
            "NOMINATIM_USER_AGENT": _env("NOMINATIM_USER_AGENT", "django-geoaddress/1.0"),
            "NOMINATIM_BASE_URL": _env("NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org"),
        },
    },
    {
        "class": "geoaddress.backends.photon.PhotonAddressBackend",
        "config": {
            "PHOTON_BASE_URL": _env("PHOTON_BASE_URL", "https://photon.komoot.io"),
        },
    },
    {
        "class": "geoaddress.backends.locationiq.LocationIQAddressBackend",
        "config": {
            "LOCATIONIQ_API_KEY": _env("LOCATIONIQ_API_KEY", ""),
            "LOCATIONIQ_BASE_URL": _env("LOCATIONIQ_BASE_URL", "https://api.locationiq.com/v1"),
        },
    },
    {
        "class": "geoaddress.backends.opencage.OpenCageAddressBackend",
        "config": {
            "OPENCAGE_API_KEY": _env("OPENCAGE_API_KEY", ""),
            "OPENCAGE_BASE_URL": _env(
                "OPENCAGE_BASE_URL", "https://api.opencagedata.com/geocode/v1"
            ),
        },
    },
    {
        "class": "geoaddress.backends.geocode_earth.GeocodeEarthAddressBackend",
        "config": {
            "GEOCODE_EARTH_API_KEY": _env("GEOCODE_EARTH_API_KEY", ""),
            "GEOCODE_EARTH_BASE_URL": _env(
                "GEOCODE_EARTH_BASE_URL", "https://api.geocode.earth/v1"
            ),
        },
    },
    {
        "class": "geoaddress.backends.geoapify.GeoapifyAddressBackend",
        "config": {
            "GEOAPIFY_API_KEY": _env("GEOAPIFY_API_KEY", ""),
            "GEOAPIFY_BASE_URL": _env("GEOAPIFY_BASE_URL", "https://api.geoapify.com/v1"),
        },
    },
    {
        "class": "geoaddress.backends.maps_co.MapsCoAddressBackend",
        "config": {
            "MAPS_CO_API_KEY": _env("MAPS_CO_API_KEY", ""),
            "MAPS_CO_BASE_URL": _env("MAPS_CO_BASE_URL", "https://geocode.maps.co"),
        },
    },
    {
        "class": "geoaddress.backends.google_maps.GoogleMapsAddressBackend",
        "config": {
            "GOOGLE_MAPS_API_KEY": _env("GOOGLE_MAPS_API_KEY", ""),
        },
    },
    {
        "class": "geoaddress.backends.mapbox.MapboxAddressBackend",
        "config": {
            "MAPBOX_ACCESS_TOKEN": _env("MAPBOX_ACCESS_TOKEN", ""),
        },
    },
    {
        "class": "geoaddress.backends.here.HereAddressBackend",
        "config": {
            "HERE_APP_ID": _env("HERE_APP_ID", ""),
            "HERE_APP_CODE": _env("HERE_APP_CODE", ""),
        },
    },
]

# Address autocomplete view configuration
GEOADDRESS_VIEW_ENABLE = _env("GEOADDRESS_VIEW_ENABLE", "True").lower() in ("true", "1", "yes")
GEOADDRESS_VIEW_AUTH_ENABLE = _env("GEOADDRESS_VIEW_AUTH_ENABLE", "False").lower() in (
    "true",
    "1",
    "yes",
)
