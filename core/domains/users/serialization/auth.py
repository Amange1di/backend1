import re

from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.models import Company, Course, User
from core.domains.users.passwords import validate_strong_password
from core.domains.auth.first_login import verify_and_consume_first_login_password

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True
    )

    def validate(self, attrs):
        username = (attrs.get("username") or "").strip()
        password = attrs.get("password") or ""

        user = authenticate(
            username=username,
            password=password,
        )
        first_login = False

        if not user:
            candidate = User.objects.filter(
                username__iexact=username,
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

class StudentIdentityLoginSerializer(
    serializers.Serializer
):
    phone_number = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        trim_whitespace=False,
    )

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

