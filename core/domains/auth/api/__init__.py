from .course_admin import CourseAdminCreateView, CourseAdminDetailView, CourseAdminResetPasswordView
from .credentials import (
    FirstLoginSetPasswordView,
    LoginThrottle,
    LoginView,
    LogoutView,
    MeView,
    RegisterThrottle,
    RegisterView,
)
from .student import StudentProfileView

__all__ = [
    "CourseAdminCreateView",
    "CourseAdminDetailView",
    "CourseAdminResetPasswordView",
    "FirstLoginSetPasswordView",
    "LoginThrottle",
    "LoginView",
    "LogoutView",
    "MeView",
    "RegisterThrottle",
    "RegisterView",
    "StudentProfileView",
]
