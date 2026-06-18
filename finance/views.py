from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from calendar import monthrange
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from core.models import Payment, Expense, GroupMonth, User
from core.permissions import IsCourseAdminOrManager
from .models import Budget, Forecast, MonthlySummary
from .serializers import (
    BudgetSerializer,
    ForecastSerializer,
    MonthlySummarySerializer,
)


class BudgetViewSet(viewsets.ModelViewSet):
    """
    Управление бюджетами компании.
    CRUD + проверка превышения.
    """
    permission_classes = [IsCourseAdminOrManager]
    serializer_class = BudgetSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.COURSE_ADMIN:
            return Budget.objects.filter(company__owner=user).distinct()
        if user.role == User.Role.MANAGER:
            return Budget.objects.filter(company=user.company) if user.company else Budget.objects.none()
        return Budget.objects.none()

    @action(detail=True, methods=['post'])
    def check(self, request, pk=None):
        """Проверить состояние бюджета"""
        budget = self.get_object()
        budget.is_over_budget = budget.check_over_budget()
        return Response({
            'is_over_budget': budget.is_over_budget,
            'spent': float(budget.spent),
            'remaining': float(budget.remaining),
            'utilization_rate': budget.utilization_rate,
        })


class ForecastViewSet(viewsets.ModelViewSet):
    """
    Прогнозирование доходов/расходов.
    CRUD + автоматический прогноз.
    """
    permission_classes = [IsCourseAdminOrManager]
    serializer_class = ForecastSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.COURSE_ADMIN:
            return Forecast.objects.filter(company__owner=user).distinct()
        if user.role == User.Role.MANAGER:
            return Forecast.objects.filter(company=user.company) if user.company else Forecast.objects.none()
        return Forecast.objects.none()

    @action(detail=False, methods=['post'])
    def auto_forecast(self, request):
        """
        Автоматический прогноз на основе исторических данных.
        POST /finance/forecasts/auto_forecast/?months=3
        """
        months_back = int(request.query_params.get('months', 3))
        user = request.user

        if user.role == User.Role.COURSE_ADMIN:
            company = user.company
        elif user.role == User.Role.MANAGER:
            company = user.company
        else:
            return Response({'detail': 'Нет доступа'}, status=403)

        if not company:
            return Response({'detail': 'Компания не найдена'}, status=404)

        # Получаем исторические данные
        end_date = timezone.now().date()
        start_date = end_date - relativedelta(months=months_back)

        # Доходы
        income = Payment.objects.filter(
            company=company, status='paid',
            paid_at__gte=start_date, paid_at__lte=end_date
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Расходы (регулярные + зарплаты преподавателей)
        regular_expenses = Expense.objects.filter(
            company=company,
            date__gte=start_date, date__lte=end_date
        ).aggregate(total=Sum('amount'))['total'] or 0

        salaries = GroupMonth.objects.filter(
            group__company=company, teacher_salary__isnull=False,
            completed_at__gte=start_date, completed_at__lte=end_date
        ).aggregate(total=Sum('teacher_salary'))['total'] or 0

        total_expenses = float(regular_expenses) + float(salaries)

        # Средние
        avg_income = float(income) / months_back
        avg_expense = total_expenses / months_back

        # Создаём прогноз на следующий месяц
        next_month = end_date.month + 1
        next_year = end_date.year
        if next_month > 12:
            next_month = 1
            next_year += 1

        forecasts = {
            'income': avg_income,
            'expense': avg_expense,
            'profit': avg_income - avg_expense,
        }

        for ftype, amount in forecasts.items():
            Forecast.objects.update_or_create(
                company=company,
                forecast_type=ftype,
                period_month=next_month,
                period_year=next_year,
                defaults={
                    'estimated_amount': round(amount, 2),
                    'confidence_level': 70,
                    'notes': f'Автоматический прогноз на {months_back} мес.',
                }
            )

        return Response({
            'forecasts': forecasts,
            'period': f'{next_month}/{next_year}',
        })


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
            GroupMonth.objects.filter(
                group__company=company, teacher_salary__isnull=False,
                completed_at__gte=first_day, completed_at__lte=last_day
            ).aggregate(total=Sum('teacher_salary'))['total'] or 0
        )
        total_expenses = float(regular_expenses) + float(salaries)

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

        total_income = sum(s['total_income'] for s in data)
        total_expenses = sum(s['total_expenses'] for s in data)
        total_salaries = sum(s['total_salaries'] for s in data)
        total_profit = sum(s['net_profit'] for s in data)

        return Response({
            'monthly_summaries': data,
            'summary': {
                'total_income': total_income,
                'total_expenses': total_expenses,
                'total_salaries': total_salaries,
                'total_profit': total_profit,
                'avg_profit_margin': round((total_profit / total_income) * 100, 2) if total_income > 0 else 0,
            }
        })