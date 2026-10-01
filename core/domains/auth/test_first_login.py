from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from core.domains.auth.first_login import (
    issue_first_login_password,
)
from core.models import User


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]
)
class FirstLoginFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="first_login_teacher",
            role=User.Role.TEACHER,
            is_active=True,
        )
        self.one_time_password = (
            issue_first_login_password(
                self.user
            )
        )

    def test_login_uses_only_username_and_password(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": self.user.username,
                "password": self.one_time_password,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(
            response.data[
                "requires_password_setup"
            ]
        )
        self.assertIn("token", response.data)

    def test_one_time_password_cannot_be_used_twice(self):
        first = self.client.post(
            "/api/auth/login/",
            {
                "username": self.user.username,
                "password": self.one_time_password,
            },
            format="json",
        )
        self.assertEqual(
            first.status_code,
            status.HTTP_200_OK,
        )

        self.client.credentials()
        second = self.client.post(
            "/api/auth/login/",
            {
                "username": self.user.username,
                "password": self.one_time_password,
            },
            format="json",
        )
        self.assertEqual(
            second.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_first_login_token_is_restricted_until_password_setup(self):
        login = self.client.post(
            "/api/auth/login/",
            {
                "username": self.user.username,
                "password": self.one_time_password,
            },
            format="json",
        )
        token = login.data["token"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        response = self.client.get(
            "/api/managers/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_user_can_set_own_password_after_first_login(self):
        login = self.client.post(
            "/api/auth/login/",
            {
                "username": self.user.username,
                "password": self.one_time_password,
            },
            format="json",
        )
        token = login.data["token"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        response = self.client.post(
            "/api/auth/first-login/set-password/",
            {
                "password": "S3cure-New-Pass!2026",
                "password_confirm": "S3cure-New-Pass!2026",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertFalse(
            response.data[
                "requires_password_setup"
            ]
        )

        self.user.refresh_from_db()
        self.assertFalse(
            self.user.must_set_password
        )
        self.assertTrue(
            self.user.check_password(
                "S3cure-New-Pass!2026"
            )
        )
