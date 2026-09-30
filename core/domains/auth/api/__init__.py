from .course_admin import CourseAdminCreateView, CourseAdminDetailView
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
    "FirstLoginSetPasswordView",
    "LoginThrottle",
    "LoginView",
    "LogoutView",
    "MeView",
    "RegisterThrottle",
    "RegisterView",
    "StudentProfileView",
]
