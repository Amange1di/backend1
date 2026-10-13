"""Privacy-preserving lookup keys for the future independent Auth Directory.

This module does not perform authentication or choose a tenant.
"""
import hashlib
import hmac
import re


def normalize_identifier(identifier: str) -> str:
    """Normalize email or an international phone number.

    Phone input must include the country code. A dedicated phone-number
    parser should replace this minimal validator before production rollout.
    """
    if not isinstance(identifier, str):
        raise ValueError("Identifier must be text")
    value = identifier.strip()
    if "@" in value:
        value = value.casefold()
        if len(value) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Invalid email")
        return "email:" + value
    digits = re.sub(r"[\s()\-]", "", value)
    if not re.fullmatch(r"\+[1-9]\d{7,14}", digits):
        raise ValueError("Phone must be in international format")
    return "phone:" + digits


def identifier_digest(identifier: str, secret: bytes) -> str:
    """Return a deterministic, non-reversible keyed lookup digest.

    Keep secret outside databases and logs; rotate with a versioned key ID.
    """
    if not isinstance(secret, bytes) or len(secret) < 32:
        raise ValueError("A secret of at least 32 bytes is required")
    normalized = normalize_identifier(identifier)
    return hmac.new(secret, normalized.encode("utf-8"), hashlib.sha256).hexdigest()
