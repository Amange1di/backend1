"""Create editable draft websites for companies without touching existing pages.

Usage:
  python manage.py seed_company_websites --dry-run
  python manage.py seed_company_websites
  python manage.py seed_company_websites --company-id 4
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from core.models import Company, LandingPage, LandingSection


def initial_sections(company):
    courses = list(company.courses.filter(is_active=True).order_by("id")[:12])
    course_items = [
        {
            "title": course.title,
            "description": course.description,
            "price": str(course.price),
            "slug": course.slug,
        }
        for course in courses
    ]
    return [
        ("header", {"title": company.name, "logo": company.logo.url if company.logo else ""}),
        ("hero", {
            "title": company.name,
            "subtitle": company.description or "Откройте новые возможности через обучение.",
            "buttonText": "Посмотреть курсы",
        }),
        ("about", {"title": "О нас", "description": company.description or ""}),
        ("course_grid", {"title": "Наши курсы", "courses": course_items}),
        ("benefits", {"title": "Почему выбирают нас", "items": []}),
        ("teacher_slider", {"title": "Преподаватели", "items": []}),
        ("testimonials", {"title": "Отзывы", "items": []}),
        ("faq", {"title": "Частые вопросы", "items": []}),
        ("contacts", {
            "title": "Контакты",
            "city": company.city,
            "district": company.district,
            "phone": company.phone,
            "instagram": company.instagram,
            "telegram": company.telegram,
            "whatsapp": company.whatsapp,
        }),
        ("lead_form", {"title": "Записаться на курс", "companyId": company.pk}),
    ]


class Command(BaseCommand):
    help = "Create draft landing websites for companies without overwriting existing sites."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--company-id", type=int, default=None)

    def handle(self, *args, **options):
        companies = Company.objects.filter(is_active=True).order_by("id")
        if options["company_id"] is not None:
            companies = companies.filter(pk=options["company_id"])
        created = skipped = 0

        for company in companies.iterator():
            if LandingPage.objects.filter(company=company).exists():
                skipped += 1
                self.stdout.write(f"SKIP {company.pk}: {company.name} (site exists)")
                continue

            base = (slugify(company.slug, allow_unicode=False) or f"company-{company.pk}")[:130]
            slug = base
            suffix = 1
            while LandingPage.objects.filter(slug=slug).exists():
                suffix += 1
                slug = f"{base[:125]}-{suffix}"

            if options["dry_run"]:
                self.stdout.write(f"WOULD CREATE {company.pk}: {company.name} ({slug})")
                created += 1
                continue

            with transaction.atomic():
                # Recheck under the transaction; never overwrite a customized site.
                if LandingPage.objects.filter(company=company).exists():
                    skipped += 1
                    continue
                owner = company.owner if company.owner.role == "course_admin" else None
                page = LandingPage.objects.create(
                    company=company,
                    owner=owner,
                    title=company.name[:200],
                    slug=slug,
                    status=LandingPage.Status.DRAFT,
                )
                LandingSection.objects.bulk_create([
                    LandingSection(page=page, section_type=section_type, order=index, content=data)
                    for index, (section_type, data) in enumerate(initial_sections(company))
                ])
            created += 1
            self.stdout.write(self.style.SUCCESS(f"CREATED {company.pk}: {slug} (draft)"))

        self.stdout.write(f"Done. {'Would create' if options['dry_run'] else 'Created'}: {created}; skipped: {skipped}")
