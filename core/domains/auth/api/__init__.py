from .course_admin import CourseAdminCreateView, CourseAdminDetailView
from .credentials import (
    LoginThrottle,
    LoginView,
    LogoutView,
    MeView,
    RegisterThrottle,
    RegisterView,
)
from .student import StudentLoginView, StudentProfileView, StudentSetPasswordView

__all__ = [
    "CourseAdminCreateView",
    "CourseAdminDetailView",
    "LoginThrottle",
    "LoginView",
    "LogoutView",
    "MeView",
    "RegisterThrottle",
    "RegisterView",
    "StudentLoginView",
    "StudentProfileView",
    "StudentSetPasswordView",
]
