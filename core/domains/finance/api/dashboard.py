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
        if user.role != User.Role.COURSE_ADMIN:
            return Response({'detail': 'Нет доступа'}, status=403)
        company = user.company

        if not company:
            return Response({'detail': 'Компания не найдена'}, status=404)

        now = timezone.now().date()
        first_of_month = date(now.year, now.month, 1)
        end_of_month = date(now.year, now.month, monthrange(now.year, now.month)[1])
        start_of_year = date(now.year, 1, 1)

        monthly_income = Payment.objects.filter(
            company=company, status='paid',
            paid_at__gte=first_of_month, paid_at__lte=end_of_month
        ).aggregate(total=Sum('amount'))['total'] or 0

        monthly_expenses = Expense.objects.filter(
            company=company,
            date__gte=first_of_month, date__lte=end_of_month
        ).aggregate(total=Sum('amount'))['total'] or 0

        monthly_total_expenses = float(monthly_expenses)

        yearly_income = Payment.objects.filter(
            company=company, status='paid',
            paid_at__gte=start_of_year, paid_at__lte=end_of_month
        ).aggregate(total=Sum('amount'))['total'] or 0

        yearly_expenses = Expense.objects.filter(
            company=company,
            date__gte=start_of_year, date__lte=end_of_month
        ).aggregate(total=Sum('amount'))['total'] or 0

        yearly_total_expenses = float(yearly_expenses)

        total_debt = Payment.objects.filter(
            company=company, status='debt'
        ).aggregate(total=Sum('amount'))['total'] or 0

        students_count = Student.objects.filter(company=company).count()

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
