from django.utils import timezone

from core.models import (
    CompanyBalance,
    Transaction,
)


BOOST_COST = 500
URGENT_COST = 200


def resolve_user_company_name(user) -> str:
    company = getattr(user, "company", None)
    if company and company.name:
        return company.name.strip()

    created_by = getattr(user, "created_by", None)
    created_company = getattr(
        created_by,
        "company",
        None,
    )
    if created_company and created_company.name:
        return created_company.name.strip()

    return ""


def ensure_balance(company, amount):
    try:
        balance = CompanyBalance.objects.get(
            company=company
        )
    except CompanyBalance.DoesNotExist:
        return None

    if balance.balance < amount:
        return None

    return balance


def charge_promotion(
    *,
    company,
    amount,
    reason,
    transaction_type,
):
    balance = ensure_balance(
        company,
        amount,
    )
    if not balance:
        return False

    balance.balance -= amount
    balance.save()

    Transaction.objects.create(
        company=company,
        amount=-amount,
        reason=reason,
        transaction_type=transaction_type,
    )
    return True


def promote_item(item, *, days: int):
    item.is_promoted = True
    item.promoted_until = (
        timezone.now()
        + timezone.timedelta(days=days)
    )
    item.save()
    return item


def mark_urgent(item, *, days: int):
    item.is_urgent = True
    item.urgent_until = (
        timezone.now()
        + timezone.timedelta(days=days)
    )
    item.save()
    return item
