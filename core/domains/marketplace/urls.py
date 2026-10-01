from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BoostCourseView,
    BoostJobView,
    MarketplaceCompanyViewSet,
    MarketplaceCourseViewSet,
    MarketplaceJobViewSet,
    MyCoursesView,
    MyJobsView,
    PublicCourseViewSet,
    PublicJobViewSet,
    UrgentCourseView,
    UrgentJobView,
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
        "marketplace/boost-course/<int:pk>/",
        BoostCourseView.as_view(),
        name="marketplace-boost-course",
    ),
    path(
        "marketplace/urgent-course/<int:pk>/",
        UrgentCourseView.as_view(),
        name="marketplace-urgent-course",
    ),
    path(
        "marketplace/boost-job/<int:pk>/",
        BoostJobView.as_view(),
        name="marketplace-boost-job",
    ),
    path(
        "marketplace/urgent-job/<int:pk>/",
        UrgentJobView.as_view(),
        name="marketplace-urgent-job",
    ),
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
