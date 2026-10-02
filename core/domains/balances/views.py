from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    Company,
    CompanyBalance,
    Transaction,
    User,
    UserBalance,
)


class UserBalanceHistoryView(APIView):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request):
        if request.user.role not in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            return Response(
                {
                    "detail": (
                        "staff_only"
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        company_id = (
            request.user.company_id
            or getattr(
                getattr(
                    request.user,
                    "created_by",
                    None,
                ),
                "company_id",
                None,
            )
        )

        if not company_id:
            return Response(
                {
                    "detail": (
                        "company_not_found"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_company = Company.objects.filter(
            id=company_id
        ).first()

        if not user_company:
            return Response(
                {
                    "detail": (
                        "company_not_found"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        transactions = Transaction.objects.filter(
            company=user_company
        ).order_by("-timestamp")

        balance = 0
        try:
            company_balance = (
                CompanyBalance.objects.get(
                    company=user_company
                )
            )
            balance = company_balance.balance
        except CompanyBalance.DoesNotExist:
            pass

        data = []
        for transaction in transactions:
            data.append(
                {
                    "id": transaction.id,
                    "amount": transaction.amount,
                    "reason": transaction.reason,
                    "transaction_type": (
                        transaction.transaction_type
                    ),
                    "transaction_type_display": (
                        transaction
                        .get_transaction_type_display()
                    ),
                    "timestamp": (
                        transaction.timestamp
                        .isoformat()
                    ),
                    "actor": (
                        transaction.user.get_full_name()
                        or transaction.user.username
                        if transaction.user
                        else None
                    ),
                    "actor_role": (
                        transaction.user.role
                        if transaction.user
                        else None
                    ),
                    "balance_after": balance,
                }
            )
            balance -= transaction.amount

        current = (
            CompanyBalance.objects.filter(
                company=user_company
            ).first()
        )

        return Response(
            {
                "balance": (
                    current.balance
                    if current
                    else 0
                ),
                "transactions": data,
            }
        )


class UserBalanceMeView(APIView):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request):
        user = request.user

        if user.role in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            company_id = (
                user.company_id
                or getattr(
                    getattr(user, "created_by", None),
                    "company_id",
                    None,
                )
            )

            if not company_id:
                return Response(
                    {"balance": 0}
                )

            company_balance, _ = (
                CompanyBalance.objects.get_or_create(
                    company_id=company_id
                )
            )
            return Response(
                {
                    "balance": company_balance.balance
                }
            )

        user_balance, _ = (
            UserBalance.objects.get_or_create(
                user=user
            )
        )
        return Response(
            {
                "balance": user_balance.balance
            }
        )
