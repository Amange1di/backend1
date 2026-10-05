"""Compatibility facade for authentication views."""

from .api import (
    CourseAdminCreateView,
    CourseAdminDetailView,
    CourseAdminResetPasswordView,
    FirstLoginLinkView,
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
