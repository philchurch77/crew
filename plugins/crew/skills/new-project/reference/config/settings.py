"""Django settings. Everything that differs between machines comes from the
environment; nothing here is a secret."""
from datetime import timedelta
from pathlib import Path
import os

from dotenv import load_dotenv

from config.deploy import (
    database_config,
    deployed_hostname,
    is_deployed,
    trust_forwarded_for,
    unresolved_key_vault_references,
)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# An unresolved Key Vault reference arrives as its own text: a guessable
# SECRET_KEY. Refuse, naming the variables, never their values.
if names := unresolved_key_vault_references(os.environ):
    raise RuntimeError(f"Key Vault reference not resolved: {', '.join(names)}.")

# --- Core ---
SECRET_KEY = os.getenv("SECRET_KEY", "")
DEBUG = os.getenv("DEBUG", "0") in ("1", "true", "True")

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-secret-key"  # local development only
    else:
        raise RuntimeError("SECRET_KEY must be set in production")

# DEBUG on a public site would mean the dev key and traceback pages.
if DEBUG and is_deployed(os.environ):
    raise RuntimeError("DEBUG must not be enabled on a deployed site")

# The top bar's two names (core.context_processors.names).
PRODUCT_NAME = os.getenv("PRODUCT_NAME", "Product")
CLIENT_NAME = os.getenv("CLIENT_NAME", "Client name")

# One writable root. On App Service, the persistent volume, never wwwroot
# (wiped on deploy).
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR if DEBUG else "/home/site/data"))

# --- Hosts / CSRF ---
# No platform wildcard: it would trust every site on the platform.
extra_hosts = [x.strip() for x in os.getenv("ALLOWED_HOSTS_EXTRA", "").split(",") if x.strip()]
ALLOWED_HOSTS = [h for h in [deployed_hostname(os.environ), *extra_hosts] if h]
if DEBUG:
    ALLOWED_HOSTS += ["localhost", "127.0.0.1"]

CSRF_TRUSTED_ORIGINS = [f"https://{h.lstrip('.')}" for h in ALLOWED_HOSTS]
if DEBUG:
    CSRF_TRUSTED_ORIGINS += ["http://localhost", "http://127.0.0.1"]

# --- Apps / Middleware ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "core",
    "accounts",
    "axes",
]

MIDDLEWARE = [
    # First, so every response carries the policy.
    "core.middleware.ContentSecurityPolicyMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Last, per django-axes.
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "core.context_processors.names",
    ]},
}]

# --- Uploads ---
# No page takes a file until one is designed (article 6, and the Purser):
# memory only, so no request is spooled to disk.
FILE_UPLOAD_HANDLERS = ["django.core.files.uploadhandler.MemoryFileUploadHandler"]
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024  # the whole request

# --- Database ---
DATABASES = {
    "default": database_config(os.environ, os.getenv("SQLITE_PATH") or (DATA_DIR / "db.sqlite3")),
}

# --- Cache ---
# Anything counted here (a rate limit) must be shared across workers:
# LocMem would multiply the limit by the worker count.
if DEBUG:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
            "LOCATION": str(DATA_DIR / "django_cache"),
        },
    }

# --- i18n / tz ---
LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

# --- Static ---
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# No "default" storage: nothing writes files, so any future use fails loudly
# rather than saving into the app directory.
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage" if DEBUG
        else "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TEST_RUNNER = "core.testing.FastHasherRunner"

# --- Passwords ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Proxy & transport security ---
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = not DEBUG  # allow http locally
CSRF_COOKIE_SECURE = not DEBUG     # allow http locally
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
# Set by core.middleware. Nothing loads or connects off-site, so nothing a
# person typed can leave the page in a URL. Adding 'unsafe-inline',
# 'unsafe-eval' or a remote origin is a decision, not a fix.
SECURE_CSP = {
    "default-src": ["'none'"],
    "script-src": ["'self'"],
    "style-src": ["'self'"],
    "img-src": ["'self'"],
    "font-src": ["'self'"],
    "connect-src": ["'self'"],
    "form-action": ["'self'"],
    "frame-ancestors": ["'none'"],
    "base-uri": ["'none'"],
    "object-src": ["'none'"],
}
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    # Raise to 31536000 + INCLUDE_SUBDOMAINS once stable.
    SECURE_HSTS_SECONDS = 3600

# --- Auth ---
# Shared computers: a session ends with the browser, 24 hours at most.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 60 * 60 * 24

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"

# --- Login throttle (django-axes) ---
# Login and admin alike. Keyed on username and address together, so nobody
# can lock a named person out from anywhere.
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",  # must be first
    "django.contrib.auth.backends.ModelBackend",
]
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_LOCKOUT_TEMPLATE = "accounts/locked_out.html"
AXES_DISABLE_ACCESS_LOG = True  # no table of every sign-in and its address
AXES_CLIENT_IP_CALLABLE = "accounts.throttle.client_ip"
# On each new host, check a failed sign-in records your real address under
# Admin > Axes, not a proxy's.
TRUST_X_FORWARDED_FOR = trust_forwarded_for(os.environ)

# --- Logging ---
# System errors only. Never anything a person typed.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "django.security.csrf": {"handlers": ["console"], "level": "INFO", "propagate": False},
        # Failures and lockouts only; username and address masked.
        "axes": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
