"""Directory lookup contract; no central-user or tenant authentication dependency.

Deploy backing storage separately from the management database. This module
intentionally does not choose a tenant when an identifier has multiple matches.
"""
from dataclasses import dataclass
from typing import Protocol

from .auth_directory_keys import identifier_digest


@dataclass(frozen=True)
class DirectoryEntry:
    tenant_id: str
    local_user_id: str


class DirectoryUnavailable(RuntimeError):
    pass


class DirectoryStore(Protocol):
    def lookup(self, digest: str) -> list[DirectoryEntry]: ...


class AuthDirectory:
    def __init__(self, store: DirectoryStore, hmac_key: bytes, max_candidates: int = 8):
        if max_candidates < 1:
            raise ValueError("max_candidates must be positive")
        self.store = store
        self.hmac_key = hmac_key
        self.max_candidates = max_candidates

    def candidates(self, identifier: str) -> tuple[DirectoryEntry, ...]:
        digest = identifier_digest(identifier, self.hmac_key)
        try:
            entries = self.store.lookup(digest)
        except Exception as exc:
            raise DirectoryUnavailable("Auth directory is unavailable") from exc
        if len(entries) > self.max_candidates:
            raise DirectoryUnavailable("Too many candidate accounts; additional verification required")
        # Stable de-duplication; never pick the first entry as an authenticated user.
        unique = {(e.tenant_id, e.local_user_id): e for e in entries}
        return tuple(unique[key] for key in sorted(unique))
