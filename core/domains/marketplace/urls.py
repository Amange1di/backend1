from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    MarketplaceCompanyViewSet,
    MarketplaceCourseViewSet,
    MarketplaceJobViewSet,
    MyCoursesView,
    MyJobsView,
    PublicCourseViewSet,
    PublicJobViewSet,
)

router = DefaultRouter()
router.register(
    "marketplace/companies",
    MarketplaceCompanyViewSet,
    basename="marketplace-companies",
)
router.register(
    "marketplace/courses",
    MarketplaceCourseViewSet,
    basename="marketplace-courses",
)
router.register(
    "marketplace/jobs",
    MarketplaceJobViewSet,
    basename="marketplace-jobs",
)
router.register(
    "public/courses",
    PublicCourseViewSet,
    basename="public-courses",
)
router.register(
    "public/jobs",
    PublicJobViewSet,
    basename="public-jobs",
)

urlpatterns = [
    path(
        "marketplace/my-courses/",
        MyCoursesView.as_view(),
        name="marketplace-my-courses",
    ),
    path(
        "marketplace/my-jobs/",
        MyJobsView.as_view(),
        name="marketplace-my-jobs",
    ),
    *router.urls,
]
