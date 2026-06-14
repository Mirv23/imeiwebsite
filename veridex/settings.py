"""
Django settings for the Veridex IMEI verification site.

Solid, backend-ready defaults: env-driven secrets, a clear app boundary
(`core`), template + static dirs wired, and a switchable database so a real
Postgres can drop in later without touching the code.
"""
from pathlib import Path
import os

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security -------------------------------------------------------------
# Override these via environment variables in production.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-insecure-change-me-before-deploying-veridex",
)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

# Hosts: localhost for dev, *.vercel.app for the deployment, plus anything
# passed in DJANGO_ALLOWED_HOSTS (comma-separated, e.g. a custom domain).
ALLOWED_HOSTS = [
    "localhost", "127.0.0.1", "0.0.0.0", ".vercel.app",
]
ALLOWED_HOSTS += [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h]

# CSRF over HTTPS on Vercel + any custom domain.
CSRF_TRUSTED_ORIGINS = ["https://*.vercel.app"]
CSRF_TRUSTED_ORIGINS += [
    o for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o
]

# --- Applications ---------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise serves static files directly from the app (works in serverless).
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "veridex.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.brand",
            ],
        },
    },
]

WSGI_APPLICATION = "veridex.wsgi.application"
ASGI_APPLICATION = "veridex.asgi.application"

# --- Database -------------------------------------------------------------
# Local dev: SQLite. Production (Vercel/Neon/Supabase): set DATABASE_URL and
# dj-database-url wires up Postgres automatically. Vercel's filesystem is
# read-only + ephemeral, so SQLite cannot be used there — DATABASE_URL is
# required in production.
# Accept either a generic DATABASE_URL (Neon/Supabase) or Vercel Postgres's
# POSTGRES_URL. Falls back to local SQLite when neither is set.
_DB_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
DATABASES = {
    "default": dj_database_url.parse(
        _DB_URL or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=bool(_DB_URL) and not DEBUG,
    )
}

# --- Password validation --------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- I18N -----------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static files ---------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise: compress + far-future cache headers, no hashed manifest (so it
# stays safe in serverless where staticfiles.json may not ship with the lambda).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Veridex business config ---------------------------------------------
# Currency + brand constants surfaced to templates via context processor.
VERIDEX = {
    "currency": "USD",
    "currency_symbol": "$",
    "support_email": "help@veridex.io",
}
