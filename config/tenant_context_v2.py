"""Tenant database context for the isolated v2 API."""
from contextlib import contextmanager
from contextvars import ContextVar

from django.core.exceptions import PermissionDenied

_tenant = ContextVar('eduosh_tenant_v2', default=None)


def current_tenant():
    return _tenant.get()


@contextmanager
def tenant_context(alias):
    if not isinstance(alias, str) or not alias.startswith('tenant_'):
        raise PermissionDenied('Invalid tenant')
    token = _tenant.set(alias)
    try:
        yield
    finally:
        _tenant.reset(token)
