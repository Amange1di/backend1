import re

from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.models import Company, Course, User

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True
    )

    def validate(self, attrs):
        user = authenticate(
            username=attrs.get("username"),
            password=attrs.get("password"),
        )
        if not user:
            raise serializers.ValidationError(
                _("Invalid credentials.")
            )
        attrs["user"] = user
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
        return attrs

