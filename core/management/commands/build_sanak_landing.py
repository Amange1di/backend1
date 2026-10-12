"""Create a complete, editable Sanak IT Academy landing without resetting data.

Usage:
    python manage.py build_sanak_landing
    python manage.py build_sanak_landing --hero-image https://example.com/academy.jpg
    python manage.py build_sanak_landing --replace-draft

The command creates a DRAFT only. Review it in the builder and submit for moderation.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from core.models import Company, LandingPage, LandingSection, User


class Command(BaseCommand):
    help = "Create a seven-section Sanak IT Academy landing from its existing CRM data."

    def add_arguments(self, parser):
        parser.add_argument("--hero-image", default="", help="Public HTTPS URL of an authorized academy photo")
        parser.add_argument("--replace-draft", action="store_true", help="Replace only this command's existing draft")

    @transaction.atomic
    def handle(self, *args, **options):
        company = Company.objects.filter(slug="sanak-it-academy").first()
        if not company:
            raise CommandError("Sanak IT Academy not found. No data changed.")
        owner = User.objects.filter(company=company, role=User.Role.COURSE_ADMIN).first()
        if not owner:
            raise CommandError("Sanak course_admin not found. No data changed.")
        image = options["hero_image"].strip()
        if image and not image.startswith("https://"):
            raise CommandError("--hero-image must be an HTTPS URL")
        slug = "sanak-it-academy-premium"
        page = LandingPage.objects.filter(slug=slug).first()
        if page:
            if not options["replace_draft"]:
                raise CommandError("Page already exists. Use --replace-draft to replace its draft only.")
            if page.company_id != company.id or page.status != LandingPage.Status.DRAFT:
                raise CommandError("Existing page is not a Sanak draft. Refusing to overwrite.")
        elif owner.max_pages and owner.get_pages_count() >= owner.max_pages:
            raise CommandError("Owner landing page limit reached.")
        else:
            page = LandingPage.objects.create(
                title="Sanak IT Academy — Обучение IT в Оше",
                slug=slug, company=company, owner=owner,
                status=LandingPage.Status.DRAFT,
            )

        courses = list(company.courses.filter(is_active=True).order_by("id")[:6])
        course_lines = [
            f"{course.title}|{int(course.price):,} сом".replace(",", " ")
            for course in courses
        ]
        descriptions = [
            f"{course.title}: {course.description}".strip()
            for course in courses if course.description
        ]
        course_count = company.courses.filter(is_active=True).count()
        teacher_count = User.objects.filter(company=company, role=User.Role.TEACHER).count()
        sections = [
            ("hero", {
                "title": "Освой IT-профессию с Sanak IT Academy",
                "subtitle": company.description or "Практическое обучение IT в Оше.",
                "button_label": "Записаться на консультацию",
                "button_href": "#lead-form",
                "background_url": image,
                "design_variant": "cinematic" if image else "gradient",
            }),
            ("about", {
                "title": "Обучение, ориентированное на практику",
                "text": company.description or "Выберите направление и начните обучение.",
                "design_variant": "reverse",
            }),
            ("course_grid", {
                "title": "Выберите своё IT-направление",
                "design_variant": "featured",
                "items": "\n".join(descriptions),
            }),
            ("teacher_slider", {
                "title": "Преподаватели Sanak IT Academy",
                "design_variant": "cards",
            }),
            ("benefits", {
                "title": "Почему выбирают Sanak",
                "items": "Практические задания\nСовременные IT-направления\nПоддержка во время обучения",
            }),
            ("lead_form", {
                "title": "Поможем выбрать курс",
                "design_variant": "premium",
            }),
            ("contacts", {
                "phone": company.phone or "",
                "telegram": company.telegram or "",
                "whatsapp": company.whatsapp or "",
                "address": company.district or "",
                "design_variant": "cards",
            }),
        ]
        if owner.max_blocks and len(sections) > owner.max_blocks:
            raise CommandError("Owner landing section limit is too low.")
        if options["replace_draft"]:
            page.sections.all().delete()
        LandingSection.objects.bulk_create([
            LandingSection(page=page, section_type=kind, order=i, content=data)
            for i, (kind, data) in enumerate(sections)
        ])
        self.stdout.write(self.style.SUCCESS(
            f"Created Sanak draft #{page.pk}, slug={page.slug}, sections={len(sections)}, "
            f"active_courses={course_count}, teachers={teacher_count}. "
            "Review in builder; draft was NOT published."
        ))
