from .course_admin import CourseAdminCreateView, CourseAdminDetailView, CourseAdminResetPasswordView
from .credentials import (
    FirstLoginLinkView,
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
    "FirstLoginLinkView",
    "FirstLoginSetPasswordView",
    "LoginThrottle",
    "LoginView",
    "LogoutView",
    "MeView",
    "RegisterThrottle",
    "RegisterView",
    "StudentProfileView",
]
