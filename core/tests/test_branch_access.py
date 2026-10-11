from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Branch, Company, User


class BranchAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_single_branch_course_admin_can_list_company_branch_without_membership(self):
        admin = User.objects.create_user(
            username="single-branch-admin", role=User.Role.COURSE_ADMIN
        )
        company = Company.objects.create(
            name="Single branch", owner=admin, description="test", category="other", city="Онлайн"
        )
        admin.company = company
        admin.save(update_fields=["company"])
        branch = Branch.objects.create(company=company, name="Main", is_main=True)

        self.client.force_authenticate(admin)
        response = self.client.get("/api/branches/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [branch.id])

    def test_multi_branch_course_admin_only_lists_assigned_branch(self):
        owner = User.objects.create_user(username="multi-owner", role=User.Role.COMPANY_OWNER)
        company = Company.objects.create(
            name="Multi branch", owner=owner, description="test", category="other", city="Онлайн", branch_limit=2
        )
        owner.company = company
        owner.save(update_fields=["company"])
        first = Branch.objects.create(company=company, name="First", is_main=True)
        Branch.objects.create(company=company, name="Second")
        admin = User.objects.create_user(username="multi-admin", role=User.Role.COURSE_ADMIN, company=company)
        admin.branches.add(first)

        self.client.force_authenticate(admin)
        response = self.client.get("/api/branches/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [first.id])
