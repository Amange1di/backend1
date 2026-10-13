"""Tenant context must come from a verified membership, not a request header."""
from contextlib import contextmanager

from config.tenant_context_v2 import tenant_context
from .services import resolve_membership


@contextmanager
def authorized_tenant(user, company_id):
    membership = resolve_membership(user, company_id)
    with tenant_context(membership.company.database_alias):
        yield membership
