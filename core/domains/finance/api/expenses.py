import logging
from calendar import monthrange
from datetime import date

from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from core.models import (
    Expense,
    Group,
    GroupMonth,
    Payment,
    Student,
    User,
    UserBalance,
    UserTransaction,
)
from core.permissions import (
    IsCourseAdminOrManager,
    IsCourseAdminOrManagerReadOnly,
)

from ..serializers import (
    ExpenseSerializer,
    GroupMonthSerializer,
)

logger = logging.getLogger(__name__)

class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.none()
    permission_classes = [
        IsCourseAdminOrManager
    ]
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role == User.Role.COURSE_ADMIN:
            if user.company:
                return Expense.objects.filter(
                    company=user.company
                )

        if user.role == User.Role.MANAGER:
            if user.company:
                return Expense.objects.filter(
                    company=user.company
                ).exclude(category="salary")

        return Expense.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        company = user.company
        if not company:
            raise PermissionDenied(
                (
                    "У вас нет компании "
                    "для создания расходов."
                )
            )

        if (
            user.role == User.Role.MANAGER
            and serializer.validated_data.get("category") == "salary"
        ):
            raise PermissionDenied(
                "Менеджер не может создавать расходы по зарплатам."
            )

        serializer.save(company=company)

    def perform_update(self, serializer):
        user = self.request.user
        category = serializer.validated_data.get(
            "category",
            serializer.instance.category,
        )
        if user.role == User.Role.MANAGER and category == "salary":
            raise PermissionDenied(
                "Менеджер не может изменять расходы по зарплатам."
            )
        serializer.save()
