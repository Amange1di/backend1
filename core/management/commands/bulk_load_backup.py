"""Fast alias for copying the local EduOsh SQLite database into PostgreSQL."""

from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = (
        "Bulk-copy the local SQLite database into the configured PostgreSQL "
        "database. This is a convenience wrapper around migrate_local_sqlite."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "source",
            nargs="?",
            default="db.sqlite3",
            help=(
                "SQLite source path. Defaults to ./db.sqlite3. "
                "For compatibility, backup_data.json is accepted and maps "
                "to ./db.sqlite3 when that file exists."
            ),
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Rows per bulk insert batch (default: 1000).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Inspect source/target counts without writing.",
        )

    def handle(self, *args, **options):
        source_arg = options["source"]
        source = Path(source_arg).expanduser()

        # The user may already have created backup_data.json with dumpdata.
        # The purpose-built SQLite migrator is substantially faster and safer
        # for this project, so transparently use the original SQLite database.
        if source.suffix.lower() == ".json":
            sqlite_source = Path(settings.BASE_DIR) / "db.sqlite3"
            if not sqlite_source.is_file():
                raise CommandError(
                    "backup JSON was supplied, but db.sqlite3 was not found. "
                    "Pass the SQLite database path explicitly."
                )
            self.stdout.write(
                self.style.WARNING(
                    f"Using {sqlite_source} instead of {source_arg}: "
                    "direct SQLite -> PostgreSQL bulk copy is faster."
                )
            )
            source = sqlite_source

        source = source.resolve()
        if not source.is_file():
            raise CommandError(f"SQLite source does not exist: {source}")

        kwargs = {
            "source": str(source),
            "batch_size": options["batch_size"],
        }
        if not options["dry_run"]:
            kwargs["apply"] = True

        call_command("migrate_local_sqlite", **kwargs)
