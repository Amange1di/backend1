"""Tenant context is server-side only; resolve memberships before entering."""
from contextlib import contextmanager
from contextvars import ContextVar

from django.core.exceptions import PermissionDenied
from django.db import connections

_tenant = ContextVar('eduosh_tenant_v2', default=None)


def current_tenant():
    return _tenant.get()


@contextmanager
def tenant_context(alias):
    if (
        not isinstance(alias, str)
        or not alias.startswith('tenant_')
        or alias not in connections.databases
    ):
        raise PermissionDenied('Unknown or invalid tenant')
    token = _tenant.set(alias)
    try:
        yield
    finally:
        _tenant.reset(token)
