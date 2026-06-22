from datetime import date
from django.contrib.auth.hashers import make_password
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Company, Course, Student, User, Contract, Group, ContractTemplate


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    ]
)
class LoginViewTests(APITestCase):

    def test_login_succeeds_without_bcrypt_installed(self):
        password = "testpass123"
        user = User.objects.create(
            username="teacher1",
            role=User.Role.TEACHER,
            password=make_password(password, hasher="pbkdf2_sha256"),
        )
        response = self.client.post(
            "/api/auth/login/",
            {"username": user.username, "password": password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["id"], user.id)


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    ]
)
class AutoContractOnGroupCreateTests(APITestCase):
    """Тесты для авто-создания договоров при создании группы со студентами."""

    def setUp(self):
        self.admin_user = User.objects.create(
            username="test_admin",
            role=User.Role.COURSE_ADMIN,
            password=make_password("admin123", hasher="pbkdf2_sha256"),
        )
        self.company = Company.objects.create(
            name="Test School", slug="test-school",
            description="Test school for testing",
            category="languages", city="Бишкек",
            is_active=True, owner=self.admin_user,
        )
        self.admin_user.company = self.company
        self.admin_user.save(update_fields=["company"])
        self.course = Course.objects.create(
            title="English Course", price=5000, duration_weeks=12, lesson_duration_minutes=90,
        )
        self.course.admins.add(self.admin_user)
        self.student1 = Student.objects.create(
            first_name="John", last_name="Doe", phone="555-0101", company=self.company,
        )
        self.student2 = Student.objects.create(
            first_name="Jane", last_name="Smith", phone="555-0102", company=self.company,
        )
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_contracts_created_for_students_on_group_create(self):
        response = self.client.post("/api/groups/", {
            "name": "Test Group A1", "course": self.course.id,
            "schedule_days": "ПН, СР", "schedule_time": "10:00",
            "lessons_per_month": 8, "total_months": 3,
            "student_ids": [self.student1.id, self.student2.id],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, msg=response.data)
        contracts = Contract.objects.filter(group_id=response.data["id"])
        self.assertEqual(contracts.count(), 2)
        for student in [self.student1, self.student2]:
            c = contracts.get(student=student)
            self.assertEqual(c.status, Contract.Status.DRAFT)
            self.assertEqual(c.amount, self.course.price)
            self.assertEqual(c.company, self.company)
            self.assertEqual(c.created_by, self.admin_user)
            self.assertTrue(c.contract_number.startswith("ДОГ-"))

    def test_no_contracts_without_students(self):
        response = self.client.post("/api/groups/", {
            "name": "Empty Group", "course": self.course.id,
            "schedule_days": "ПН, СР", "schedule_time": "10:00",
            "lessons_per_month": 8, "total_months": 3, "student_ids": [],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Contract.objects.filter(group_id=response.data["id"]).count(), 0)

    def test_contract_amount_matches_course_price(self):
        price = 9999.99
        course = Course.objects.create(title="Premium English", price=price, duration_weeks=10)
        course.admins.add(self.admin_user)
        response = self.client.post("/api/groups/", {
            "name": "Premium Group", "course": course.id,
            "schedule_days": "ПН, СР", "schedule_time": "10:00",
            "lessons_per_month": 8, "total_months": 3,
            "student_ids": [self.student1.id],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        contract = Contract.objects.get(group_id=response.data["id"], student=self.student1)
        self.assertEqual(float(contract.amount), price)

    def test_contract_has_correct_dates(self):
        response = self.client.post("/api/groups/", {
            "name": "Dated Group", "course": self.course.id,
            "schedule_days": "ПН, СР", "schedule_time": "10:00",
            "lessons_per_month": 8, "total_months": 3,
            "start_date": "2026-07-01",
            "student_ids": [self.student1.id],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        group = Group.objects.get(id=response.data["id"])
        contract = Contract.objects.get(group_id=response.data["id"], student=self.student1)
        self.assertEqual(contract.start_date, group.start_date)
        self.assertEqual(contract.end_date, group.end_date)

    def test_contracts_created_with_manager(self):
        manager = User.objects.create(
            username="test_manager", role=User.Role.MANAGER,
            company=self.company, created_by=self.admin_user,
            password=make_password("manager123", hasher="pbkdf2_sha256"),
        )
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=manager)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.post("/api/groups/", {
            "name": "Manager Group", "course": self.course.id,
            "schedule_days": "ПН, СР", "schedule_time": "10:00",
            "lessons_per_month": 8, "total_months": 3,
            "student_ids": [self.student1.id],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        contract = Contract.objects.get(group_id=response.data["id"], student=self.student1)
        self.assertEqual(contract.created_by, manager)

    def test_new_group_same_students_creates_new_contracts(self):
        r1 = self.client.post("/api/groups/", {
            "name": "First Group", "course": self.course.id,
            "schedule_days": "ПН, СР", "schedule_time": "10:00",
            "lessons_per_month": 8, "total_months": 3,
            "student_ids": [self.student1.id, self.student2.id],
        }, format="json")
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        r2 = self.client.post("/api/groups/", {
            "name": "Second Group", "course": self.course.id,
            "schedule_days": "ПН, СР", "schedule_time": "10:00",
            "lessons_per_month": 8, "total_months": 3,
            "student_ids": [self.student1.id, self.student2.id],
        }, format="json")
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Contract.objects.filter(group_id=r1.data["id"]).count(), 2)
        self.assertEqual(Contract.objects.filter(group_id=r2.data["id"]).count(), 2)

    def test_no_auto_contract_on_group_update(self):
        r = self.client.post("/api/groups/", {
            "name": "Update Test Group", "course": self.course.id,
            "schedule_days": "ПН, СР", "schedule_time": "10:00",
            "lessons_per_month": 8, "total_months": 3,
            "student_ids": [self.student1.id],
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        gid = r.data["id"]
        before = list(Contract.objects.filter(group_id=gid).values_list("id", flat=True))
        self.assertEqual(len(before), 1)
        r2 = self.client.patch(f"/api/groups/{gid}/", {
            "student_ids": [self.student1.id, self.student2.id],
        }, format="json")
        self.assertEqual(r2.status_code, status.HTTP_200_OK, msg=r2.data)
        after = list(Contract.objects.filter(group_id=gid).values_list("id", flat=True))
        self.assertEqual(after, before)


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


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    ]
)
class ContractTemplateViewSetTests(APITestCase):
    """Тесты для ContractTemplateViewSet — CRUD шаблонов договоров."""

    def setUp(self):
        self.admin_a = User.objects.create(
            username="admin_a", role=User.Role.COURSE_ADMIN,
            password=make_password("pass123", hasher="pbkdf2_sha256"),
        )
        self.company_a = Company.objects.create(
            name="School A", slug="school-a", description="A",
            category="languages", city="Бишкек", is_active=True, owner=self.admin_a,
        )
        self.admin_a.company = self.company_a
        self.admin_a.save(update_fields=["company"])

        self.admin_b = User.objects.create(
            username="admin_b", role=User.Role.COURSE_ADMIN,
            password=make_password("pass456", hasher="pbkdf2_sha256"),
        )
        self.company_b = Company.objects.create(
            name="School B", slug="school-b", description="B",
            category="it", city="Ош", is_active=True, owner=self.admin_b,
        )
        self.admin_b.company = self.company_b
        self.admin_b.save(update_fields=["company"])

        self.manager_a = User.objects.create(
            username="manager_a", role=User.Role.MANAGER,
            company=self.company_a, created_by=self.admin_a,
            password=make_password("mgr123", hasher="pbkdf2_sha256"),
        )
        self.teacher = User.objects.create(
            username="teacher_no_access", role=User.Role.TEACHER,
            company=self.company_a,
            password=make_password("tch123", hasher="pbkdf2_sha256"),
        )
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=self.admin_a)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def _login(self, user):
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_create_template(self):
        response = self.client.post("/api/contract-templates/", {
            "name": "My Template",
            "html_content": "<p>{{ student_name }}</p>",
            "is_default": False,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "My Template")
        self.assertEqual(response.data["html_content"], "<p>{{ student_name }}</p>")
        self.assertFalse(response.data["is_default"])

    def test_create_template_as_default_unsets_others(self):
        self.client.post("/api/contract-templates/", {
            "name": "Template Old", "html_content": "<p>Old</p>", "is_default": False,
        }, format="json")
        response = self.client.post("/api/contract-templates/", {
            "name": "Template Default", "html_content": "<p>New Default</p>", "is_default": True,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_default"])
        defaults = ContractTemplate.objects.filter(company=self.company_a, is_default=True)
        self.assertEqual(defaults.count(), 1)

    def test_create_template_with_company_is_ignored(self):
        response = self.client.post("/api/contract-templates/", {
            "name": "Template", "html_content": "<p>X</p>",
            "company": self.company_b.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["company"], self.company_a.id)

    def test_list_templates(self):
        ContractTemplate.objects.create(company=self.company_a, name="T1", html_content="<p>1</p>")
        ContractTemplate.objects.create(company=self.company_a, name="T2", html_content="<p>2</p>")
        response = self.client.get("/api/contract-templates/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [t["name"] for t in response.data]
        self.assertIn("T1", names)
        self.assertIn("T2", names)
        self.assertEqual(len(response.data), 2)

    def test_list_templates_isolation(self):
        ContractTemplate.objects.create(company=self.company_a, name="T_A", html_content="<p>A</p>")
        ContractTemplate.objects.create(company=self.company_b, name="T_B", html_content="<p>B</p>")
        response = self.client.get("/api/contract-templates/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [t["name"] for t in response.data]
        self.assertIn("T_A", names)
        self.assertNotIn("T_B", names)

    def test_retrieve_template(self):
        tmpl = ContractTemplate.objects.create(
            company=self.company_a, name="Detail", html_content="<p>content</p>",
        )
        response = self.client.get(f"/api/contract-templates/{tmpl.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Detail")

    def test_retrieve_other_company_template_forbidden(self):
        tmpl_b = ContractTemplate.objects.create(
            company=self.company_b, name="Secret", html_content="<p>Secret</p>",
        )
        response = self.client.get(f"/api/contract-templates/{tmpl_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_template(self):
        tmpl = ContractTemplate.objects.create(
            company=self.company_a, name="Old Name", html_content="<p>Old</p>",
        )
        response = self.client.patch(f"/api/contract-templates/{tmpl.id}/", {
            "name": "New Name", "html_content": "<p>New Content</p>",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "New Name")

    def test_update_template_set_default_unsets_others(self):
        t1 = ContractTemplate.objects.create(company=self.company_a, name="First", html_content="<p>1</p>", is_default=True)
        t2 = ContractTemplate.objects.create(company=self.company_a, name="Second", html_content="<p>2</p>", is_default=False)
        response = self.client.patch(f"/api/contract-templates/{t2.id}/", {"is_default": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t1.refresh_from_db()
        self.assertFalse(t1.is_default)

    def test_update_other_company_template_forbidden(self):
        tmpl_b = ContractTemplate.objects.create(company=self.company_b, name="Secret", html_content="<p>Secret</p>")
        response = self.client.patch(f"/api/contract-templates/{tmpl_b.id}/", {"name": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_template(self):
        tmpl = ContractTemplate.objects.create(company=self.company_a, name="Del", html_content="<p>Bye</p>")
        response = self.client.delete(f"/api/contract-templates/{tmpl.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_other_company_template_forbidden(self):
        tmpl_b = ContractTemplate.objects.create(company=self.company_b, name="Secret", html_content="<p>Secret</p>")
        response = self.client.delete(f"/api/contract-templates/{tmpl_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_manager_can_create_template(self):
        self._login(self.manager_a)
        response = self.client.post("/api/contract-templates/", {"name": "Mgr Template", "html_content": "<p>M</p>"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_teacher_cannot_manage_templates(self):
        self._login(self.teacher)
        response = self.client.post("/api/contract-templates/", {"name": "Tch Template", "html_content": "<p>No</p>"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_list_templates(self):
        self.client.credentials()
        response = self.client.get("/api/contract-templates/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


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


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    ]
)
class ContractSignActionTests(APITestCase):
    """Тесты для sign action в ContractViewSet — подписание договора студентом."""

    def setUp(self):
        # Компания и админ
        self.admin_user = User.objects.create(
            username="admin_sign",
            role=User.Role.COURSE_ADMIN,
            password=make_password("admin123", hasher="pbkdf2_sha256"),
        )
        self.company = Company.objects.create(
            name="Sign School", slug="sign",
            description="test", category="languages", city="Бишкек",
            is_active=True, owner=self.admin_user,
        )
        self.admin_user.company = self.company
        self.admin_user.save(update_fields=["company"])

        # Курс
        self.course = Course.objects.create(title="English", price=5000, duration_weeks=10)
        self.course.admins.add(self.admin_user)

        # Группа
        self.group = Group.objects.create(
            name="Sign Group", course=self.course, company=self.company,
            start_date=date(2026, 7, 1), end_date=date(2026, 9, 30),
        )

        # Студент Alice (будет подписывать)
        self.alice_user = User.objects.create(
            username="alice_sign", role=User.Role.STUDENT,
            company=self.company,
            password=make_password("alice123", hasher="pbkdf2_sha256"),
        )
        self.alice = Student.objects.create(
            first_name="Alice", last_name="Signer", phone="555-1001",
            company=self.company, user=self.alice_user, can_login=True,
        )

        # Студент Bob (не будет подписывать, для теста чужого договора)
        self.bob_user = User.objects.create(
            username="bob_sign", role=User.Role.STUDENT,
            company=self.company,
            password=make_password("bob123", hasher="pbkdf2_sha256"),
        )
        self.bob = Student.objects.create(
            first_name="Bob", last_name="Signer", phone="555-1002",
            company=self.company, user=self.bob_user, can_login=True,
        )

    def _login(self, user):
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def _create_contract(self, student, status=Contract.Status.SENT):
        return Contract.objects.create(
            company=self.company,
            student=student,
            group=self.group,
            amount=5000,
            start_date=self.group.start_date,
            end_date=self.group.end_date,
            created_by=self.admin_user,
            status=status,
        )

    def test_student_can_sign_own_sent_contract(self):
        """Студент может подписать свой отправленный договор."""
        contract = self._create_contract(self.alice, status=Contract.Status.SENT)
        self._login(self.alice_user)

        response = self.client.post(f"/api/contracts/{contract.id}/sign/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Contract.Status.SIGNED)
        self.assertEqual(response.data["status_display"], "Подписан")

        contract.refresh_from_db()
        self.assertEqual(contract.status, Contract.Status.SIGNED)
        self.assertIsNotNone(contract.signed_at)

    def test_student_cannot_sign_other_students_contract(self):
        """Студент не может подписать чужой договор (403)."""
        contract = self._create_contract(self.bob, status=Contract.Status.SENT)
        self._login(self.alice_user)

        response = self.client.post(f"/api/contracts/{contract.id}/sign/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_sign_draft_contract(self):
        """Нельзя подписать договор в статусе DRAFT (400)."""
        contract = self._create_contract(self.alice, status=Contract.Status.DRAFT)
        self._login(self.alice_user)

        response = self.client.post(f"/api/contracts/{contract.id}/sign/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Статус не изменился
        contract.refresh_from_db()
        self.assertEqual(contract.status, Contract.Status.DRAFT)

    def test_cannot_sign_already_signed_contract(self):
        """Нельзя подписать уже подписанный договор (400)."""
        contract = self._create_contract(self.alice, status=Contract.Status.SIGNED)
        self._login(self.alice_user)

        response = self.client.post(f"/api/contracts/{contract.id}/sign/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_sign_cancelled_contract(self):
        """Нельзя подписать аннулированный договор (400)."""
        contract = self._create_contract(self.alice, status=Contract.Status.CANCELLED)
        self._login(self.alice_user)

        response = self.client.post(f"/api/contracts/{contract.id}/sign/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_student_cannot_sign(self):
        """Course_admin не может подписать договор (403)."""
        contract = self._create_contract(self.alice, status=Contract.Status.SENT)
        self._login(self.admin_user)

        response = self.client.post(f"/api/contracts/{contract.id}/sign/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_sign(self):
        """Неавторизованный пользователь не может подписать (401)."""
        contract = self._create_contract(self.alice, status=Contract.Status.SENT)
        self.client.credentials()

        response = self.client.post(f"/api/contracts/{contract.id}/sign/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_signed_at_is_set_after_signing(self):
        """После подписания поле signed_at должно быть установлено."""
        contract = self._create_contract(self.alice, status=Contract.Status.SENT)
        self.assertIsNone(contract.signed_at)
        self._login(self.alice_user)

        self.client.post(f"/api/contracts/{contract.id}/sign/")
        contract.refresh_from_db()
        self.assertIsNotNone(contract.signed_at)

    def test_student_without_profile_cannot_sign(self):
        """Студент-пользователь без student_profile не может подписать (403)."""
        orphan = User.objects.create(
            username="orphan_sign", role=User.Role.STUDENT,
            password=make_password("orphan123", hasher="pbkdf2_sha256"),
        )
        # Ситуация: есть User(role=STUDENT), но нет Student(user=this_user)
        contract = self._create_contract(self.alice, status=Contract.Status.SENT)
        self._login(orphan)

        response = self.client.post(f"/api/contracts/{contract.id}/sign/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
