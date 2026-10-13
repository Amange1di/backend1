# API v2 migration runbook

**Do not run this against the existing production database.**

## Prerequisites
Create isolated PostgreSQL databases `eduosh_central_v2` and `eduosh_tenant_demo_v2`.
Use credentials with access only to those databases.

Environment:
- `DJANGO_SETTINGS_MODULE=config.settings_v2`
- `EDUOSH_V2_ISOLATED=true`
- `DATABASE_URL` = isolated central DB URL (legacy settings import)
- `EDUOSH_V2_CENTRAL_DATABASE_URL` = isolated central DB URL
- `EDUOSH_V2_DEMO_DATABASE_URL` = isolated demo tenant DB URL
- `SECRET_KEY` = new independent key

Commands (after reviewing migration plan):
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --database=default --plan
python manage.py migrate --database=tenant_demo --plan
python manage.py migrate --database=default
python manage.py migrate operations_v2 --database=tenant_demo
```

The existing core app is central only in this transitional stage.
The tenant database must not receive legacy core/auth models.
Never run an unscoped `migrate` on a tenant database.

## Not yet production ready
Company onboarding and database provisioning, membership API endpoints,
tenant/branch-level authorization, background jobs, public projections,
migration of existing company data, and integration tests are pending.
