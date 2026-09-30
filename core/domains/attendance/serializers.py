from rest_framework import serializers

from core.models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = (
            "id",
            "group",
            "student",
            "date",
            "status",
            "created_at",
        )
