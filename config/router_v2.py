"""Database router for new v2 apps only; legacy apps are untouched."""
from django.core.exceptions import PermissionDenied
from .tenant_context_v2 import current_tenant


class V2Router:
    central_apps = {'identity_v2', 'tenancy_v2', 'catalog_v2'}
    tenant_apps = {'operations_v2'}

    def db_for_read(self, model, **hints):
        return self._db(model)

    def db_for_write(self, model, **hints):
        return self._db(model)

    def _db(self, model):
        label = model._meta.app_label
        if label in self.central_apps:
            return 'default'
        if label in self.tenant_apps:
            alias = current_tenant()
            if not alias:
                raise PermissionDenied('Tenant context required')
            return alias
        return None

    def allow_relation(self, obj1, obj2, **hints):
        labels = {obj1._meta.app_label, obj2._meta.app_label}
        if labels & (self.central_apps | self.tenant_apps):
            return bool(obj1._state.db and obj1._state.db == obj2._state.db)
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.central_apps:
            return db == 'default'
        if app_label in self.tenant_apps:
            return db.startswith('tenant_')
        return None
