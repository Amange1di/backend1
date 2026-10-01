from rest_framework import viewsets

from core.models import User
from core.permissions import IsCourseAdminOrManager
from finance.models import SalaryRecord
from finance.serializers import SalaryRecordSerializer


class SalaryRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [IsCourseAdminOrManager]
    serializer_class = SalaryRecordSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.COURSE_ADMIN:
            company = user.company
        elif user.role == User.Role.MANAGER:
            company = user.company
        else:
            return SalaryRecord.objects.none()

        if not company:
            return SalaryRecord.objects.none()

        qs = SalaryRecord.objects.filter(company=company).select_related("employee")

        employee_role = self.request.query_params.get("role")
        status = self.request.query_params.get("status")
        year = self.request.query_params.get("year")
        month = self.request.query_params.get("month")

        if employee_role:
            qs = qs.filter(employee__role=employee_role)
        if status:
            qs = qs.filter(status=status)
        if year and year.isdigit():
            qs = qs.filter(year=int(year))
        if month and month.isdigit():
            qs = qs.filter(month=int(month))

        return qs

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)
