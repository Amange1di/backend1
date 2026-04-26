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
    HomeworkSubmissionViewSet,
    HomeworkTaskViewSet,
    LandingHeaderLinkViewSet,
    LandingPageViewSet,
    LoginView,
    ManagerViewSet,
    MeView,
    PaymentViewSet,
    PublicLandingDetailView,
    PublicLandingLeadCreateView,
    RegisterView,
    StudentLoginView,
    StudentProfileView,
    StudentSetPasswordView,
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
router.register("landing-pages", LandingPageViewSet, basename="landing-pages")
router.register("landing-header-links", LandingHeaderLinkViewSet, basename="landing-header-links")
router.register("homework-tasks", HomeworkTaskViewSet, basename="homework-tasks")
router.register("homework-submissions", HomeworkSubmissionViewSet, basename="homework-submissions")
router.register("trial-leads", TrialLeadViewSet, basename="trial-leads")
router.register("tasks", TaskViewSet, basename="tasks")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/course-admins/", CourseAdminCreateView.as_view(), name="auth-course-admins"),
    path("auth/course-admins/<int:pk>/", CourseAdminDetailView.as_view(), name="auth-course-admin-detail"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/student/login/", StudentLoginView.as_view(), name="auth-student-login"),
    path("auth/student/set-password/", StudentSetPasswordView.as_view(), name="auth-student-set-password"),
    path("auth/student/profile/", StudentProfileView.as_view(), name="auth-student-profile"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("attendance/mark/", AttendanceMarkView.as_view(), name="attendance-mark"),
    path("public/landing-pages/<slug:slug>/", PublicLandingDetailView.as_view(), name="public-landing-detail"),
    path("public/landing-pages/<slug:slug>/lead/", PublicLandingLeadCreateView.as_view(), name="public-landing-lead"),
    path("", include(router.urls)),
]
