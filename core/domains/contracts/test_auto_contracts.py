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
