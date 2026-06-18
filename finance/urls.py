from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BudgetViewSet, ForecastViewSet, MonthlySummaryViewSet

router = DefaultRouter()
router.register('budgets', BudgetViewSet, basename='budgets')
router.register('forecasts', ForecastViewSet, basename='forecasts')
router.register('summaries', MonthlySummaryViewSet, basename='summaries')

urlpatterns = [
    path('', include(router.urls)),
]
