from rest_framework.exceptions import PermissionDenied

from core.models import LandingHeaderLink, LandingPage, User


def validate_landing_page_for_publication(
    page: LandingPage,
    owner: User | None,
):
    if (
        owner
        and owner.role == User.Role.COURSE_ADMIN
        and page.sections.count() > owner.max_blocks
    ):
        raise PermissionDenied(
            (
                "Page exceeds the allowed number "
                f"of blocks ({owner.max_blocks})."
            )
        )

    total_pages = LandingPage.objects.filter(
        company=page.company
    ).count()

    if total_pages <= 1:
        return

    links = LandingHeaderLink.objects.filter(
        company=page.company
    )
    if not links.exists():
        raise PermissionDenied(
            (
                "Header navigation must be configured "
                "when more than one landing page exists."
            )
        )

    invalid_target_exists = links.exclude(
        target_page__company=page.company
    ).exists()
    if invalid_target_exists:
        raise PermissionDenied(
            (
                "All header links must target pages "
                "from the same company."
            )
        )
