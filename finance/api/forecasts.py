from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Expense, GroupMonth, Payment, User
from core.permissions import IsCourseAdmin
from finance.models import Forecast
from finance.serializers import ForecastSerializer


class ForecastViewSet(viewsets.ModelViewSet):
    """
    Прогнозирование доходов/расходов.
    CRUD + автоматический прогноз.
    """
    permission_classes = [IsCourseAdmin]
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

        if user.role != User.Role.COURSE_ADMIN:
            return Response({'detail': 'Нет доступа'}, status=403)
        company = user.company

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
