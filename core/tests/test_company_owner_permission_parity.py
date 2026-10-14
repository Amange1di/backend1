from types import SimpleNamespace

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from core.models import User
from core.permissions import (
    IsCourseAdmin,
    IsCourseAdminOrManager,
    IsCourseAdminOrManagerReadOnly,
    IsCourseAdminOrTeacherReadOnly,
    IsTeacherOrCourseAdminReadOnly,
    IsCourseAdminOrManagerOrStudentReadOnly,
    IsCourseAdminOrStudentReadOnly,
)


class CompanyOwnerPermissionParityTests(SimpleTestCase):
    """Owners retain exactly the course-admin access on shared endpoints."""

    permission_classes = (
        IsCourseAdmin,
        IsCourseAdminOrManager,
        IsCourseAdminOrManagerReadOnly,
        IsCourseAdminOrTeacherReadOnly,
        IsTeacherOrCourseAdminReadOnly,
        IsCourseAdminOrManagerOrStudentReadOnly,
        IsCourseAdminOrStudentReadOnly,
    )

    def test_owner_matches_course_admin_for_read_and_write_methods(self):
        factory = APIRequestFactory()
        for permission_class in self.permission_classes:
            for method in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                with self.subTest(permission=permission_class.__name__, method=method):
                    request = factory.generic(method, "/api/test/")
                    permission = permission_class()
                    admin_request = SimpleNamespace(
                        method=request.method,
                        user=SimpleNamespace(is_authenticated=True, role=User.Role.COURSE_ADMIN),
                    )
                    owner_request = SimpleNamespace(
                        method=request.method,
                        user=SimpleNamespace(is_authenticated=True, role=User.Role.COMPANY_OWNER),
                    )
                    self.assertEqual(
                        permission.has_permission(owner_request, None),
                        permission.has_permission(admin_request, None),
                    )
