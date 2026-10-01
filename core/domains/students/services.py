import re

from core.models import Student, User
from core.domains.auth.first_login import issue_first_login_password


def normalize_phone(value: str) -> str:
    return re.sub(r"\D+", "", value or "")


def build_student_username(
    student: Student,
) -> str:
    phone = normalize_phone(student.phone)
    if phone:
        if not User.objects.filter(username=phone).exists():
            return phone

        return f"student_{phone}_{student.id}"

    return f"student_{student.id}"


def find_existing_student_user_by_phone(
    phone: str,
):
    normalized = normalize_phone(phone)
    if not normalized:
        return None

    # Phone is a private cross-company identity key. We intentionally resolve
    # it only on the backend and never expose whether another company already
    # has this account.
    candidates = User.objects.filter(
        role=User.Role.STUDENT,
        is_active=True,
    ).only("id", "phone")

    for candidate in candidates.iterator():
        if normalize_phone(candidate.phone) == normalized:
            return candidate

    return None


def sync_student_user(
    student: Student,
    *,
    created_by=None,
):
    user = student.user

    if not user:
        existing_user = find_existing_student_user_by_phone(
            student.phone
        )

        if existing_user:
            student.user = existing_user
            student.save(
                update_fields=["user"]
            )
            # Do not mutate the shared account from a company-side student
            # record. This prevents one course admin from changing another
            # company's view of the same person's global account.
            return student

        user = User(
            # Student-facing login is always the phone number. The username
            # remains an internal unique identifier and normally equals the
            # normalized phone.
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

    # If this Student is the account's original/primary company profile,
    # keep the account in sync. Shared profiles from other companies remain
    # company-local and never overwrite global identity fields.
    if (
        user.company_id
        and student.company_id
        and user.company_id != student.company_id
    ):
        return student

    changed_fields = []

    field_values = {
        "first_name": student.first_name,
        "last_name": student.last_name,
        "phone": student.phone,
        "telegram": student.telegram,
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
