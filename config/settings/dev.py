from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "library_db"),
        "USER": os.getenv("POSTGRES_USER", "library_user"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "library_password"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432")
    }
}