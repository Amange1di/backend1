"""Auth Directory lookup contract tests; no Django DB required."""
import unittest

from tenancy_v2.auth_directory import (
    AuthDirectory, DirectoryEntry, DirectoryUnavailable,
)


class Store:
    def __init__(self, entries=(), fail=False):
        self.entries = list(entries)
        self.fail = fail
        self.lookups = 0

    def lookup(self, digest):
        self.lookups += 1
        if self.fail:
            raise ConnectionError("offline")
        return self.entries


class AuthDirectoryTests(unittest.TestCase):
    def test_single_index_lookup(self):
        store = Store([DirectoryEntry("tenant_37", "125")])
        entries = AuthDirectory(store, b"x" * 32).candidates("+996700123456")
        self.assertEqual(entries, (DirectoryEntry("tenant_37", "125"),))
        self.assertEqual(store.lookups, 1)

    def test_multiple_tenants_are_not_silently_selected(self):
        store = Store([DirectoryEntry("tenant_37", "125"), DirectoryEntry("tenant_12", "5")])
        entries = AuthDirectory(store, b"x" * 32).candidates("+996700123456")
        self.assertEqual(len(entries), 2)

    def test_fail_closed(self):
        with self.assertRaises(DirectoryUnavailable):
            AuthDirectory(Store(fail=True), b"x" * 32).candidates("+996700123456")

    def test_candidate_cap(self):
        store = Store([DirectoryEntry(str(i), str(i)) for i in range(9)])
        with self.assertRaises(DirectoryUnavailable):
            AuthDirectory(store, b"x" * 32).candidates("+996700123456")

    def test_duplicate_entry(self):
        item = DirectoryEntry("tenant_37", "125")
        self.assertEqual(AuthDirectory(Store([item, item]), b"x" * 32).candidates("+996700123456"), (item,))
