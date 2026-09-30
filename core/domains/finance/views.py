"""Compatibility facade for CRM finance views."""

from .api import (
    ExpenseViewSet,
    FinanceDashboardView,
    FinanceExportView,
    GroupMonthViewSet,
)

__all__ = [
    "ExpenseViewSet",
    "FinanceDashboardView",
    "FinanceExportView",
    "GroupMonthViewSet",
]
