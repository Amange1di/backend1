from django.test import TestCase
from rest_framework.test import APIClient

from core.models import User


class DashboardPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_dashboard_is_available_to_superuser(self):
        superuser = User.objects.create_superuser(
            username="dashboard-superuser",
            password="StrongPass123!",
        )
        self.client.force_authenticate(superuser)

        response = self.client.get("/api/dashboard/")

        self.assertEqual(response.status_code, 200)

    def test_dashboard_is_forbidden_for_company_admin(self):
        course_admin = User.objects.create_user(
            username="dashboard-course-admin",
            password="StrongPass123!",
            role=User.Role.COURSE_ADMIN,
        )
        self.client.force_authenticate(course_admin)

        response = self.client.get("/api/dashboard/")

        self.assertEqual(response.status_code, 403)
