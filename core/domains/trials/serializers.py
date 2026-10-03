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
        instance = self.instance

        status_value = attrs.get(
            "status",
            getattr(instance, "status", TrialLead.Status.NEW),
        )
        converted_value = attrs.get(
            "converted_to_student",
            getattr(instance, "converted_to_student", False),
        )

        if status_value == TrialLead.Status.CONVERTED:
            converted_value = True
            attrs["converted_to_student"] = True

        if converted_value:
            attrs["status"] = TrialLead.Status.CONVERTED
            attrs["trial_attended"] = True
            status_value = TrialLead.Status.CONVERTED
        elif status_value == TrialLead.Status.ATTENDED:
            attrs["trial_attended"] = True
        else:
            attrs["trial_attended"] = False

        trial_date = attrs.get(
            "trial_date",
            getattr(instance, "trial_date", None),
        )

        if status_value in (
            TrialLead.Status.TRIAL_SCHEDULED,
            TrialLead.Status.ATTENDED,
            TrialLead.Status.NOT_ATTENDED,
            TrialLead.Status.CONVERTED,
        ) and not trial_date:
            raise serializers.ValidationError(
                {"trial_date": "trial_date_required"}
            )

        if not converted_value:
            attrs["group_assigned"] = None
            attrs["payment_status"] = (
                TrialLead.PaymentStatus.NOT_PAID
            )

        age = attrs.get(
            "age",
            getattr(instance, "age", None),
        )
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
