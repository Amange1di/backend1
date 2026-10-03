from rest_framework import serializers

from core.models import Company, TrialLead


class TrialLeadSerializer(serializers.ModelSerializer):
    group_assigned_label = serializers.CharField(
        source="group_assigned.name",
        read_only=True,
    )
    company_id = serializers.PrimaryKeyRelatedField(
        source="company",
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )
    assigned_manager = serializers.SerializerMethodField(
        read_only=True,
    )

    class Meta:
        model = TrialLead
        fields = (
            "id",
            "full_name",
            "phone",
            "age",
            "course_interest",
            "trial_attended",
            "status",
            "trial_date",
            "source",
            "comment",
            "converted_to_student",
            "group_assigned",
            "group_assigned_label",
            "payment_status",
            "company",
            "company_id",
            "assigned_manager",
            "created_at",
        )
        read_only_fields = ()

    def validate(self, attrs):
        status_value = attrs.get(
            "status",
            getattr(self.instance, "status", TrialLead.Status.NEW),
        )

        if status_value == TrialLead.Status.ATTENDED:
            attrs["trial_attended"] = True
        elif status_value == TrialLead.Status.NOT_ATTENDED:
            attrs["trial_attended"] = False

        if status_value == TrialLead.Status.CONVERTED:
            attrs["trial_attended"] = True
            attrs["converted_to_student"] = True

        if attrs.get("converted_to_student") is True:
            attrs["status"] = TrialLead.Status.CONVERTED
            attrs["trial_attended"] = True

        trial_date = attrs.get(
            "trial_date",
            getattr(self.instance, "trial_date", None),
        )
        effective_status = attrs.get("status", status_value)

        if effective_status in (
            TrialLead.Status.TRIAL_SCHEDULED,
            TrialLead.Status.ATTENDED,
            TrialLead.Status.NOT_ATTENDED,
        ) and not trial_date:
            raise serializers.ValidationError(
                {"trial_date": "trial_date_required"}
            )

        age = attrs.get("age")
        if age is not None and (age < 3 or age > 100):
            raise serializers.ValidationError(
                {"age": "age_out_of_range"}
            )

        return attrs

    def get_assigned_manager(self, obj):
        assignment = getattr(obj, "assignment", None)
        if assignment and assignment.manager:
            manager = assignment.manager
            full_name = (
                f"{manager.first_name} {manager.last_name}".strip()
            )
            return {
                "id": manager.id,
                "name": full_name or manager.username,
                "username": manager.username,
            }
        return None
