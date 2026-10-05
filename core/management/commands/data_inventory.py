"""Write or print a read-only pre/post migration data inventory."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.management.data_safety import critical_counts


class Command(BaseCommand):
    help = "Print critical EduOsh record counts; optionally save them as JSON."

    def add_arguments(self, parser):
        parser.add_argument("--output", help="Path to a JSON inventory file.")

    def handle(self, *args, **options):
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "counts": critical_counts(),
        }
        rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        output = options.get("output")
        if output:
            path = Path(output)
            if path.exists():
                raise CommandError(f"Refusing to overwrite existing inventory: {path}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered + "\n", encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Inventory saved: {path}"))
        self.stdout.write(rendered)
