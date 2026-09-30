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

class StudentContractsViewTests(APITestCase):
    """Тесты для StudentContractsView — список договоров в личном кабинете студента."""

    def setUp(self):
        self.admin_user = User.objects.create(
            username="admin_for_student",
            role=User.Role.COURSE_ADMIN,
            password=make_password("admin123", hasher="pbkdf2_sha256"),
        )
        self.company = Company.objects.create(
            name="School For Students", slug="school-students",
            description="test", category="languages", city="Бишкек",
            is_active=True, owner=self.admin_user,
        )
        self.admin_user.company = self.company
        self.admin_user.save(update_fields=["company"])
        self.course = Course.objects.create(title="English", price=5000, duration_weeks=10)
        self.course.admins.add(self.admin_user)
        self.student_user = User.objects.create(
            username="student_main", role=User.Role.STUDENT,
            company=self.company, password=make_password("pass123", hasher="pbkdf2_sha256"),
        )
        self.student = Student.objects.create(
            first_name="Alice", last_name="Brown", phone="555-9999",
            company=self.company, user=self.student_user, can_login=True,
        )
        self.student2_user = User.objects.create(
            username="student_other", role=User.Role.STUDENT,
            company=self.company, password=make_password("pass456", hasher="pbkdf2_sha256"),
        )
        self.student2 = Student.objects.create(
            first_name="Bob", last_name="Green", phone="555-8888",
            company=self.company, user=self.student2_user, can_login=True,
        )
        self.group = Group.objects.create(
            name="Student Group", course=self.course, company=self.company,
            start_date=date(2026, 7, 1), end_date=date(2026, 9, 30),
        )

    def _login_as_student(self, user):
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def _create_contract(self, student, amount=5000):
        return Contract.objects.create(
            company=self.company, student=student, group=self.group,
            amount=amount, start_date=self.group.start_date, end_date=self.group.end_date,
            created_by=self.admin_user, status=Contract.Status.DRAFT,
        )

    def test_student_sees_own_contracts(self):
        self._create_contract(self.student)
        self._login_as_student(self.student_user)
        response = self.client.get("/api/auth/student/contracts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["student_name"], "Alice Brown")
        self.assertEqual(float(response.data[0]["amount"]), 5000)
        self.assertEqual(response.data[0]["status_display"], "Черновик")
        self.assertEqual(response.data[0]["status"], "draft")
        self.assertEqual(response.data[0]["group_name"], "Student Group")

    def test_student_sees_multiple_contracts(self):
        self._create_contract(self.student, amount=5000)
        self._create_contract(self.student, amount=7000)
        self._login_as_student(self.student_user)
        response = self.client.get("/api/auth/student/contracts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        amounts = [float(c["amount"]) for c in response.data]
        self.assertIn(5000, amounts)
        self.assertIn(7000, amounts)

    def test_student_sees_only_own_contracts(self):
        self._create_contract(self.student)
        self._create_contract(self.student2)
        self._login_as_student(self.student_user)
        response = self.client.get("/api/auth/student/contracts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["student_name"], "Alice Brown")

    def test_empty_list_when_no_contracts(self):
        self._login_as_student(self.student_user)
        response = self.client.get("/api/auth/student/contracts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_non_student_gets_forbidden(self):
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.get("/api/auth/student/contracts/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_without_profile_gets_not_found(self):
        orphan_user = User.objects.create(
            username="orphan", role=User.Role.STUDENT,
            password=make_password("orphan123", hasher="pbkdf2_sha256"),
        )
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=orphan_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.get("/api/auth/student/contracts/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_user_gets_forbidden(self):
        self.client.credentials()
        response = self.client.get("/api/auth/student/contracts/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_contract_data_includes_all_fields(self):
        self._create_contract(self.student, amount=9999)
        self._login_as_student(self.student_user)
        response = self.client.get("/api/auth/student/contracts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data[0]
        expected_fields = {
            "id", "company", "company_name", "student", "student_name",
            "group", "group_name", "status", "status_display",
            "contract_number", "amount", "start_date", "end_date",
            "terms", "created_by", "signed_at", "pdf_file",
            "created_at", "updated_at",
        }
        self.assertEqual(set(data.keys()), expected_fields,
                         msg=f"Missing fields: {expected_fields - set(data.keys())}")

    def test_contract_number_is_returned(self):
        self._create_contract(self.student)
        self._login_as_student(self.student_user)
        response = self.client.get("/api/auth/student/contracts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contract_number = response.data[0]["contract_number"]
        self.assertTrue(contract_number.startswith("ДОГ-"))
        self.assertIn(str(date.today().year), contract_number)
