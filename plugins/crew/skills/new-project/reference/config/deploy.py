"""Platform detection and the database: pure functions of the environment,
no Django, so tests pass a plain dict."""
import re


def is_deployed(environ):
    """Azure App Service sets WEBSITE_HOSTNAME."""
    return "WEBSITE_HOSTNAME" in environ


def trust_forwarded_for(environ):
    """True behind a proxy that appends the real client to X-Forwarded-For.
    Anywhere else a client could write the header and pick its throttle key."""
    return is_deployed(environ)


# App Service passes an unresolvable reference through verbatim. Loose on
# purpose: quotes, spaces, any case, App Configuration too.
UNRESOLVED_REFERENCE = re.compile(r"^\W*@microsoft\.(keyvault|appconfiguration)\s*\(", re.IGNORECASE)


def unresolved_key_vault_references(environ):
    """Sorted names (never values) of variables still holding a reference."""
    return sorted(
        name for name, value in environ.items()
        if UNRESOLVED_REFERENCE.match(value)
    )


def deployed_hostname(environ):
    return environ.get("WEBSITE_HOSTNAME")


POSTGRES_REQUIRED = ("POSTGRES_DB", "POSTGRES_USER")
# "allow" and "prefer" fall back to plain text silently.
DEPLOYED_SSLMODES = ("require", "verify-ca", "verify-full")


def database_config(environ, sqlite_path):
    """SQLite at ``sqlite_path``, or Postgres when POSTGRES_HOST is set.

    Deployed, POSTGRES_HOST is required, so a forgotten setting stops the
    site rather than booting it on an empty SQLite file.
    """
    host = environ.get("POSTGRES_HOST", "").strip()
    if not host and is_deployed(environ):
        raise RuntimeError("POSTGRES_HOST is required on a deployed site.")
    if not host:
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": sqlite_path,
            # Wait for the lock and take it up front, so a save is not
            # refused mid-transaction.
            "OPTIONS": {"timeout": 20, "transaction_mode": "IMMEDIATE"},
        }
    missing = [name for name in POSTGRES_REQUIRED if not environ.get(name, "").strip()]
    if missing:
        raise RuntimeError(f"POSTGRES_HOST is set but {', '.join(missing)} is not.")
    sslmode = environ.get("POSTGRES_SSLMODE", "").strip() or "require"
    if is_deployed(environ) and sslmode not in DEPLOYED_SSLMODES:
        raise RuntimeError("POSTGRES_SSLMODE must be require or stronger on a deployed site.")
    return {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": host,
        "PORT": environ.get("POSTGRES_PORT", "").strip() or "5432",
        "NAME": environ["POSTGRES_DB"].strip(),
        "USER": environ["POSTGRES_USER"].strip(),
        "PASSWORD": environ.get("POSTGRES_PASSWORD", ""),  # may be empty locally
        "OPTIONS": {"sslmode": sslmode, "connect_timeout": 10},
        # UTF-8 whatever template1 is, so tests keep emoji as production does.
        "TEST": {"CHARSET": "UTF8", "TEMPLATE": "template0"},
    }
