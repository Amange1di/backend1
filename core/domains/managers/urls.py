from rest_framework.routers import DefaultRouter

from .views import ManagerViewSet

router = DefaultRouter()
router.register(
    "managers",
    ManagerViewSet,
    basename="managers",
)

urlpatterns = router.urls
