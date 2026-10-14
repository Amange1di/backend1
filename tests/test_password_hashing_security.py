from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password, identify_hasher
from django.test import SimpleTestCase, override_settings

from django.conf import settings


class PasswordHashingTests(SimpleTestCase):
    def test_new_passwords_use_argon2(self):
        encoded = make_password("Test-only-secret-123!")
        self.assertEqual(identify_hasher(encoded).algorithm, "argon2")
        self.assertTrue(check_password("Test-only-secret-123!", encoded))
        self.assertFalse(check_password("incorrect", encoded))

    def test_legacy_pbkdf2_hash_still_verifies(self):
        with override_settings(PASSWORD_HASHERS=[
            "django.contrib.auth.hashers.PBKDF2PasswordHasher"
        ]):
            encoded = make_password("Test-only-secret-123!")
        self.assertTrue(check_password("Test-only-secret-123!", encoded))

    def test_password_field_is_write_only(self):
        from core.domains.users.serialization.auth import LoginSerializer
        self.assertTrue(LoginSerializer().fields["password"].write_only)
