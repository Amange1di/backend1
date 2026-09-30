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
