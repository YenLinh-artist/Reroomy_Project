"""Production-like settings for the shared Re:Room staging site.

Local development continues to use ``settings.py`` and its SQLite database.
The staging site requires a shared PostgreSQL URL and external media storage.
"""

import os

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F403


def _required_environment_value(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"Set the {name} environment variable for staging.")
    return value


SECRET_KEY = _required_environment_value("DJANGO_SECRET_KEY")
DEBUG = False
# Keep detailed exceptions in the hosting logs while DEBUG stays disabled for
# public requests. This makes staging 500s diagnosable without exposing traces
# in the browser.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "ERROR",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
ADMIN_DEMO_MODE = os.environ.get("ADMIN_DEMO_MODE", "true").lower() in {"1", "true", "yes", "on"}

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
]
render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if render_hostname:
    ALLOWED_HOSTS.append(render_hostname)
if not ALLOWED_HOSTS:
    # Lets build-time commands such as collectstatic and migrate run before
    # Render injects its public hostname. Set DJANGO_ALLOWED_HOSTS for other hosts.
    ALLOWED_HOSTS = ["localhost"]

database_url = _required_environment_value("DATABASE_URL")
DATABASES = {
    "default": dj_database_url.parse(
        database_url,
        conn_max_age=600,
        ssl_require=True,
    )
}

# A single shared media bucket prevents uploaded product photos from being
# lost when the web service restarts or redeploys.
_required_environment_value("CLOUDINARY_URL")
INSTALLED_APPS = [*INSTALLED_APPS, "cloudinary", "cloudinary_storage"]  # noqa: F405
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405
MEDIA_URL = "/media/"

MIDDLEWARE = list(MIDDLEWARE)  # noqa: F405
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

csrf_origins = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
csrf_origins.extend(f"https://{host}" for host in ALLOWED_HOSTS if host != "localhost")
CSRF_TRUSTED_ORIGINS = sorted(set(csrf_origins))

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
