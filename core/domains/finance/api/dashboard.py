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
from core.permissions import IsCourseAdmin

from ..serializers import (
    ExpenseSerializer,
    GroupMonthSerializer,
)

logger = logging.getLogger(__name__)

class FinanceDashboardView(APIView):
    """
    Дашборд финансовой сводки.
    GET /api/finance/dashboard/
    """
    permission_classes = [IsCourseAdmin]

    def get(self, request):
        from django.db.models import Sum
        
        from calendar import monthrange

        user = request.user
        if user.role not in (User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN):
            return Response({'detail': 'access_denied'}, status=403)
        company = user.company

        if not company:
            return Response({'detail': 'company_not_found'}, status=404)

        now = timezone.now().date()
        first_of_month = date(now.year, now.month, 1)
        end_of_month = date(now.year, now.month, monthrange(now.year, now.month)[1])
        start_of_year = date(now.year, 1, 1)
        selected_branch = request.COOKIES.get("eduosh_branch")
        branch_id = int(selected_branch) if selected_branch and selected_branch.isdigit() else None
        allowed_branch_ids = None
        if user.role == User.Role.COURSE_ADMIN:
            allowed_branch_ids = list(user.branches.filter(is_active=True).values_list("id", flat=True))
            if branch_id and branch_id not in allowed_branch_ids:
                raise PermissionDenied("branch_access_denied")

        monthly_income_qs = Payment.objects.filter(
            company=company, status='paid',
            paid_at__gte=first_of_month, paid_at__lte=end_of_month
        )
        if branch_id:
            monthly_income_qs = monthly_income_qs.filter(branch_id=branch_id)
        elif allowed_branch_ids is not None:
            monthly_income_qs = monthly_income_qs.filter(branch_id__in=allowed_branch_ids)
        monthly_income = monthly_income_qs.aggregate(total=Sum('amount'))['total'] or 0

        monthly_expenses_qs = Expense.objects.filter(
            company=company,
            date__gte=first_of_month, date__lte=end_of_month
        )
        if branch_id:
            monthly_expenses_qs = monthly_expenses_qs.filter(branch_id=branch_id)
        elif allowed_branch_ids is not None:
            monthly_expenses_qs = monthly_expenses_qs.filter(branch_id__in=allowed_branch_ids)
        monthly_expenses = monthly_expenses_qs.aggregate(total=Sum('amount'))['total'] or 0

        monthly_total_expenses = float(monthly_expenses)

        yearly_income_qs = Payment.objects.filter(
            company=company, status='paid',
            paid_at__gte=start_of_year, paid_at__lte=end_of_month
        )
        if branch_id:
            yearly_income_qs = yearly_income_qs.filter(branch_id=branch_id)
        elif allowed_branch_ids is not None:
            yearly_income_qs = yearly_income_qs.filter(branch_id__in=allowed_branch_ids)
        yearly_income = yearly_income_qs.aggregate(total=Sum('amount'))['total'] or 0

        yearly_expenses_qs = Expense.objects.filter(
            company=company,
            date__gte=start_of_year, date__lte=end_of_month
        )
        if branch_id:
            yearly_expenses_qs = yearly_expenses_qs.filter(branch_id=branch_id)
        elif allowed_branch_ids is not None:
            yearly_expenses_qs = yearly_expenses_qs.filter(branch_id__in=allowed_branch_ids)
        yearly_expenses = yearly_expenses_qs.aggregate(total=Sum('amount'))['total'] or 0

        yearly_total_expenses = float(yearly_expenses)

        total_debt_qs = Payment.objects.filter(company=company, status='debt')
        if branch_id:
            total_debt_qs = total_debt_qs.filter(branch_id=branch_id)
        elif allowed_branch_ids is not None:
            total_debt_qs = total_debt_qs.filter(branch_id__in=allowed_branch_ids)
        total_debt = total_debt_qs.aggregate(total=Sum('amount'))['total'] or 0

        students_qs = Student.objects.filter(company=company)
        if branch_id:
            students_qs = students_qs.filter(groups__branch_id=branch_id).distinct()
        elif allowed_branch_ids is not None:
            students_qs = students_qs.filter(groups__branch_id__in=allowed_branch_ids).distinct()
        students_count = students_qs.count()

        from finance.models import Budget
        active_budgets_count = Budget.objects.filter(company=company, is_active=True).count()

        return Response({
            'monthly': {
                'income': float(monthly_income),
                'expenses': monthly_total_expenses,
                'net': float(monthly_income) - monthly_total_expenses,
            },
            'yearly': {
                'income': float(yearly_income),
                'expenses': yearly_total_expenses,
                'net': float(yearly_income) - yearly_total_expenses,
            },
            'total_debt': float(total_debt),
            'students_count': students_count,
            'active_budgets': active_budgets_count,
        })
