from rest_framework import serializers
from core.models import Branch


class BranchSerializer(serializers.ModelSerializer):
    can_archive = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = ("id", "company", "name", "address", "phone", "email", "is_main", "is_active", "can_archive", "created_at", "updated_at")
        read_only_fields = ("company", "created_at", "updated_at", "can_archive")

    def get_can_archive(self, obj):
        return not obj.is_main and obj.is_active

    def validate(self, attrs):
        request = self.context["request"]
        company = request.user.company
        if not company:
            raise serializers.ValidationError({"company": "company_required"})
        if self.instance is None and company.branches.filter(is_active=True).count() >= company.branch_limit:
            raise serializers.ValidationError({"code": "branch_limit_reached", "branch_limit": company.branch_limit})
        return attrs
