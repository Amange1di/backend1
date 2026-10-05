from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Company, User


class Command(BaseCommand):
    help = "Create one explicitly requested demo course-admin account without modifying existing data."

    def add_arguments(self, parser):
        parser.add_argument("--allow-production", action="store_true")
        parser.add_argument("--username", default="demo_admin")
        parser.add_argument("--password", default="Demo1234!")

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

        company = Company.objects.order_by("pk").first()
        if company is None:
            raise CommandError(
                "Refusing to create a company-admin without an existing company. No changes were made."
            )

        user = User(
            username=username,
            first_name="Demo",
            last_name="Admin",
            email="demo_admin@demo.local",
            role=User.Role.COURSE_ADMIN,
            company=company,
            is_active=True,
            must_set_password=False,
            max_managers=10,
        )
        user.set_password(options["password"])
        user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Created demo account {user.username!r} for existing company {company.pk}."
            )
        )
