"""Compatibility facade for authentication views."""

from .api import (
    CourseAdminCreateView,
    CourseAdminDetailView,
    LoginThrottle,
    LoginView,
    LogoutView,
    MeView,
    RegisterThrottle,
    RegisterView,
    StudentLoginView,
    StudentProfileView,
    StudentSetPasswordView,
)

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
