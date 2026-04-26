from django.contrib.auth.hashers import make_password
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


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
