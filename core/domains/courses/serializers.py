from django.db import models
from rest_framework import serializers

from core.models import Course, User


class CourseSerializer(serializers.ModelSerializer):
    duration_weeks = serializers.IntegerField(
        required=False,
        default=0,
        min_value=0,
    )
    admins = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=User.objects.filter(
            models.Q(role=User.Role.COURSE_ADMIN)
            | models.Q(role=User.Role.TEACHER)
        ),
    )

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "price",
            "duration_weeks",
            "lesson_duration_minutes",
            "description",
            "schedule",
            "admins",
            "created_at",
        )
