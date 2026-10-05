"""Safely import the legacy fixture into a brand-new database once."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.management.data_safety import critical_counts, existing_application_records


class Command(BaseCommand):
    help = (
        "Import crm_data.json only into an empty application database. "
        "Never overwrites or deletes existing records."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fixture",
            default=str(settings.BASE_DIR / "crm_data.json"),
            help="Absolute or project-relative JSON fixture path (default: crm_data.json).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate the fixture and target database without importing.",
        )

    def handle(self, *args, **options):
        fixture_path = Path(options["fixture"]).expanduser().resolve()
        if not fixture_path.is_file():
            raise CommandError(f"Fixture does not exist: {fixture_path}")

        existing = existing_application_records()
        if existing:
            detail = ", ".join(f"{label}={count}" for label, count in sorted(existing.items()))
            self.stdout.write(self.style.WARNING(f"SKIPPED: target database is not empty ({detail})."))
            raise CommandError(
                "Refusing fixture import: it could overwrite real data. "
                "Use a backup/restore or an explicitly reviewed data migration instead."
            )

        try:
            fixture_data = json.loads(fixture_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Invalid JSON fixture: {exc}") from exc
        if not isinstance(fixture_data, list) or not fixture_data:
            raise CommandError("Fixture must be a non-empty Django JSON fixture list.")

        labels = Counter(item.get("model", "<missing>") for item in fixture_data if isinstance(item, dict))
        digest = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
        self.stdout.write(f"Fixture: {fixture_path} ({len(fixture_data)} records, sha256={digest})")
        self.stdout.write("Models: " + ", ".join(f"{label}={count}" for label, count in sorted(labels.items())))
        self.stdout.write("Target before import: " + json.dumps(critical_counts(), sort_keys=True))

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS("Dry run passed; no data was written."))
            return

        try:
            with transaction.atomic():
                call_command("loaddata", str(fixture_path), verbosity=options["verbosity"])
        except Exception as exc:
            raise CommandError(f"Import failed; transaction rolled back: {exc}") from exc

        after = critical_counts()
        self.stdout.write(self.style.SUCCESS("Imported fixture into an empty target database."))
        self.stdout.write("Target after import: " + json.dumps(after, sort_keys=True))
