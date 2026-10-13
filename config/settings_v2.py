"""Opt-in isolated v2 settings. Never use production DB credentials."""
import os

if os.environ.get("EDUOSH_V2_ISOLATED") != "true":
    raise RuntimeError("Set EDUOSH_V2_ISOLATED=true to enable isolated API v2 settings")

from .settings import *  # noqa: F403,F401,E402
from .tenant_v2 import build_v2_databases

DATABASES = build_v2_databases()
INSTALLED_APPS = [*INSTALLED_APPS, "tenancy_v2", "operations_v2"]
DATABASE_ROUTERS = ["config.router_v2.V2Router"]

ROOT_URLCONF = "config.urls_v2"
