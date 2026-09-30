from django.urls import path

from .views import (
    CourseAdminCreateView,
    CourseAdminDetailView,
    FirstLoginSetPasswordView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    StudentProfileView,
)

urlpatterns = [
    path(
        "auth/register/",
        RegisterView.as_view(),
        name="auth-register",
    ),
    path(
        "auth/course-admins/",
        CourseAdminCreateView.as_view(),
        name="auth-course-admins",
    ),
    path(
        "auth/course-admins/<int:pk>/",
        CourseAdminDetailView.as_view(),
        name="auth-course-admin-detail",
    ),
    path(
        "auth/login/",
        LoginView.as_view(),
        name="auth-login",
    ),
    path(
        "auth/first-login/set-password/",
        FirstLoginSetPasswordView.as_view(),
        name="auth-first-login-set-password",
    ),
    path(
        "auth/student/profile/",
        StudentProfileView.as_view(),
        name="auth-student-profile",
    ),
    path(
        "auth/me/",
        MeView.as_view(),
        name="auth-me",
    ),
    path(
        "auth/logout/",
        LogoutView.as_view(),
        name="auth-logout",
    ),
]
