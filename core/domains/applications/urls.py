from django.urls import path

from .views import (
    MarketplaceApplicationDetailView,
    MarketplaceApplicationsView,
    StudentApplicationCreateView,
    TeacherApplicationCreateView,
    PlatformApplicationCreateView,
    SuperAdminPlatformApplicationsView,
    SuperAdminPlatformApplicationDetailView,
)

urlpatterns = [
    path("platform-applications/", PlatformApplicationCreateView.as_view(), name="platform-application-create"),
    path("super-admin/applications/", SuperAdminPlatformApplicationsView.as_view(), name="super-admin-platform-applications"),
    path("super-admin/applications/<int:pk>/", SuperAdminPlatformApplicationDetailView.as_view(), name="super-admin-platform-application-detail"),
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
