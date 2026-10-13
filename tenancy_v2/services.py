"""Server-side tenant resolution; caller must authenticate the user first."""
from django.core.exceptions import PermissionDenied
from django.db import connections

from .models import CompanyMembership


def resolve_membership(user, company_id):
    if not user or not user.is_authenticated or not user.is_active:
        raise PermissionDenied('Authentication required')
    try:
        membership = (
            CompanyMembership.objects.using('default')
            .select_related('company')
            .get(user_id=user.pk, company_id=company_id, active=True, company__active=True)
        )
    except CompanyMembership.DoesNotExist as exc:
        raise PermissionDenied('Company membership required') from exc
    alias = membership.company.database_alias
    if not alias.startswith('tenant_') or alias not in connections.databases:
        raise PermissionDenied('Tenant is not available')
    return membership


def available_companies(user):
    if not user or not user.is_authenticated or not user.is_active:
        raise PermissionDenied('Authentication required')
    return CompanyMembership.objects.using('default').filter(
        user_id=user.pk, active=True, company__active=True
    ).select_related('company')
