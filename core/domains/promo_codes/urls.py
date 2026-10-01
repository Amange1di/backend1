from rest_framework.routers import DefaultRouter

from .views import PromoCodeViewSet

router = DefaultRouter()
router.register(
    "admin/promo-codes",
    PromoCodeViewSet,
    basename="admin-promo-codes",
)

urlpatterns = router.urls
