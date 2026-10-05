import secrets
import string

from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from core.models import FirstLoginCredential


def _generate_password():
    chars = [
        *(secrets.choice(string.digits) for _ in range(4)),
        secrets.choice(string.ascii_uppercase),
    ]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def issue_first_login_password(user):
    plain = _generate_password()
    credential, _ = FirstLoginCredential.objects.update_or_create(
        user=user,
        defaults={
            "password_hash": make_password(plain),
            "is_used": False,
            "used_at": None,
        },
    )
    user.must_set_password = True
    user.set_unusable_password()
    user.save(update_fields=["must_set_password", "password"])
    user._one_time_password = plain
    return plain


def verify_and_consume_first_login_password(user, plain):
    try:
        credential = user.first_login_credential
    except FirstLoginCredential.DoesNotExist:
        return False

    if credential.is_used:
        return False

    if not check_password(plain, credential.password_hash):
        return False

    credential.is_used = True
    credential.used_at = timezone.now()
    credential.save(update_fields=["is_used", "used_at"])
    return True
