import secrets
import string

from django.core import signing
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


FIRST_LOGIN_LINK_SALT = "eduosh.first-login-link"
FIRST_LOGIN_LINK_MAX_AGE = 60 * 60 * 24


def create_first_login_link_token(user):
    credential = FirstLoginCredential.objects.filter(
        user=user,
        is_used=False,
    ).first()
    if not credential:
        return ""
    return signing.dumps(
        {
            "user_id": user.id,
            "credential_created_at": credential.created_at.isoformat(),
        },
        salt=FIRST_LOGIN_LINK_SALT,
        compress=True,
    )


def consume_first_login_link_token(token):
    try:
        payload = signing.loads(
            token,
            salt=FIRST_LOGIN_LINK_SALT,
            max_age=FIRST_LOGIN_LINK_MAX_AGE,
        )
    except (signing.BadSignature, signing.SignatureExpired):
        return None

    user_id = payload.get("user_id")
    created_at = payload.get("credential_created_at")
    if not user_id or not created_at:
        return None

    credential = FirstLoginCredential.objects.select_related("user").filter(
        user_id=user_id,
        is_used=False,
    ).first()
    if not credential:
        return None
    if credential.created_at.isoformat() != created_at:
        return None

    credential.is_used = True
    credential.used_at = timezone.now()
    credential.save(update_fields=["is_used", "used_at"])
    return credential.user
