from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AttendanceMarkView,
    AttendanceViewSet,
    AuditoriumViewSet,
    CourseViewSet,
    DashboardView,
    CourseAdminCreateView,
    CourseAdminDetailView,
    GroupViewSet,
    LoginView,
    ManagerViewSet,
    MeView,
    PaymentViewSet,
    RegisterView,
    StudentViewSet,
    TaskViewSet,
    TeacherViewSet,
    TrialLeadViewSet,
)

router = DefaultRouter()
router.register("courses", CourseViewSet)
router.register("teachers", TeacherViewSet)
router.register("managers", ManagerViewSet, basename="managers")
router.register("students", StudentViewSet)
router.register("groups", GroupViewSet)
router.register("auditoriums", AuditoriumViewSet)
router.register("attendance", AttendanceViewSet)
router.register("payments", PaymentViewSet)
router.register("trial-leads", TrialLeadViewSet, basename="trial-leads")
router.register("tasks", TaskViewSet, basename="tasks")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/course-admins/", CourseAdminCreateView.as_view(), name="auth-course-admins"),
    path("auth/course-admins/<int:pk>/", CourseAdminDetailView.as_view(), name="auth-course-admin-detail"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("attendance/mark/", AttendanceMarkView.as_view(), name="attendance-mark"),
    path("", include(router.urls)),
]
