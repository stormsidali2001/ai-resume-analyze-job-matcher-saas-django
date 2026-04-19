"""
config/settings/base.py

Shared settings for all environments.
"""

from datetime import timedelta
from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY", default="insecure-dev-key-replace-in-production")

GEMINI_API_KEY: str = config("GEMINI_API_KEY", default="")

DEBUG = False

ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    # daphne must be first — overrides runserver with ASGI-capable server
    "daphne",
    "channels",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "infrastructure",
    "interfaces",
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

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="resumeai"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default="postgres"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

AUTH_USER_MODEL = "infrastructure.CustomUser"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# OpenAPI schema
SPECTACULAR_SETTINGS = {
    "TITLE": "ResumeAI API",
    "DESCRIPTION": (
        "Intelligent resume analyzer and job matching platform.\n\n"
        "## Authentication\n"
        "All protected endpoints require a Bearer JWT token in the `Authorization` header.\n"
        "Obtain tokens via `POST /api/auth/token/` or `POST /api/auth/register/`."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/",
}

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "EXCEPTION_HANDLER": "interfaces.api.exceptions.custom_exception_handler",
}

# Simple JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ---------------------------------------------------------------------------
# ASGI / Django Channels
# ---------------------------------------------------------------------------

ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Redis & Celery
# ---------------------------------------------------------------------------

REDIS_URL: str = config("REDIS_URL", default="redis://localhost:6379")

# Django cache — Redis DB 1 (DB 0 reserved for Celery broker)
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_URL}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "resumeai",
    }
}

# Celery broker + result backend
CELERY_BROKER_URL: str = f"{REDIS_URL}/0"
CELERY_RESULT_BACKEND: str = f"{REDIS_URL}/0"
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_TIME_LIMIT = 120        # hard kill after 2 min (Gemini can be slow)
CELERY_TASK_SOFT_TIME_LIMIT = 90    # raise SoftTimeLimitExceeded at 90 s
CELERY_TASK_ACKS_LATE = True        # only ack after the task succeeds
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # one task at a time per worker

# Channel layers — Redis DB 2 (DB 0 = Celery, DB 1 = cache)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [f"{REDIS_URL}/2"]},
    }
}
