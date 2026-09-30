from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AttendanceMarkView,
    AttendanceViewSet,
)

router = DefaultRouter()
router.register(
    "attendance",
    AttendanceViewSet,
    basename="attendance",
)

urlpatterns = [
    path(
        "attendance/mark/",
        AttendanceMarkView.as_view(),
        name="attendance-mark",
    ),
    *router.urls,
]
