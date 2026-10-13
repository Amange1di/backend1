# EduOsh v2 — common login with tenant-local users

Design only. Current develop-v2 still uses central core.User and CompanyMembership. Do not deploy without migration and tests.

## Requirements
- Single eduosh.kg/login: email or phone and password, no company selection.
- Tenant PostgreSQL owns users, password hashes, roles, branch access, sessions, CRM data.
- Central management DB holds company registry and billing, not tenant passwords.
- Separate highly available Auth Directory maps HMAC(normalized identifier) to one or more opaque tenant IDs. No raw login identifiers or passwords in directory.
- Directory must have tested failover, backups and durable writes; independently available trusted tenant routing configuration. A shared router or directory remains a potential failure point.
- Never accept DB aliases from client requests. Rate-limit login and use uniform errors.
- When the same identifier exists in multiple companies, route to bounded candidate tenants and verify tenant-local credentials. If multiple valid matches exist, require additional account binding or verification; never select arbitrarily.
- Tenant-bound signed short-lived sessions include tenant ID, local user ID, expiry, audience; enforce local role/branch and revocation state for every request.
- Use an outbox/reconciliation mechanism for identifier updates, user creation, deactivation, deletion and directory consistency.
- Central management DB outage does not prevent new logins only if directory, router, API, tenant DB and secrets remain available.

## Implementation sequence
1. Keep production untouched; implement in isolated feature branch.
2. Introduce tenant-local identity models and auth backend; do not mutate core.User in place.
3. Provision independent Auth Directory, identifier normalization/HMAC and reconciliation.
4. Migrate pilot tenant identity mappings and password hashes safely.
5. Replace central-membership v2 API permissions; adapt frontend and Flutter sessions.
6. Test tenant isolation, duplicate identifiers, failover, revocation, stale directory, concurrency, rollback and backup restoration.
7. Roll out gradually with feature flags and explicit approval.

## Safeguards
TLS, secret manager, least-privilege credentials, connection pooling, auditing, monitoring, rate limits, and documented RPO/RTO. Independent database storage does not eliminate shared API/DNS/router outages.
