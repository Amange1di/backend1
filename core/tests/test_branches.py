from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Branch, Company, User


class BranchTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner-branch-test",
            password="StrongPass123!",
            role=User.Role.COMPANY_OWNER,
        )
        self.company = Company.objects.create(
            name="Branch Test Company",
            owner=self.owner,
            description="test",
            category="other",
            city="Онлайн",
            branch_limit=2,
        )
        self.owner.company = self.company
        self.owner.save(update_fields=["company"])
        self.main = Branch.objects.create(
            company=self.company,
            name="Main",
            is_main=True,
        )
        self.owner.branches.add(self.main)
        self.client = APIClient()
        self.client.force_authenticate(self.owner)

    def test_branch_limit_is_enforced_on_server(self):
        Branch.objects.create(company=self.company, name="Second")
        with self.assertRaises(ValidationError):
            Branch.objects.create(company=self.company, name="Third")

    def test_owner_can_create_branch(self):
        response = self.client.post(
            "/api/branches/",
            {"name": "Second", "address": "Osh"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Second")

    def test_main_branch_cannot_be_archived(self):
        response = self.client.post(f"/api/branches/{self.main.id}/archive/")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "cannot_archive_main_branch")

    def test_other_company_branch_is_not_visible(self):
        other_owner = User.objects.create_user(username="other-owner", role=User.Role.COMPANY_OWNER)
        other = Company.objects.create(
            name="Other Company",
            owner=other_owner,
            description="test",
            category="other",
            city="Онлайн",
        )
        Branch.objects.create(company=other, name="Other Main", is_main=True)
        response = self.client.get("/api/branches/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual({item["id"] for item in response.data}, {self.main.id})

    def test_non_owner_cannot_update_branch(self):
        admin = User.objects.create_user(
            username="course-admin-branch-test",
            password="StrongPass123!",
            role=User.Role.COURSE_ADMIN,
        )
        admin.company = self.company
        admin.save(update_fields=["company"])
        admin.branches.add(self.main)
        self.client.force_authenticate(admin)
        response = self.client.patch(
            f"/api/branches/{self.main.id}/",
            {"name": "Unauthorized"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.main.refresh_from_db()
        self.assertEqual(self.main.name, "Main")

    def test_owner_cannot_hard_delete_branch(self):
        response = self.client.delete(f"/api/branches/{self.main.id}/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Branch.objects.filter(pk=self.main.pk).exists())

    def test_owner_cannot_disable_main_branch_via_patch(self):
        response = self.client.patch(
            f"/api/branches/{self.main.id}/",
            {"is_active": False, "is_main": False},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.main.refresh_from_db()
        self.assertTrue(self.main.is_active)
        self.assertTrue(self.main.is_main)

    def test_owner_cannot_create_second_main_branch(self):
        response = self.client.post(
            "/api/branches/",
            {"name": "Second", "is_main": True},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        created = Branch.objects.get(pk=response.data["id"])
        self.assertFalse(created.is_main)
