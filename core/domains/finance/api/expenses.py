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

        if user.role in (User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN):
            if user.company:
                qs = Expense.objects.filter(company=user.company)
                selected = self.request.COOKIES.get("eduosh_branch")
                if selected and selected.isdigit():
                    branch_id = int(selected)
                    if user.role != User.Role.COMPANY_OWNER and not user.branches.filter(id=branch_id, is_active=True).exists():
                        raise PermissionDenied("branch_access_denied")
                    return qs.filter(branch_id=branch_id)
                if user.role != User.Role.COMPANY_OWNER:
                    return qs.filter(branch__in=user.branches.filter(is_active=True))
                return qs

        if user.role == User.Role.MANAGER:
            if user.company:
                allowed = user.branches.filter(is_active=True)
                selected = self.request.COOKIES.get("eduosh_branch")
                if selected and selected.isdigit():
                    branch_id = int(selected)
                    if not allowed.filter(id=branch_id).exists():
                        raise PermissionDenied("branch_access_denied")
                    return Expense.objects.filter(
                        company=user.company,
                        branch_id=branch_id,
                    ).exclude(category="salary")
                return Expense.objects.filter(
                    company=user.company,
                    branch__in=allowed,
                ).exclude(category="salary")

        return Expense.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        company = user.company
        if not company:
            raise PermissionDenied(
                (
                    "company_required_for_expense"
                )
            )

        if (
            user.role == User.Role.MANAGER
            and serializer.validated_data.get("category") == "salary"
        ):
            raise PermissionDenied(
                "manager_salary_expense_create_forbidden"
            )

        branch = serializer.validated_data.get("branch")
        selected = self.request.COOKIES.get("eduosh_branch")
        allowed = company.branches.filter(is_active=True)
        if user.role != User.Role.COMPANY_OWNER:
            allowed = allowed.filter(users=user)
        if not branch and selected and selected.isdigit():
            branch = allowed.filter(id=int(selected)).first()
        if not branch and allowed.count() == 1:
            branch = allowed.first()
        if not branch or not allowed.filter(id=branch.id).exists():
            raise PermissionDenied("branch_access_denied")
        serializer.save(company=company, branch=branch)

    def perform_update(self, serializer):
        user = self.request.user
        category = serializer.validated_data.get(
            "category",
            serializer.instance.category,
        )
        if user.role == User.Role.MANAGER and category == "salary":
            raise PermissionDenied(
                "manager_salary_expense_update_forbidden"
            )
        serializer.save()
