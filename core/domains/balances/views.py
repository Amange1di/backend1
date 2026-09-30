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
from core.domains.users.services import (
    resolve_user_company_name,
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
                        "Доступно только для "
                        "course_admin и manager."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        company_name = resolve_user_company_name(
            request.user
        )
        if not company_name:
            return Response(
                {
                    "detail": (
                        "Компания не найдена."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_company = request.user.company

        if (
            not user_company
            and request.user.role
            == User.Role.MANAGER
        ):
            company_name = (
                resolve_user_company_name(
                    request.user
                )
            )
            if company_name:
                user_company = (
                    Company.objects.filter(
                        name=company_name
                    ).first()
                )

        if not user_company:
            return Response(
                {
                    "detail": (
                        "Компания не найдена."
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
        user_balance, _ = (
            UserBalance.objects.get_or_create(
                user=request.user
            )
        )
        return Response(
            {
                "balance": user_balance.balance
            }
        )
