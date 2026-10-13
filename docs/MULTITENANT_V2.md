# EduOsh API v2 — isolated multi-database foundation

## Status
Scaffold only. No tenant-aware ORM routing or migrated tenant models yet.
Do not use this as a production multi-tenant implementation.

## Isolation
- Existing Vercel project and `main` branch remain unchanged.
- Use `develop-v2` for new code and a **different** Vercel project.
- Never copy production `DATABASE_URL`, `SECRET_KEY`, tokens or personal data.
- Create two separate PostgreSQL databases with least-privilege credentials.
- Configure `DJANGO_SETTINGS_MODULE=config.settings_v2`.
- Set `EDUOSH_V2_ISOLATED=true`.
- Set `EDUOSH_V2_CENTRAL_DATABASE_URL` and `EDUOSH_V2_DEMO_DATABASE_URL`.
- The legacy `config.settings` still requires `DATABASE_URL` during import; for v2 it must be a **non-production** central database URL. Set `DATABASE_URL` to the same isolated central DB as `EDUOSH_V2_CENTRAL_DATABASE_URL`.
- Do not run `migrate` on tenant databases until app ownership and cross-database foreign keys are resolved.

## Planned boundaries
Central: User/authentication, Company, Membership, public Marketplace,
public courses/jobs/landing, subscription, tenant registry.
Tenant: Student, Group, Schedule, Attendance, Payment, Homework,
Library, operational staff/branches.

Existing `core` models mix these concerns and contain relationships across
the proposed boundary. Django does not support cross-database ForeignKeys.
Next: inventory relations, extract central identities, add tenant-specific
models, design tenant context derived from authenticated membership, and
implement explicit routing with deny-by-default tests.

## Acceptance gates
1. Isolated environment cannot connect to production.
2. User enters login and password only; company membership is resolved server-side.
3. Cross-tenant access returns 403/404 and never leaks data.
4. Public catalogue uses approved projections in central DB.
5. Migrations, background jobs, file access and backup/restore are tenant-aware.
6. Web and Flutter integration tests pass before any migration of real data.
