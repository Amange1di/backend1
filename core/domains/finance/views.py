from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from core.models import Expense, Group, GroupMonth, User
from core.permissions import (
    IsCourseAdminOrManager,
    IsCourseAdminOrManagerReadOnly,
)

from .serializers import (
    ExpenseSerializer,
    GroupMonthSerializer,
)


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.none()
    permission_classes = [
        IsCourseAdminOrManager
    ]
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            if user.company:
                return Expense.objects.filter(
                    company=user.company
                )

        return Expense.objects.none()

    def perform_create(self, serializer):
        company = self.request.user.company
        if not company:
            raise PermissionDenied(
                (
                    "У вас нет компании "
                    "для создания расходов."
                )
            )

        serializer.save(company=company)


class GroupMonthViewSet(viewsets.ModelViewSet):
    queryset = GroupMonth.objects.none()
    permission_classes = [
        IsCourseAdminOrManagerReadOnly
    ]
    serializer_class = GroupMonthSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            if user.company:
                queryset = GroupMonth.objects.filter(
                    group__company=user.company
                )
            else:
                return GroupMonth.objects.none()

        elif user.role == User.Role.TEACHER:
            queryset = GroupMonth.objects.filter(
                group__teacher=user
            )

        else:
            return GroupMonth.objects.none()

        group_id = self.request.query_params.get(
            "group"
        )
        if group_id and group_id.isdigit():
            queryset = queryset.filter(
                group_id=int(group_id)
            )

        teacher_id = self.request.query_params.get(
            "teacher_id"
        )
        if (
            teacher_id
            and teacher_id.isdigit()
        ):
            queryset = queryset.filter(
                group__teacher_id=int(
                    teacher_id
                )
            )

        month_number = (
            self.request.query_params.get(
                "month_number"
            )
        )
        if (
            month_number
            and month_number.isdigit()
        ):
            queryset = queryset.filter(
                month_number=int(
                    month_number
                )
            )

        status_value = (
            self.request.query_params.get(
                "status"
            )
        )
        if status_value:
            queryset = queryset.filter(
                status=status_value
            )

        return (
            queryset
            .select_related(
                "group",
                "group__course",
            )
            .prefetch_related(
                "group__students"
            )
        )

    def list(self, request, *args, **kwargs):
        group_id = request.query_params.get(
            "group"
        )
        if group_id:
            try:
                group = Group.objects.get(
                    id=group_id
                )
                if (
                    group.total_months
                    and group.total_months > 0
                ):
                    existing = set(
                        GroupMonth.objects.filter(
                            group=group
                        ).values_list(
                            "month_number",
                            flat=True,
                        )
                    )

                    for month_number in range(
                        1,
                        group.total_months + 1,
                    ):
                        if (
                            month_number
                            not in existing
                        ):
                            GroupMonth.objects.create(
                                group=group,
                                month_number=month_number,
                                status=(
                                    GroupMonth.Status.PENDING
                                ),
                            )

            except Group.DoesNotExist:
                pass

        return super().list(
            request,
            *args,
            **kwargs,
        )
