"""Compatibility facade for user serializers."""

from .serialization import (
    CourseAdminUpdateSerializer,
    LoginSerializer,
    RegisterSerializer,
    StudentProfileSerializer,
    StudentSetPasswordSerializer,
    TeacherCreateSerializer,
    TeacherUpdateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

__all__ = [
    "CourseAdminUpdateSerializer",
    "LoginSerializer",
    "RegisterSerializer",
    "StudentProfileSerializer",
    "StudentSetPasswordSerializer",
    "TeacherCreateSerializer",
    "TeacherUpdateSerializer",
    "UserSerializer",
    "UserUpdateSerializer",
]
