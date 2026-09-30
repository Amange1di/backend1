from rest_framework.exceptions import PermissionDenied

from core.models import Student, User


def resolve_support_telegram(user: User) -> str:
    if user.role == User.Role.COURSE_ADMIN:
        admin = (
            user.created_by
            if (
                user.created_by
                and user.created_by.role
                == User.Role.ADMIN
            )
            else None
        )
        if admin and admin.telegram:
            return admin.telegram

        admin = (
            User.objects.filter(
                role=User.Role.ADMIN
            )
            .order_by("date_joined")
            .first()
        )
        return (
            admin.telegram
            if admin and admin.telegram
            else ""
        )

    if user.role in (
        User.Role.TEACHER,
        User.Role.MANAGER,
        User.Role.STUDENT,
    ):
        if (
            user.created_by
            and user.created_by.telegram
        ):
            return user.created_by.telegram

        if user.company:
            course_admin = (
                User.objects.filter(
                    role=User.Role.COURSE_ADMIN,
                    company=user.company,
                )
                .order_by("date_joined")
                .first()
            )
            return (
                course_admin.telegram
                if (
                    course_admin
                    and course_admin.telegram
                )
                else ""
            )

        return ""

    if user.role == User.Role.ADMIN:
        return user.telegram or ""

    return ""


def get_company_student_cabinet_enabled(
    company,
):
    if not company:
        return False

    return User.objects.filter(
        role=User.Role.COURSE_ADMIN,
        company=company,
        is_student_cabinet_enabled=True,
    ).exists()


def student_has_allowed_group(
    student: Student,
) -> bool:
    groups = student.groups.all()
    if not groups.exists():
        return True

    return groups.filter(
        is_login_allowed=True
    ).exists()


def ensure_student_access_allowed(
    student: Student,
):
    if (
        not student.company
        or not get_company_student_cabinet_enabled(
            (
                student.company.name
                if student.company
                else ""
            )
        )
    ):
        raise PermissionDenied(
            (
                "Student cabinet is disabled "
                "for this company."
            )
        )

    if not student.can_login:
        raise PermissionDenied(
            (
                "Student login is disabled "
                "for this account."
            )
        )

    if not student_has_allowed_group(
        student
    ):
        raise PermissionDenied(
            (
                "Student login is disabled "
                "for this group."
            )
        )

    if (
        not student.user
        or student.user.role
        != User.Role.STUDENT
    ):
        raise PermissionDenied(
            "Student account is not configured."
        )

    if not student.user.is_active:
        raise PermissionDenied(
            "Student account is inactive."
        )
