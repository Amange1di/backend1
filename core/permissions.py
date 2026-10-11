from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import User


def can_manage_company(user, company) -> bool:
    """Return whether a user controls the whole company, never another one."""
    if not user.is_authenticated or not company or user.company_id != company.id:
        return False
    if user.role == User.Role.COMPANY_OWNER:
        return True
    return (
        user.role == User.Role.COURSE_ADMIN
        and company.branches.filter(is_active=True).count() <= 1
    )


class IsAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        return request.user.is_authenticated and (
            request.user.role == User.Role.ADMIN or request.user.is_superuser
        )


class IsSuperAdmin(BasePermission):
    """Restrict platform-wide data to Django superusers only."""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user.is_authenticated and request.user.is_superuser
        )


class IsCourseAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        return request.user.is_authenticated and request.user.role in (User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN)


class IsCourseAdminOrManager(BasePermission):
    def has_permission(self, request, view) -> bool:
        return request.user.is_authenticated and request.user.role in (
            User.Role.COMPANY_OWNER,
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        )


class IsCourseAdminOrManagerReadOnly(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not request.user.is_authenticated:
            return False
        if request.user.role in (User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN):
            return True
        if request.user.role == User.Role.MANAGER:
            return request.method in SAFE_METHODS
        return False


class IsCourseAdminOrTeacherReadOnly(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not request.user.is_authenticated:
            return False
        if request.user.role in (User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN):
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
        if request.user.role in (User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN):
            return request.method in SAFE_METHODS
        return False


class IsCourseAdminOrManagerOrStudentReadOnly(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not request.user.is_authenticated:
            return False
        if request.user.role in (User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN, User.Role.MANAGER):
            return True
        if request.user.role in (User.Role.TEACHER, User.Role.STUDENT):
            return request.method in SAFE_METHODS
        return False


class IsCourseAdminOrStudentReadOnly(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not request.user.is_authenticated:
            return False
        if request.user.role in (User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN):
            return True
        if request.user.role == User.Role.STUDENT:
            return request.method in SAFE_METHODS
        return False
