from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ExpenseViewSet,
    FinanceDashboardView,
    FinanceExportView,
    GroupMonthViewSet,
)

router = DefaultRouter()
router.register(
    "group-months",
    GroupMonthViewSet,
    basename="group-months",
)
router.register(
    "expenses",
    ExpenseViewSet,
    basename="expenses",
)

urlpatterns = [
    path(
        "finance/dashboard/",
        FinanceDashboardView.as_view(),
        name="finance-dashboard",
    ),
    path(
        "finance/export/<str:export_format>/",
        FinanceExportView.as_view(),
        name="finance-export",
    ),
    *router.urls,
]
