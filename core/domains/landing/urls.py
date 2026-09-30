from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    LandingHeaderLinkViewSet,
    LandingPageViewSet,
    PublicLandingDetailView,
    PublicLandingLeadCreateView,
)

router = DefaultRouter()
router.register(
    "landing-pages",
    LandingPageViewSet,
    basename="landing-pages",
)
router.register(
    "landing-header-links",
    LandingHeaderLinkViewSet,
    basename="landing-header-links",
)

urlpatterns = [
    path(
        "public/landing-pages/<slug:slug>/",
        PublicLandingDetailView.as_view(),
        name="public-landing-detail",
    ),
    path(
        "public/landing-pages/<slug:slug>/lead/",
        PublicLandingLeadCreateView.as_view(),
        name="public-landing-lead",
    ),
    *router.urls,
]
