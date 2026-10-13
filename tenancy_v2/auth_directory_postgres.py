"""Standalone PostgreSQL adapter for AuthDirectory.

Configure a separate HA PostgreSQL service; never reuse the central management
database. Schema must be provisioned by the deployment process (see SQL file).
"""
from contextlib import closing

from .auth_directory import DirectoryEntry


class PostgresDirectoryStore:
    def __init__(self, connect, *, timeout_ms=1500):
        """connect is a zero-argument callable returning a DB-API connection."""
        if not callable(connect):
            raise TypeError("connect must be callable")
        if not 1 <= timeout_ms <= 10000:
            raise ValueError("Invalid statement timeout")
        self._connect = connect
        self._timeout_ms = timeout_ms

    def lookup(self, digest: str) -> list[DirectoryEntry]:
        # All data is bound as parameters, never interpolated into SQL.
        with closing(self._connect()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("SET statement_timeout = %s", (self._timeout_ms,))
                cursor.execute(
                    "SELECT tenant_id, local_user_id FROM auth_directory_entries "
                    "WHERE identifier_digest = %s AND active = TRUE "
                    "ORDER BY tenant_id, local_user_id LIMIT 10",
                    (digest,),
                )
                return [DirectoryEntry(str(tenant), str(user)) for tenant, user in cursor.fetchall()]
