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
