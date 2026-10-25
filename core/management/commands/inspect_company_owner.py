"""Inspect a company owner without exposing credentials or passwords."""

from django.core.management.base import BaseCommand, CommandError

from core.models import Company


class Command(BaseCommand):
    help = (
        "Read-only company/owner lookup for production diagnostics. "
        "It never prints passwords, tokens, phone numbers, or emails."
    )

    def add_arguments(self, parser):
        parser.add_argument("--company", required=True, help="Exact company name")

    def handle(self, *args, **options):
        name = options["company"].strip()
        if not name:
            raise CommandError("--company must not be blank")

        companies = list(
            Company.objects.filter(name__iexact=name)
            .select_related("owner")
            .order_by("id")
        )
        if not companies:
            self.stdout.write(self.style.WARNING("Company not found."))
            return

        for company in companies:
            owner = company.owner
            self.stdout.write(
                "company_id={company_id} owner_id={owner_id} "
                "owner_username={username} owner_role={role} "
                "owner_active={active}".format(
                    company_id=company.id,
                    owner_id=owner.id,
                    username=owner.username,
                    role=owner.role,
                    active=owner.is_active,
                )
            )
