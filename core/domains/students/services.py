import re

from core.models import Student, User
from core.domains.auth.first_login import issue_first_login_password


def normalize_phone(value: str) -> str:
    return re.sub(r"\D+", "", value or "")


def build_student_username(
    student: Student,
) -> str:
    base = (
        normalize_phone(student.phone)
        or f"student{student.id}"
    )
    company_name = (
        student.company.name
        if student.company
        and student.company.name
        else ""
    )
    company = re.sub(
        r"[^a-z0-9]+",
        "",
        company_name,
    )[:24]
    prefix = company or "eduosh"

    return (
        f"{prefix}_student_"
        f"{base}_{student.id}"
    )


def sync_student_user(
    student: Student,
    *,
    created_by=None,
):
    user = student.user

    if not user:
        user = User(
            username=build_student_username(
                student
            ),
            role=User.Role.STUDENT,
            company=student.company,
            created_by=created_by,
            first_name=student.first_name,
            last_name=student.last_name,
            phone=student.phone,
            telegram=student.telegram,
            must_set_password=True,
        )
        user.set_unusable_password()
        user.save()

        student.user = user
        student.save(
            update_fields=["user"]
        )

        one_time_password = (
            issue_first_login_password(user)
        )
        student._one_time_password = (
            one_time_password
        )

        return student

    changed_fields = []

    field_values = {
        "first_name": student.first_name,
        "last_name": student.last_name,
        "phone": student.phone,
        "telegram": student.telegram,
        "company": student.company,
    }

    for field, value in field_values.items():
        if getattr(user, field) != value:
            setattr(user, field, value)
            changed_fields.append(field)

    if user.role != User.Role.STUDENT:
        user.role = User.Role.STUDENT
        changed_fields.append("role")

    if changed_fields:
        user.save(
            update_fields=changed_fields
        )

    return student
