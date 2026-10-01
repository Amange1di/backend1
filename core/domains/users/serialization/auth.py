from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.models import User
from core.domains.users.passwords import validate_strong_password
from core.domains.auth.first_login import verify_and_consume_first_login_password
from core.domains.students.services import normalize_phone

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True
    )

    def validate(self, attrs):
        login_value = (attrs.get("username") or "").strip()
        password = attrs.get("password") or ""

        # Students always sign in with their phone number. Formatting does not
        # matter: +996 700 123 456, 996700123456, etc. resolve to the same user.
        normalized_phone = normalize_phone(login_value)
        student_candidate = None
        if normalized_phone:
            for candidate in User.objects.filter(
                role=User.Role.STUDENT,
                is_active=True,
            ).only(
                "id",
                "username",
                "phone",
                "password",
                "must_set_password",
            ).iterator():
                if normalize_phone(candidate.phone) == normalized_phone:
                    student_candidate = candidate
                    break

        auth_username = (
            student_candidate.username
            if student_candidate
            else login_value
        )

        user = authenticate(
            username=auth_username,
            password=password,
        )
        first_login = False

        if not user:
            candidate = student_candidate or User.objects.filter(
                username__iexact=login_value,
                is_active=True,
            ).first()

            if (
                candidate
                and candidate.must_set_password
                and verify_and_consume_first_login_password(
                    candidate,
                    password,
                )
            ):
                user = candidate
                first_login = True

        if not user:
            raise serializers.ValidationError(
                _("Invalid credentials.")
            )

        attrs["user"] = user
        attrs["first_login"] = first_login
        return attrs

class StudentSetPasswordSerializer(
    serializers.Serializer
):
    password = serializers.CharField(
        write_only=True,
        min_length=6,
    )
    password_confirm = serializers.CharField(
        write_only=True,
        min_length=6,
    )

    def validate(self, attrs):
        if (
            attrs["password"]
            != attrs["password_confirm"]
        ):
            raise serializers.ValidationError(
                {
                    "password_confirm": _(
                        "Passwords do not match."
                    )
                }
            )
        validate_strong_password(attrs["password"])
        return attrs

