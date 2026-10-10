from rest_framework import serializers

from core.models import Auditorium, Company


class AuditoriumSerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(
        source="company",
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Auditorium
        fields = (
            "id",
            "branch",
            "name",
            "number",
            "company",
            "company_id",
            "created_at",
        )
        read_only_fields = ()
