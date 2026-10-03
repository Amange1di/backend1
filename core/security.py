from pathlib import Path
import io
import zipfile

import bleach
from rest_framework import serializers


SAFE_RICH_TEXT_TAGS = [
    "a", "b", "br", "em", "i", "li", "ol", "p", "strong", "ul",
]
SAFE_CONTRACT_TAGS = [
    "b", "br", "div", "em", "h1", "h2", "h3", "h4", "h5", "h6",
    "i", "li", "ol", "p", "span", "strong", "table", "tbody", "td",
    "th", "thead", "tr", "ul",
]
SAFE_RICH_TEXT_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
}
SAFE_PROTOCOLS = ["http", "https", "mailto"]

DANGEROUS_UPLOAD_EXTENSIONS = {
    "apk", "app", "bat", "bin", "cmd", "com", "cpl", "dll", "dmg",
    "exe", "hta", "html", "htm", "jar", "js", "jsx", "mjs", "msi",
    "php", "pl", "ps1", "py", "rb", "scr", "sh", "svg", "ts", "tsx",
    "vbs", "wasm",
}

MIME_BY_EXTENSION = {
    "pdf": {"application/pdf"},
    "png": {"image/png"},
    "jpg": {"image/jpeg"},
    "jpeg": {"image/jpeg"},
    "webp": {"image/webp"},
    "zip": {
        "application/zip",
        "application/x-zip-compressed",
        "multipart/x-zip",
    },
    "doc": {"application/msword", "application/x-ole-storage"},
    "xls": {"application/vnd.ms-excel", "application/x-ole-storage"},
    "ppt": {"application/vnd.ms-powerpoint", "application/x-ole-storage"},
    "docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
    },
    "xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
    },
    "pptx": {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/zip",
    },
    "txt": {"text/plain"},
}

ZIP_EXTENSIONS = {"zip", "docx", "xlsx", "pptx"}
OLE_EXTENSIONS = {"doc", "xls", "ppt"}

MAX_ARCHIVE_ENTRIES = 5000
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 250 * 1024 * 1024


def sanitize_rich_text(value: str) -> str:
    return bleach.clean(
        value,
        tags=SAFE_RICH_TEXT_TAGS,
        attributes=SAFE_RICH_TEXT_ATTRIBUTES,
        protocols=SAFE_PROTOCOLS,
        strip=True,
    )


