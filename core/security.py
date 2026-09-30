from pathlib import Path

import bleach
from rest_framework import serializers


SAFE_RICH_TEXT_TAGS = [
    "a", "b", "br", "em", "i", "li", "ol", "p", "strong", "ul",
]
SAFE_RICH_TEXT_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
}
SAFE_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_rich_text(value: str) -> str:
    return bleach.clean(
        value,
        tags=SAFE_RICH_TEXT_TAGS,
        attributes=SAFE_RICH_TEXT_ATTRIBUTES,
        protocols=SAFE_PROTOCOLS,
        strip=True,
    )


def sanitize_json_content(value):
    if isinstance(value, str):
        return sanitize_rich_text(value)
    if isinstance(value, list):
        return [sanitize_json_content(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): sanitize_json_content(item)
            for key, item in value.items()
        }
    return value


def validate_upload(value, *, max_bytes: int, allowed_extensions: set[str]):
    if not value:
        return value

    size = getattr(value, "size", 0) or 0
    if size > max_bytes:
        raise serializers.ValidationError(
            f"File is too large. Maximum size is {max_bytes // (1024 * 1024)} MB."
        )

    suffix = Path(getattr(value, "name", "")).suffix.lower().lstrip(".")
    if suffix not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise serializers.ValidationError(
            f"Unsupported file type. Allowed: {allowed}."
        )
    return value
