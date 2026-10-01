from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import User
from core.permissions import IsCourseAdmin
from finance.models import Budget
from finance.serializers import BudgetSerializer


class BudgetViewSet(viewsets.ModelViewSet):
    """
    Управление бюджетами компании.
    CRUD + проверка превышения.
    """
    permission_classes = [IsCourseAdmin]
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
