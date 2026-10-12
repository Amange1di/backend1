"""Fail a deployment before it serves code incompatible with the database."""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder


class Command(BaseCommand):
    help = (
        "Verify database columns required by applied EduOsh migrations without "
        "modifying the database."
    )

    def handle(self, *args, **options):
        migration = ("core", "0058_multi_branch")
        applied = set(MigrationRecorder.Migration.objects.values_list("app", "name"))
        if migration not in applied:
            raise CommandError(
                "core.0058_multi_branch is not applied. Run the reviewed migration "
                "procedure before deploying code that relies on multi-branch fields."
            )

        with connection.cursor() as cursor:
            columns = {
                column.name
                for column in connection.introspection.get_table_description(
                    cursor, "core_company"
                )
            }

        if "branch_limit" not in columns:
            raise CommandError(
                "Schema drift detected: core.0058_multi_branch is recorded as applied, "
                "but core_company.branch_limit is missing. Stop deployment; restore or "
                "repair the schema through the reviewed migration procedure."
            )

        self.stdout.write(self.style.SUCCESS("Schema contract verified."))
