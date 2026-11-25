"""Django settings. The database lives inside the workspace (journal mode DELETE)."""

from __future__ import annotations

import os
from pathlib import Path

from flanders.workspace.layout import Workspace

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE = Workspace.default()

SECRET_KEY = os.environ.get("FLANDERS_SECRET_KEY", "flanders-local-only-not-secret")
DEBUG = os.environ.get("FLANDERS_DEBUG", "0") == "1"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
if os.environ.get("FLANDERS_IN_CONTAINER") == "1":
    # The shim publishes the port on host loopback only; inside the container the
    # server must listen on 0.0.0.0, and requests arrive with the host's Host header.
    ALLOWED_HOSTS.append("0.0.0.0")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "flanders.workspace",
    "flanders.web.runs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "flanders.web.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request",
                                           "flanders.web.runs.context.nav"]},
    }
]
WSGI_APPLICATION = "flanders.web.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": WORKSPACE.db_path,
        "OPTIONS": {"timeout": 30, "init_command": "PRAGMA journal_mode=DELETE;"},
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
