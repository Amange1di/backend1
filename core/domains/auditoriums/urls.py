from rest_framework.routers import DefaultRouter

from .views import AuditoriumViewSet

router = DefaultRouter()
router.register(
    "auditoriums",
    AuditoriumViewSet,
    basename="auditoriums",
)

urlpatterns = router.urls
