from rest_framework import serializers
from .models import Budget, Forecast, PeriodComparison, AccountingReport, MonthlySummary, BudgetAlert


class BudgetSerializer(serializers.ModelSerializer):
    spent = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remaining = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    utilization_rate = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    is_over_budget = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = [
            'id', 'company', 'category', 'amount', 'period_start',
            'period_end', 'is_active', 'spent', 'remaining',
            'utilization_rate', 'is_over_budget', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'spent', 'remaining', 'utilization_rate', 'created_at', 'updated_at']

    def get_is_over_budget(self, obj):
        return obj.check_over_budget()


class BudgetAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetAlert
        fields = ['id', 'budget', 'threshold', 'is_sent', 'created_at']
        read_only_fields = ['id', 'is_sent', 'created_at']


class ForecastSerializer(serializers.ModelSerializer):
    variance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True, allow_null=True)
    variance_percent = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True, allow_null=True)

    class Meta:
        model = Forecast
        fields = [
            'id', 'company', 'forecast_type', 'period_month', 'period_year',
            'estimated_amount', 'actual_amount', 'confidence_level', 'notes',
            'variance', 'variance_percent', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'variance', 'variance_percent', 'created_at', 'updated_at']


class PeriodComparisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodComparison
        fields = [
            'id', 'company', 'period_1_label', 'period_2_label',
            'period_1_start', 'period_1_end', 'period_2_start', 'period_2_end',
            'comparison_date'
        ]
        read_only_fields = ['id', 'comparison_date']


class AccountingReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountingReport
        fields = [
            'id', 'company', 'report_type', 'period_start', 'period_end',
            'generated_at', 'generated_by', 'pdf_file', 'notes'
        ]
        read_only_fields = ['id', 'generated_at', 'generated_by']


class MonthlySummarySerializer(serializers.ModelSerializer):
    profit_margin = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)

    class Meta:
        model = MonthlySummary
        fields = [
            'id', 'company', 'year', 'month', 'total_income',
            'total_expenses', 'total_salaries', 'net_profit',
            'total_students', 'total_groups', 'profit_margin', 'generated_at'
        ]
        read_only_fields = ['id', 'profit_margin', 'generated_at']
