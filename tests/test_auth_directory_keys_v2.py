"""Isolated tests for Auth Directory lookup-key preparation."""
import unittest

from tenancy_v2.auth_directory_keys import identifier_digest, normalize_identifier


class DirectoryKeysTests(unittest.TestCase):
    def test_email_normalization(self):
        self.assertEqual(normalize_identifier("  USER@Example.COM "), "email:user@example.com")

    def test_phone_normalization(self):
        self.assertEqual(normalize_identifier("+996 (700) 123-456"), "phone:+996700123456")

    def test_digest_deterministic_and_keyed(self):
        secret = b"a" * 32
        digest = identifier_digest("+996700123456", secret)
        self.assertEqual(digest, identifier_digest("+996 (700) 123-456", secret))
        self.assertNotEqual(digest, identifier_digest("+996700123456", b"b" * 32))
        self.assertNotIn("996700123456", digest)

    def test_invalid_input(self):
        for value in ("", "0700123456", "bad@", "+123", "hello"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_identifier(value)

    def test_short_secret_rejected(self):
        with self.assertRaises(ValueError):
            identifier_digest("a@example.com", b"short")
