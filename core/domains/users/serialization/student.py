import re

from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.models import Company, Course, User

class StudentProfileSerializer(
    serializers.Serializer
):
    phone = serializers.CharField(
        required=False,
        allow_blank=False,
    )
    telegram = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    password = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        trim_whitespace=False,
        min_length=6,
    )

