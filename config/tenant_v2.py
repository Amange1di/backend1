"""Opt-in database configuration for isolated EduOsh API v2 environments.

This module does not modify Django settings or route existing ORM queries.
Never pass production database credentials to the v2 deployment.
"""
import os
from urllib.parse import parse_qs, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured


def _postgres_config(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in ("postgres", "postgresql") or not parsed.hostname or not parsed.path.strip("/"):
        raise ImproperlyConfigured("Expected a complete PostgreSQL URL")
    params = parse_qs(parsed.query)
    options = {}
    if "sslmode" in params:
        options["sslmode"] = params["sslmode"][0]
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parsed.path.lstrip("/")),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname,
        "PORT": parsed.port or 5432,
        "CONN_MAX_AGE": 0,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": options,
    }


def build_v2_databases(environ=None) -> dict:
    """Fail closed unless central and demo tenant have distinct databases."""
    env = os.environ if environ is None else environ
    central = env.get("EDUOSH_V2_CENTRAL_DATABASE_URL", "").strip()
    demo = env.get("EDUOSH_V2_DEMO_DATABASE_URL", "").strip()
    if not central or not demo:
        raise ImproperlyConfigured("API v2 requires separate central and demo PostgreSQL URLs")
    central_db = _postgres_config(central)
    demo_db = _postgres_config(demo)
    identity = lambda d: (d["HOST"].lower(), str(d["PORT"]), d["NAME"].lower())
    if identity(central_db) == identity(demo_db):
        raise ImproperlyConfigured("Central and tenant databases must be different")
    return {"default": central_db, "tenant_demo": demo_db}
