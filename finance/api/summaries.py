from calendar import monthrange
from datetime import date

from django.db.models import Sum
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Expense, Payment, User
from core.permissions import IsCourseAdminOrManager
from finance.models import MonthlySummary, SalaryRecord
from finance.serializers import MonthlySummarySerializer


class MonthlySummaryViewSet(viewsets.ModelViewSet):
    """
    Ежемесячные сводки.
    CRUD + генерация + дашборд.
    """
    permission_classes = [IsCourseAdminOrManager]
    serializer_class = MonthlySummarySerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.COURSE_ADMIN:
            return MonthlySummary.objects.filter(company__owner=user).distinct()
        if user.role == User.Role.MANAGER:
            return MonthlySummary.objects.filter(company=user.company) if user.company else MonthlySummary.objects.none()
        return MonthlySummary.objects.none()

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Генерация сводки за месяц.
        POST /finance/summaries/generate/
        {"year": 2026, "month": 1}
        """
        user = request.user
        if user.role == User.Role.COURSE_ADMIN:
            company = user.company
        elif user.role == User.Role.MANAGER:
            company = user.company
        else:
            return Response({'detail': 'Нет доступа'}, status=403)

        if not company:
            return Response({'detail': 'Компания не найдена'}, status=404)

        year = request.data.get('year', timezone.now().year)
        month = request.data.get('month', timezone.now().month)

        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])

        income = (
            Payment.objects.filter(
                company=company, status='paid',
                paid_at__gte=first_day, paid_at__lte=last_day
            ).aggregate(total=Sum('amount'))['total'] or 0
        )
        regular_expenses = (
            Expense.objects.filter(
                company=company,
                date__gte=first_day, date__lte=last_day
            ).aggregate(total=Sum('amount'))['total'] or 0
        )
        salaries = (
            SalaryRecord.objects.filter(
                company=company,
                status=SalaryRecord.Status.PAID,
                paid_at__gte=first_day,
                paid_at__lte=last_day,
            ).aggregate(
                total=Sum("base_salary") + Sum("percent_amount") + Sum("bonus_amount")
            )["total"] or 0
        )
        total_expenses = float(regular_expenses)

        students = Payment.objects.filter(
            company=company, paid_at__gte=first_day, paid_at__lte=last_day
        ).values('student').distinct().count()
        groups = Payment.objects.filter(
            company=company, paid_at__gte=first_day, paid_at__lte=last_day
        ).values('group').distinct().count()

        net_profit = float(income) - float(total_expenses)

        summary, created = MonthlySummary.objects.update_or_create(
            company=company, year=year, month=month,
            defaults={
                'total_income': income,
                'total_expenses': total_expenses,
                'total_salaries': salaries,
                'net_profit': net_profit,
                'total_students': students,
                'total_groups': groups,
            }
        )

        return Response({
            'message': 'Создана' if created else 'Обновлена',
            'summary': MonthlySummarySerializer(summary).data,
        })

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Дашборд сводок.
        GET /finance/summaries/dashboard/
        """
        user = request.user
        if user.role == User.Role.COURSE_ADMIN:
            company = user.company
        elif user.role == User.Role.MANAGER:
            company = user.company
        else:
            return Response({'detail': 'Нет доступа'}, status=403)

        if not company:
            return Response({'detail': 'Компания не найдена'}, status=404)

        summaries = MonthlySummary.objects.filter(company=company).order_by('-year', '-month')[:12]
        data = MonthlySummarySerializer(summaries, many=True).data

        totals = summaries.aggregate(
            total_income=Sum("total_income"),
            total_expenses=Sum("total_expenses"),
            total_salaries=Sum("total_salaries"),
            total_profit=Sum("net_profit"),
        )

        total_income = totals["total_income"] or 0
        total_expenses = totals["total_expenses"] or 0
        total_salaries = totals["total_salaries"] or 0
        total_profit = totals["total_profit"] or 0

        return Response({
            'monthly_summaries': data,
            'summary': {
                'total_income': float(total_income),
                'total_expenses': float(total_expenses),
                'total_salaries': float(total_salaries),
                'total_profit': float(total_profit),
                'avg_profit_margin': (
                    round((float(total_profit) / float(total_income)) * 100, 2)
                    if total_income
                    else 0
                ),
            }
        })
