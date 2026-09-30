from rest_framework import serializers

from core.models import Contract, ContractTemplate


class ContractSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    group_name = serializers.SerializerMethodField()
    company_name = serializers.CharField(source="company.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Contract
        fields = (
            "id",
            "company",
            "company_name",
            "student",
            "student_name",
            "group",
            "group_name",
            "status",
            "status_display",
            "contract_number",
            "amount",
            "start_date",
            "end_date",
            "terms",
            "created_by",
            "signed_at",
            "pdf_file",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "company",
            "contract_number",
            "created_by",
            "signed_at",
            "pdf_file",
            "created_at",
            "updated_at",
        )

    def get_student_name(self, obj):
        return str(obj.student) if obj.student else "—"

    def get_group_name(self, obj):
        return obj.group.name if obj.group else "—"


class ContractTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractTemplate
        fields = (
            "id",
            "company",
            "name",
            "html_content",
            "is_default",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("company", "created_at", "updated_at")
