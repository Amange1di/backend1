"""Isolated v2 settings: explicitly opt in with DJANGO_SETTINGS_MODULE.

Do not point any of these URLs at the existing production database.
The legacy core app still uses cross-model relations; multi-tenant ORM
routing is deliberately NOT enabled until models are separated and audited.
"""
import os

if os.environ.get("EDUOSH_V2_ISOLATED") != "true":
    raise RuntimeError("Set EDUOSH_V2_ISOLATED=true to enable isolated API v2 settings")

from .settings import *  # noqa: F403,F401,E402
from .tenant_v2 import build_v2_databases

DATABASES = build_v2_databases()
DATABASE_ROUTERS = []
