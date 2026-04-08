from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import User


class IsAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        return request.user.is_authenticated and (
            request.user.role == User.Role.ADMIN or request.user.is_superuser
        )


class IsCourseAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        return request.user.is_authenticated and request.user.role == User.Role.COURSE_ADMIN


class IsCourseAdminOrManager(BasePermission):
    def has_permission(self, request, view) -> bool:
        return request.user.is_authenticated and request.user.role in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        )


class IsCourseAdminOrManagerReadOnly(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not request.user.is_authenticated:
            return False
        if request.user.role == User.Role.COURSE_ADMIN:
            return True
        if request.user.role == User.Role.MANAGER:
            return request.method in SAFE_METHODS
        return False


class IsCourseAdminOrTeacherReadOnly(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not request.user.is_authenticated:
            return False
        if request.user.role == User.Role.COURSE_ADMIN:
            return True
        if request.user.role == User.Role.MANAGER:
            return True
        if request.user.role == User.Role.TEACHER:
            return request.method in SAFE_METHODS
        if request.user.role == User.Role.STUDENT:
            return request.method in SAFE_METHODS
        return False


class IsTeacherOrCourseAdminReadOnly(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not request.user.is_authenticated:
            return False
        if request.user.role == User.Role.TEACHER:
            return True
        if request.user.role == User.Role.COURSE_ADMIN:
            return request.method in SAFE_METHODS
        return False


class IsCourseAdminOrManagerOrStudentReadOnly(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not request.user.is_authenticated:
            return False
        if request.user.role in (User.Role.COURSE_ADMIN, User.Role.MANAGER):
            return True
        if request.user.role == User.Role.STUDENT:
            return request.method in SAFE_METHODS
        return False


class IsCourseAdminOrStudentReadOnly(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not request.user.is_authenticated:
            return False
        if request.user.role == User.Role.COURSE_ADMIN:
            return True
        if request.user.role == User.Role.STUDENT:
            return request.method in SAFE_METHODS
        return False
