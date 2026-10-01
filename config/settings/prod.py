import os

from .base import *  # noqa: F401, F403

DEBUG = False

ALLOWED_HOSTS = os.environ["DJANGO_ALLOWED_HOSTS"].split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ["POSTGRES_HOST"],
        "PORT": os.environ["POSTGRES_PORT"],
    }
}

# Static files are served by WhiteNoise (no nginx needed); run collectstatic first.
MIDDLEWARE.insert(  # noqa: F405
    MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,  # noqa: F405
    "whitenoise.middleware.WhiteNoiseMiddleware",
)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# HTTPS hardening. Enable (DJANGO_HTTPS=True) only when the site is served over HTTPS
# (e.g. behind a reverse proxy that sets X-Forwarded-Proto), otherwise login breaks.
if os.getenv("DJANGO_HTTPS", "False") == "True":
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000

# Let Django serve uploaded media (book covers). Convenient without nginx/S3, but slow:
# set DJANGO_SERVE_MEDIA=False when media is served by a reverse proxy or object storage.
SERVE_MEDIA = os.getenv("DJANGO_SERVE_MEDIA", "True") == "True"
