"""Compatibility facade for finance API views."""

from .api import BudgetViewSet, ForecastViewSet, MonthlySummaryViewSet, SalaryRecordViewSet

__all__ = ["BudgetViewSet", "ForecastViewSet", "MonthlySummaryViewSet", "SalaryRecordViewSet"]
