"""Compatibility facade for authentication views."""

from .api import (
    CourseAdminCreateView,
    CourseAdminDetailView,
    CourseAdminResetPasswordView,
    FirstLoginSetPasswordView,
    LoginThrottle,
    LoginView,
    LogoutView,
    MeView,
    RegisterThrottle,
    RegisterView,
    StudentProfileView,
)

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
