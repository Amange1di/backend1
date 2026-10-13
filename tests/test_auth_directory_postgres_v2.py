"""DB-API adapter unit tests with fake connection; no external database."""
import unittest

from tenancy_v2.auth_directory_postgres import PostgresDirectoryStore


class Cursor:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params):
        self.calls.append((sql, params))

    def fetchall(self):
        return [("tenant_37", "125")]

    def close(self):
        pass


class Connection:
    def __init__(self):
        self.cur = Cursor()
        self.closed = False

    def cursor(self):
        return self.cur

    def close(self):
        self.closed = True


class DirectoryPostgresTests(unittest.TestCase):
    def test_lookup_is_parameterized_and_closes_connection(self):
        conn = Connection()
        result = PostgresDirectoryStore(lambda: conn).lookup("a" * 64)
        self.assertEqual(result[0].tenant_id, "tenant_37")
        self.assertEqual(result[0].local_user_id, "125")
        self.assertEqual(conn.cur.calls[1][1], ("a" * 64,))
        self.assertTrue(conn.closed)

    def test_timeout_bounds(self):
        with self.assertRaises(ValueError):
            PostgresDirectoryStore(Connection, timeout_ms=0)
