from django.db import transaction
from django.utils import timezone

from core.models import (
    CompanyBalance,
    Transaction,
)


BOOST_COST = 500
URGENT_COST = 200

# Company Marketplace currency.
# 1 Coin is valued at 1.5 KGS. Coins are used only for promoting
# company courses and vacancies inside Marketplace.
COIN_VALUE_KGS = 1.5


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
    user=None,
):
    if amount <= 0:
        return False

    with transaction.atomic():
        try:
            balance = (
                CompanyBalance.objects
                .select_for_update()
                .get(company=company)
            )
        except CompanyBalance.DoesNotExist:
            return False

        if balance.balance < amount:
            return False

        balance.balance -= amount
        balance.save(update_fields=["balance", "last_update"])
        Transaction.objects.create(
            company=company,
            user=user,
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
    now = timezone.now()
    current_until = getattr(item, "urgent_until", None)
    starts_from = (
        current_until
        if current_until and current_until > now
        else now
    )
    item.is_urgent = True
    item.urgent_until = (
        starts_from
        + timezone.timedelta(days=days)
    )
    item.save(update_fields=["is_urgent", "urgent_until", "updated_at"])
    return item
