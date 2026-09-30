import random
import time

_pending_verifications: dict = {}


def _generate_code() -> str:
    """Generate a 6-digit verification code."""
    return f"{random.randint(0, 999999):06d}"


def _clean_expired_codes():
    """Remove expired verification codes (older than 5 minutes)."""
    now = time.time()
    expired = [
        key
        for key, value in _pending_verifications.items()
        if value["expires_at"] <= now
    ]
    for key in expired:
        del _pending_verifications[key]
