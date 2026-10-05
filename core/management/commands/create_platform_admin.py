from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import User


class Command(BaseCommand):
    help = "Create one explicitly requested demo platform-admin account without modifying existing data."

    def add_arguments(self, parser):
        parser.add_argument("--allow-production", action="store_true")
        parser.add_argument("--username", default="platform_admin")
        parser.add_argument("--password", default="Platform2026!")

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and not options["allow_production"]:
            raise CommandError(
                "Refusing to create a demo account while DEBUG=False without --allow-production."
            )

        username = options["username"]
        if User.objects.filter(username=username).exists():
            raise CommandError(
                f"Refusing to overwrite existing user {username!r}. No changes were made."
            )

        user = User(
            username=username,
            first_name="Platform",
            last_name="Admin",
            email="platform_admin@demo.local",
            role=User.Role.SUPER_ADMIN,
            is_staff=True,
            is_superuser=True,
            is_active=True,
            must_set_password=False,
        )
        user.set_password(options["password"])
        user.save()

        self.stdout.write(
            self.style.SUCCESS(f"Created platform demo account {user.username!r}.")
        )
