from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from core.models import (
    AuditLog,
    Branch,
    Company,
    CompanyCategory,
    CompanyCity,
    Group,
    Payment,
    Student,
    User,
)


class DataSafetyTests(APITestCase):
    def setUp(self):
        self.admin_a = User.objects.create_user(
            username="admin_a",
            password="StrongPass!A2026",
            role=User.Role.COURSE_ADMIN,
        )
        self.admin_b = User.objects.create_user(
            username="admin_b",
            password="StrongPass!B2026",
            role=User.Role.COURSE_ADMIN,
        )

        self.company_a = Company.objects.create(
            name="Company A",
            description="A",
            category=CompanyCategory.OTHER,
            city=CompanyCity.ONLINE,
            owner=self.admin_a,
        )
        self.company_b = Company.objects.create(
            name="Company B",
            description="B",
            category=CompanyCategory.OTHER,
            city=CompanyCity.ONLINE,
            owner=self.admin_b,
        )

        self.admin_a.company = self.company_a
        self.admin_a.save(update_fields=["company"])
        self.admin_b.company = self.company_b
        self.admin_b.save(update_fields=["company"])
        self.branch_a = Branch.objects.create(company=self.company_a, name="Main A", is_main=True)
        self.branch_b = Branch.objects.create(company=self.company_b, name="Main B", is_main=True)
        self.admin_a.branches.add(self.branch_a)
        self.admin_b.branches.add(self.branch_b)

        self.student_a = Student.objects.create(
            first_name="Student A",
            phone="1001",
            company=self.company_a,
        )
        self.student_b = Student.objects.create(
            first_name="Student B",
            phone="2001",
            company=self.company_b,
        )
        group = Group.objects.create(name="Branch A Group", company=self.company_a, branch=self.branch_a)
        group.students.add(self.student_a)

    def test_course_admin_cannot_read_other_company_student(self):
        self.client.force_authenticate(
            user=self.admin_a
        )

        response = self.client.get(
            f"/api/students/{self.student_b.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_student_delete_archives_instead_of_deleting(self):
        self.client.force_authenticate(
            user=self.admin_a
        )

        response = self.client.delete(
            f"/api/students/{self.student_a.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.student_a.refresh_from_db()
        self.assertIsNotNone(
            self.student_a.archived_at
        )
        self.assertFalse(
            self.student_a.can_login
        )
        self.assertTrue(
            Student.objects.filter(
                id=self.student_a.id
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action="student.archived",
                object_id=str(self.student_a.id),
            ).exists()
        )

    def test_group_delete_archives_instead_of_deleting(self):
        group = Group.objects.create(
            name="Archive Group",
            company=self.company_a,
        )
        self.client.force_authenticate(
            user=self.admin_a
        )

        response = self.client.delete(
            f"/api/groups/{group.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        group.refresh_from_db()
        self.assertIsNotNone(group.archived_at)
        self.assertTrue(
            Group.objects.filter(id=group.id).exists()
        )

    def test_payment_delete_archives_instead_of_deleting(self):
        payment = Payment.objects.create(
            student=self.student_a,
            company=self.company_a,
            branch=self.branch_a,
            amount=Decimal("1000.00"),
            status=Payment.Status.PAID,
        )
        self.client.force_authenticate(
            user=self.admin_a
        )

        response = self.client.delete(
            f"/api/payments/{payment.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        payment.refresh_from_db()
        self.assertIsNotNone(payment.archived_at)
        self.assertTrue(
            Payment.objects.filter(
                id=payment.id
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action="payment.archived",
                object_id=str(payment.id),
            ).exists()
        )
