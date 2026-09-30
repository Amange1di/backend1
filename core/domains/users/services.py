from core.models import User


def resolve_user_company_name(
    user: User,
) -> str:
    if (
        getattr(user, "company", None)
        and user.company.name
    ):
        return user.company.name.strip()

    if (
        user.role == User.Role.MANAGER
        and user.created_by
    ):
        created_company = getattr(
            user.created_by,
            "company",
            None,
        )
        if (
            created_company
            and created_company.name
        ):
            return (
                created_company.name.strip()
            )

    return ""