def sanitize_contract_html(value: str) -> str:
    return bleach.clean(
        value,
        tags=SAFE_CONTRACT_TAGS,
        attributes={},
        protocols=[],
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


def _reset_upload(value) -> None:
    try:
        value.seek(0)
    except (AttributeError, OSError, ValueError):
        file_obj = getattr(value, "file", None)
        if file_obj is not None:
            try:
                file_obj.seek(0)
            except (AttributeError, OSError, ValueError):
                pass


def _read_prefix(value, size: int = 32) -> bytes:
    _reset_upload(value)
    try:
        prefix = value.read(size)
    except (AttributeError, OSError, ValueError):
        file_obj = getattr(value, "file", None)
        if file_obj is None:
            return b""
        prefix = file_obj.read(size)
    finally:
        _reset_upload(value)

    return prefix if isinstance(prefix, bytes) else bytes(prefix or b"")


def _has_pdf_signature(prefix: bytes) -> bool:
    return prefix.startswith(b"%PDF-")


def _has_png_signature(prefix: bytes) -> bool:
    return prefix.startswith(b"\x89PNG\r\n\x1a\n")


def _has_jpeg_signature(prefix: bytes) -> bool:
    return prefix.startswith(b"\xff\xd8\xff")


def _has_webp_signature(prefix: bytes) -> bool:
    return (
        len(prefix) >= 12
        and prefix[:4] == b"RIFF"
        and prefix[8:12] == b"WEBP"
    )


def _has_ole_signature(prefix: bytes) -> bool:
    return prefix.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")


def _zip_file(value):
    _reset_upload(value)
    file_obj = getattr(value, "file", None) or value
    return zipfile.ZipFile(file_obj)


def _validate_zip_structure(value, suffix: str) -> None:
    try:
        with _zip_file(value) as archive:
            infos = archive.infolist()

            if len(infos) > MAX_ARCHIVE_ENTRIES:
                raise serializers.ValidationError(
                    "upload_archive_too_many_entries"
                )

            total_uncompressed = sum(
                max(0, info.file_size)
                for info in infos
            )
            if total_uncompressed > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
                raise serializers.ValidationError(
                    "upload_archive_too_large"
                )

            names = {info.filename for info in infos}
            lowered = {name.lower() for name in names}

            if suffix == "docx":
                valid = (
                    "[content_types].xml" in lowered
                    and any(name.startswith("word/") for name in lowered)
                )
            elif suffix == "xlsx":
                valid = (
                    "[content_types].xml" in lowered
                    and any(name.startswith("xl/") for name in lowered)
                )
            elif suffix == "pptx":
                valid = (
                    "[content_types].xml" in lowered
                    and any(name.startswith("ppt/") for name in lowered)
                )
            else:
                valid = True

            if not valid:
                raise serializers.ValidationError(
                    "upload_content_mismatch"
                )
    except serializers.ValidationError:
        raise
    except (zipfile.BadZipFile, OSError, ValueError, RuntimeError):
        raise serializers.ValidationError(
            "upload_archive_invalid"
        )
    finally:
        _reset_upload(value)


def _validate_content_signature(value, suffix: str) -> None:
    prefix = _read_prefix(value)

    validators = {
        "pdf": _has_pdf_signature,
        "png": _has_png_signature,
        "jpg": _has_jpeg_signature,
        "jpeg": _has_jpeg_signature,
        "webp": _has_webp_signature,
    }

    validator = validators.get(suffix)
    if validator and not validator(prefix):
        raise serializers.ValidationError(
            "upload_content_mismatch"
        )

    if suffix in OLE_EXTENSIONS and not _has_ole_signature(prefix):
        raise serializers.ValidationError(
            "upload_content_mismatch"
        )

    if suffix in ZIP_EXTENSIONS:
        if not prefix.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
            raise serializers.ValidationError(
                "upload_content_mismatch"
            )
        _validate_zip_structure(value, suffix)


def _validate_reported_mime(value, suffix: str) -> None:
    content_type = (
        getattr(value, "content_type", None)
        or ""
    ).split(";", 1)[0].strip().lower()

    if not content_type or content_type == "application/octet-stream":
        return

    allowed = MIME_BY_EXTENSION.get(suffix)
    if allowed and content_type not in allowed:
        raise serializers.ValidationError(
            "upload_mime_mismatch"
        )


def validate_upload(value, *, max_bytes: int, allowed_extensions: set[str]):
    if not value:
        return value

    size = getattr(value, "size", 0) or 0
    if size <= 0:
        raise serializers.ValidationError(
            "upload_empty_file"
        )

    if size > max_bytes:
        raise serializers.ValidationError(
            f"File is too large. Maximum size is {max_bytes // (1024 * 1024)} MB."
        )

    raw_name = str(getattr(value, "name", "") or "")
    if not raw_name or "\x00" in raw_name:
        raise serializers.ValidationError(
            "upload_filename_invalid"
        )

    suffix = Path(raw_name).suffix.lower().lstrip(".")

    if suffix in DANGEROUS_UPLOAD_EXTENSIONS:
        raise serializers.ValidationError(
            "upload_type_blocked"
        )

    if suffix not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise serializers.ValidationError(
            f"Unsupported file type. Allowed: {allowed}."
        )

    _validate_reported_mime(value, suffix)
    _validate_content_signature(value, suffix)
    _reset_upload(value)

    return value
