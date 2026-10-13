from types import SimpleNamespace
from django.core.exceptions import PermissionDenied
from django.test import SimpleTestCase
from config.router_v2 import V2Router
from config.tenant_context_v2 import tenant_context, current_tenant


def fake_model(label):
    return SimpleNamespace(_meta=SimpleNamespace(app_label=label))


class V2RouterTests(SimpleTestCase):
    def test_central_database(self):
        self.assertEqual(V2Router().db_for_read(fake_model('identity_v2')), 'default')

    def test_tenant_requires_context(self):
        with self.assertRaises(PermissionDenied):
            V2Router().db_for_read(fake_model('operations_v2'))

    def test_context_restored(self):
        with tenant_context('tenant_demo'):
            self.assertEqual(V2Router().db_for_write(fake_model('operations_v2')), 'tenant_demo')
        self.assertIsNone(current_tenant())

    def test_rejects_central_as_tenant(self):
        with self.assertRaises(PermissionDenied):
            with tenant_context('default'):
                pass

    def test_migration_partition(self):
        router = V2Router()
        self.assertTrue(router.allow_migrate('default', 'identity_v2'))
        self.assertFalse(router.allow_migrate('default', 'operations_v2'))
        self.assertTrue(router.allow_migrate('tenant_demo', 'operations_v2'))
