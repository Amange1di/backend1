from django.urls import path

from .views import (
    MarketplaceApplicationDetailView,
    MarketplaceApplicationsView,
    StudentApplicationCreateView,
    TeacherApplicationCreateView,
)

urlpatterns = [
    path(
        "marketplace/teacher-applications/",
        TeacherApplicationCreateView.as_view(),
        name="marketplace-teacher-application-create",
    ),
    path(
        "marketplace/student-applications/",
        StudentApplicationCreateView.as_view(),
        name="marketplace-student-application-create",
    ),
    path(
        "marketplace/applications/",
        MarketplaceApplicationsView.as_view(),
        name="marketplace-applications",
    ),
    path(
        "marketplace/applications/<int:pk>/",
        MarketplaceApplicationDetailView.as_view(),
        name="marketplace-application-detail",
    ),
]
