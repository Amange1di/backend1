from rest_framework.routers import DefaultRouter

from .views import (
    ExpenseViewSet,
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

urlpatterns = router.urls
