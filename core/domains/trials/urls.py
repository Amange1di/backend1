from rest_framework.routers import DefaultRouter

from .views import TrialLeadViewSet

router = DefaultRouter()
router.register(
    "trial-leads",
    TrialLeadViewSet,
    basename="trial-leads",
)

urlpatterns = router.urls
