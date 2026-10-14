"""Generate a four-page public website for each company without overwriting existing pages."""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import Company, LandingHeaderLink, LandingPage, LandingSection

# Stable remote images; every image is an ordinary editable URL.
IMAGES = {
    "hero": "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=1600&q=85",
    "about": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=1200&q=85",
    "courses": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=1200&q=85",
    "contacts": "https://images.unsplash.com/photo-1497366754035-f200968a6e72?w=1200&q=85",
}

PAGES = (
    ("home", "Главная"),
    ("courses", "Курсы"),
    ("about", "О компании"),
    ("contacts", "Контакты"),
)


def sections_for(company, kind):
    description = company.description or "Обучение и развитие вместе с нами."
    contact = {
        "title": "Контакты",
        "phone": company.phone or "",
        "city": company.city or "",
        "address": company.district or "",
        "telegram": company.telegram or "",
        "whatsapp": company.whatsapp or "",
        "instagram": company.instagram or "",
    }
    header = ("header", {"title": company.name, "header_title": company.name, "header_logo_url": company.logo_data or "", "header_phone": company.phone or ""})
    hero = ("hero", {"title": company.name if kind == "home" else dict(PAGES)[kind], "subtitle": description, "background_url": IMAGES["hero" if kind == "home" else kind], "button_label": "Посмотреть курсы", "button_href": "#courses"})
    catalog = ("course_grid", {"title": "Наши курсы"})
    lead = ("lead_form", {"title": "Оставить заявку", "companyId": company.pk})
    if kind == "home":
        return [header, hero, ("about", {"title": "О компании", "body": description, "image_url": IMAGES["about"]}), catalog, lead, ("contacts", contact)]
    if kind == "courses":
        return [header, hero, catalog, lead]
    if kind == "about":
        return [header, hero, ("about", {"title": "О нас", "body": description, "image_url": IMAGES["about"]}), ("benefits", {"title": "Почему выбирают нас", "items": []}), ("teacher_slider", {"title": "Наша команда"})]
    return [header, hero, ("contacts", contact), lead]


def create_company_website(company, *, publish=True, dry_run=False):
    """Create a complete website only if this company has no landing pages."""
    if LandingPage.objects.filter(company_id=company.pk).exists():
        return []
    if dry_run:
        return [f"{company.slug}-{key}" for key, _ in PAGES]
    with transaction.atomic():
        # Lock company to make concurrent seed and creation attempts idempotent.
        company = Company.objects.select_for_update().get(pk=company.pk)
        if LandingPage.objects.filter(company_id=company.pk).exists():
            return []
        owner = company.owner if company.owner.role in ("company_owner", "course_admin") else None
        result = []
        for key, title in PAGES:
            base = f"{company.slug}-{key}"[:138]
            slug = base
            index = 2
            while LandingPage.objects.filter(slug=slug).exists():
                slug = f"{base[:135]}-{index}"
                index += 1
            page = LandingPage.objects.create(
                company=company,
                owner=owner,
                title=f"{company.name} — {title}"[:200],
                slug=slug,
                status=LandingPage.Status.ACTIVE if publish else LandingPage.Status.DRAFT,
                published_at=timezone.now() if publish else None,
            )
            LandingSection.objects.bulk_create([
                LandingSection(page=page, section_type=type_, order=position, content=content)
                for position, (type_, content) in enumerate(sections_for(company, key))
            ])
            result.append(page)
        LandingHeaderLink.objects.bulk_create([
            LandingHeaderLink(company=company, target_page=page, label=label, order=i)
            for i, ((_, label), page) in enumerate(zip(PAGES, result))
        ])
        return result


class Command(BaseCommand):
    help = "Create four-page websites for companies without existing landings. Existing pages are never changed."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--company-id", type=int, default=None)
        parser.add_argument("--draft", action="store_true", help="Create unpublished drafts instead of public pages")

    def handle(self, *args, **options):
        companies = Company.objects.filter(is_active=True).order_by("id")
        if options["company_id"] is not None:
            companies = companies.filter(pk=options["company_id"])
        created = skipped = 0
        for company in companies.iterator():
            pages = create_company_website(company, publish=not options["draft"], dry_run=options["dry_run"])
            if not pages:
                skipped += 1
                continue
            created += 1
            self.stdout.write(f"{'WOULD CREATE' if options['dry_run'] else 'CREATED'} {company.pk} {company.name}: {', '.join(str(p.slug) if hasattr(p, 'slug') else p for p in pages)}")
        self.stdout.write(f"Companies created: {created}, skipped: {skipped}")
