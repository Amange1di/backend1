from django.urls import path

from .views import (
    DashboardView,
    SuperAdminStatsView,
)

urlpatterns = [
    path(
        "dashboard/",
        DashboardView.as_view(),
        name="dashboard",
    ),
    path(
        "super-admin/stats/",
        SuperAdminStatsView.as_view(),
        name="super-admin-stats",
    ),
]
