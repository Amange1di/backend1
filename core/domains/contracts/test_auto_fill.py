from datetime import date

from django.contrib.auth.hashers import make_password
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Company, Contract, ContractTemplate, Course, Group, Student, User


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    ]
)

class ContractAutoFillTests(APITestCase):
    """Тесты для auto_fill action в ContractViewSet."""

    AUTO_FILL_URL = "/api/contracts/auto-fill/"

    def setUp(self):
        self.admin_user = User.objects.create(
            username="admin_autofill",
            role=User.Role.COURSE_ADMIN,
            password=make_password("admin123", hasher="pbkdf2_sha256"),
        )
        self.company = Company.objects.create(
            name="AutoFill School", slug="autofill",
            description="test", category="languages", city="Бишкек",
            is_active=True, owner=self.admin_user,
        )
        self.admin_user.company = self.company
        self.admin_user.save(update_fields=["company"])

        self.other_admin = User.objects.create(
            username="other_admin", role=User.Role.COURSE_ADMIN,
            password=make_password("other123", hasher="pbkdf2_sha256"),
        )
        self.other_company = Company.objects.create(
            name="Other School", slug="other",
            description="other", category="it", city="Ош",
            is_active=True, owner=self.other_admin,
        )
        self.other_admin.company = self.other_company
        self.other_admin.save(update_fields=["company"])

        self.course = Course.objects.create(title="English", price=10000, duration_weeks=12)
        self.course.admins.add(self.admin_user)

        self.student = Student.objects.create(first_name="Auto", last_name="Fill", phone="555-0001", company=self.company)
        self.other_student = Student.objects.create(first_name="Other", last_name="Student", phone="555-0002", company=self.other_company)

        self.group = Group.objects.create(
            name="AutoFill Group", course=self.course, company=self.company,
            schedule_days="ПН, СР", schedule_time="10:00",
            start_date=date(2026, 8, 1), end_date=date(2026, 10, 31),
        )

        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_get_auto_fill_returns_prefilled_data(self):
        response = self.client.get(f"{self.AUTO_FILL_URL}?student_id={self.student.id}&group_id={self.group.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["student_name"], "Auto Fill")
        self.assertEqual(float(response.data["amount"]), 10000)
        self.assertEqual(response.data["start_date"], "2026-08-01")
        self.assertEqual(response.data["end_date"], "2026-10-31")

    def test_get_auto_fill_missing_params_returns_400(self):
        response = self.client.get(self.AUTO_FILL_URL)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_auto_fill_invalid_student_returns_403(self):
        response = self.client.get(f"{self.AUTO_FILL_URL}?student_id=99999&group_id={self.group.id}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_auto_fill_other_company_student_returns_403(self):
        response = self.client.get(f"{self.AUTO_FILL_URL}?student_id={self.other_student.id}&group_id={self.group.id}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_auto_fill_no_course_group_returns_defaults(self):
        g2 = Group.objects.create(name="No Course", company=self.company, start_date=date(2026, 8, 1))
        response = self.client.get(f"{self.AUTO_FILL_URL}?student_id={self.student.id}&group_id={g2.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data["amount"]), 0)
        self.assertEqual(response.data["course_name"], "—")
