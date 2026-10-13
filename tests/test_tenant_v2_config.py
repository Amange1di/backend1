import unittest

from django.core.exceptions import ImproperlyConfigured

from config.tenant_v2 import build_v2_databases


class TenantV2ConfigTests(unittest.TestCase):
    def test_two_distinct_databases(self):
        result = build_v2_databases({
            "EDUOSH_V2_CENTRAL_DATABASE_URL": "postgresql://u:p@db.example/central",
            "EDUOSH_V2_DEMO_DATABASE_URL": "postgresql://u:p@db.example/company",
        })
        self.assertEqual(result["default"]["NAME"], "central")
        self.assertEqual(result["tenant_demo"]["NAME"], "company")

    def test_rejects_missing_url(self):
        with self.assertRaises(ImproperlyConfigured):
            build_v2_databases({})

    def test_rejects_same_database(self):
        with self.assertRaises(ImproperlyConfigured):
            build_v2_databases({
                "EDUOSH_V2_CENTRAL_DATABASE_URL": "postgresql://u:p@db.example/central",
                "EDUOSH_V2_DEMO_DATABASE_URL": "postgresql://u:p@db.example/central",
            })

    def test_rejects_sqlite(self):
        with self.assertRaises(ImproperlyConfigured):
            build_v2_databases({
                "EDUOSH_V2_CENTRAL_DATABASE_URL": "sqlite:///local.db",
                "EDUOSH_V2_DEMO_DATABASE_URL": "postgresql://u:p@db.example/demo",
            })
