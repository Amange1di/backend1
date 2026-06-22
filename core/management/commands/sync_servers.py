"""
Management команда для двусторонней синхронизации БД между серверами.

Каждый сервер может:
1. Отправить свои данные на другой сервер (push)
2. Получить данные с другого сервера (pull)

Использование:
    python manage.py sync_servers --remote=https://backend1-1-vmlx.onrender.com/api
    python manage.py sync_servers --remote=http://162.62.231.244/api --pull-only
    python manage.py sync_servers --remote=https://other-server.com/api --push-only

Настройка (в .env или Render env vars на ОБОИХ серверах):
    SYNC_SECRET=<общий секрет, одинаковый на обоих серверах>
    SYNC_TOKEN=<токен супер-админа на удалённом сервере>

Cron (каждые 2 дня на обоих серверах, в разное время):
    Render:  0 3 */2 * * cd /path/to/backend1 && python3 manage.py sync_servers --remote=http://162.62.231.244/api
    VPS:     0 5 */2 * * cd /path/to/backend1 && python3 manage.py sync_servers --remote=https://backend1-1-vmlx.onrender.com/api

ВАЖНО: Для production рекомендуется использовать единую PostgreSQL базу данных
вместо синхронизации. Обратитесь к README для инструкции.
"""

import json
import logging
import urllib.request
import urllib.error

from django.conf import settings
from django.core import serializers
from django.db import transaction
from django.core.management.base import BaseCommand, CommandError

from core.sync_views import _get_sync_objects, _save_or_update

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync data with another server (bidirectional)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--remote",
            required=True,
            help="Remote server URL (e.g. https://other-server.com/api)",
        )
        parser.add_argument(
            "--push-only",
            action="store_true",
            dest="push_only",
            default=False,
            help="Only push local data to remote (skip pull)",
        )
        parser.add_argument(
            "--pull-only",
            action="store_true",
            dest="pull_only",
            default=False,
            help="Only pull remote data to local (skip push)",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=120,
            help="HTTP timeout in seconds (default: 120)",
        )

    def handle(self, *args, **options):
        remote_url = options["remote"].rstrip("/")
        push_only = options["push_only"]
        pull_only = options["pull_only"]
        timeout = options["timeout"]

        do_push = not pull_only
        do_pull = not push_only

        sync_secret = getattr(settings, "SYNC_SECRET", None) or ""
        if not sync_secret:
            raise CommandError(
                "SYNC_SECRET is not configured. "
                "Set it in your .env or Render env vars."
            )

        sync_token = getattr(settings, "SYNC_TOKEN", None)
        if not sync_token:
            raise CommandError(
                "SYNC_TOKEN is not configured. "
                "Set it in your .env or Render env vars."
            )

        self.stdout.write(self.style.NOTICE(f"Starting sync with: {remote_url}"))
        self.stdout.write(f"  Push: {'✓' if do_push else '✗'}")
        self.stdout.write(f"  Pull: {'✓' if do_pull else '✗'}")

        errors = []

        if do_push:
            try:
                self._push_to_remote(remote_url, sync_secret, sync_token, timeout)
            except Exception as e:
                errors.append(f"Push: {e}")
                self.stderr.write(self.style.ERROR(f"  ✗ Push failed: {e}"))

        if do_pull:
            try:
                self._pull_from_remote(remote_url, sync_secret, sync_token, timeout)
            except Exception as e:
                errors.append(f"Pull: {e}")
                self.stderr.write(self.style.ERROR(f"  ✗ Pull failed: {e}"))

        if errors:
            raise CommandError(
                f"Sync completed with {len(errors)} error(s): {'; '.join(errors)}"
            )

        self.stdout.write(self.style.SUCCESS("Sync completed successfully!"))

    def _push_to_remote(
        self, remote_url: str, secret: str, token: str, timeout: int
    ):
        """Экспортирует локальные данные и отправляет на удалённый сервер."""
        self.stdout.write("  → Exporting local data...")

        objects = list(_get_sync_objects())
        raw_data = serializers.serialize(
            "json",
            objects,
            indent=2,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
        )
        data = json.loads(raw_data)
        self.stdout.write(f"  → Exported {len(data)} objects")

        self.stdout.write("  → Sending to remote server...")
        import_url = f"{remote_url}/sync/import/"

        req = urllib.request.Request(
            import_url,
            data=raw_data.encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Token {token}",
                "X-Sync-Secret": secret,
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            imported = result.get("imported", 0)
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ Push OK: {imported} objects imported on remote"
                )
            )

    def _pull_from_remote(
        self, remote_url: str, secret: str, token: str, timeout: int
    ):
        """Запрашивает данные с удалённого сервера и загружает локально."""
        self.stdout.write("  → Fetching data from remote server...")

        export_url = f"{remote_url}/sync/export/"
        req = urllib.request.Request(
            export_url,
            headers={
                "Authorization": f"Token {token}",
                "X-Sync-Secret": secret,
            },
            method="GET",
        )

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_data = resp.read().decode("utf-8")

        data = json.loads(raw_data)
        self.stdout.write(f"  → Received {len(data)} objects from remote")

        self.stdout.write("  → Importing data locally...")
        with transaction.atomic():
            objects = serializers.deserialize("json", raw_data)
            count = 0
            for obj in objects:
                _save_or_update(obj)
                count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ Pull OK: {count} objects imported locally"
            )
        )
