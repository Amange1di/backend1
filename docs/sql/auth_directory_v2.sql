-- Apply only to a dedicated Auth Directory PostgreSQL database.
-- Not to the central management or any tenant database.
CREATE TABLE IF NOT EXISTS auth_directory_entries (
    identifier_digest CHAR(64) NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    local_user_id VARCHAR(100) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (identifier_digest, tenant_id, local_user_id),
    CONSTRAINT auth_directory_digest_hex CHECK (identifier_digest ~ '^[0-9a-f]{64}$')
);
CREATE INDEX IF NOT EXISTS auth_directory_active_lookup
    ON auth_directory_entries (identifier_digest)
    WHERE active = TRUE;
-- Writes must be performed by a separately authorized provisioning worker.
-- Read-only login service account should have SELECT only.
