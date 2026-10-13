"""Apply tenant and branch restrictions before reading operational records."""
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet

from operations_v2.models import TenantBranch


GLOBAL_BRANCH_ROLES = frozenset(("owner", "admin"))


def authorized_branch(membership, branch_id):
    if not isinstance(branch_id, int) or isinstance(branch_id, bool) or branch_id <= 0:
        raise PermissionDenied("Valid branch required")
    if membership.role not in GLOBAL_BRANCH_ROLES and membership.branch_id != branch_id:
        raise PermissionDenied("Branch access denied")
    try:
        return TenantBranch.objects.get(
            pk=branch_id,
            company_id=membership.company_id,
            active=True,
        )
    except TenantBranch.DoesNotExist as exc:
        raise PermissionDenied("Branch unavailable") from exc


def scope_to_membership(queryset: QuerySet, membership, branch_field="branch_id"):
    """Caller must enter authorized_tenant before evaluating this queryset."""
    if membership.role in GLOBAL_BRANCH_ROLES:
        return queryset.filter(**{f"{branch_field}__in": TenantBranch.objects.filter(
            company_id=membership.company_id, active=True
        ).values("pk")})
    if membership.branch_id is None:
        return queryset.none()
    authorized_branch(membership, membership.branch_id)
    return queryset.filter(**{branch_field: membership.branch_id})
