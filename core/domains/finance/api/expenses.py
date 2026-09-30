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

        if user.role in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            if user.company:
                return Expense.objects.filter(
                    company=user.company
                )

        return Expense.objects.none()

    def perform_create(self, serializer):
        company = self.request.user.company
        if not company:
            raise PermissionDenied(
                (
                    "У вас нет компании "
                    "для создания расходов."
                )
            )

        serializer.save(company=company)
