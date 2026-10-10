from django.utils import timezone
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.audit import write_audit
from core.models import Payment, User
from core.permissions import (
    IsCourseAdminOrManagerOrStudentReadOnly,
)

from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.filter(
        archived_at__isnull=True
    ).order_by("-created_at")
    serializer_class = PaymentSerializer
    permission_classes = [
        IsCourseAdminOrManagerOrStudentReadOnly
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        selected_branch = self.request.COOKIES.get("eduosh_branch")
        branch_id = int(selected_branch) if selected_branch and selected_branch.isdigit() else None

        if (
            user.is_authenticated
            and user.role in (User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN)
        ):
            queryset = queryset.filter(company=user.company)
            if user.role == User.Role.COURSE_ADMIN:
                allowed = user.branches.filter(is_active=True)
                if branch_id:
                    if not allowed.filter(id=branch_id).exists():
                        raise PermissionDenied("branch_access_denied")
                    return queryset.filter(branch_id=branch_id).distinct()
                return queryset.filter(branch__in=allowed).distinct()
            return queryset.filter(branch_id=branch_id).distinct() if branch_id else queryset.distinct()

        if (
            user.is_authenticated
            and user.role == User.Role.MANAGER
        ):
            if not user.company:
                return queryset.none()

            allowed = user.branches.filter(is_active=True)
            if branch_id:
                if not allowed.filter(id=branch_id).exists():
                    raise PermissionDenied("branch_access_denied")
                return queryset.filter(company=user.company, branch_id=branch_id).distinct()
            return queryset.filter(company=user.company, branch__in=allowed).distinct()

        if (
            user.is_authenticated
            and user.role == User.Role.STUDENT
        ):
            return queryset.filter(
                student__user=user
            )

        return queryset

    def perform_create(self, serializer):
        user = self.request.user

        if user.role in (
            User.Role.COMPANY_OWNER,
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            student = serializer.validated_data.get(
                "student"
            )
            group = serializer.validated_data.get(
                "group"
            )
            allowed = False

            if (
                student
                and student.primary_course
            ):
                if (
                    user.role
                    == User.Role.COURSE_ADMIN
                ):
                    allowed = (
                        student.primary_course
                        .admins.filter(
                            id=user.id
                        )
                        .exists()
                    )
                else:
                    allowed = (
                        student.primary_course
                        .admins.filter(
                            company=user.company
                        )
                        .exists()
                    )

            if (
                student
                and student.company
                == user.company
            ):
                allowed = True

            if group:
                if group.course:
                    if (
                        user.role
                        == User.Role.COURSE_ADMIN
                    ):
                        allowed = (
                            group.course.admins
                            .filter(id=user.id)
                            .exists()
                        )
                    else:
                        allowed = (
                            group.course.admins
                            .filter(
                                company=user.company
                            )
                            .exists()
                        )

                if (
                    group.company
                    and group.company
                    == user.company
                ):
                    allowed = True

            if not allowed:
                raise PermissionDenied(
                    "Not allowed for this course."
                )

        elif user.role == User.Role.STUDENT:
            raise PermissionDenied(
                "Students cannot create payments."
            )

        student = serializer.validated_data.get(
            "student"
        )
        group = serializer.validated_data.get(
            "group"
        )

        if student and student.archived_at:
            raise PermissionDenied(
                "Archived student cannot receive a new payment."
            )
        if group and group.archived_at:
            raise PermissionDenied(
                "Archived group cannot receive a new payment."
            )
        company = serializer.validated_data.get(
            "company"
        )

        if not company:
            company = (
                (
                    student.company
                    if student
                    and student.company
                    else None
                )
                or (
                    group.company
                    if group
                    and group.company
                    else None
                )
            )

        branch = serializer.validated_data.get("branch")
        if not branch and group:
            branch = group.branch
        if not branch:
            selected_branch = self.request.COOKIES.get("eduosh_branch")
            if selected_branch and selected_branch.isdigit():
                branch = user.company.branches.filter(id=int(selected_branch), is_active=True).first()
        if not branch or branch.company_id != user.company_id:
            raise PermissionDenied("branch_access_denied")
        if user.role != User.Role.COMPANY_OWNER and not user.branches.filter(id=branch.id, is_active=True).exists():
            raise PermissionDenied("branch_access_denied")
        if group and group.branch_id and group.branch_id != branch.id:
            raise PermissionDenied("payment_group_branch_mismatch")

        serializer.save(
            company=company,
            branch=branch,
            received_by=user,
        )

    def destroy(self, request, *args, **kwargs):
        if request.user.role in (
            User.Role.MANAGER,
            User.Role.STUDENT,
        ):
            raise PermissionDenied(
                "Not allowed to archive payments."
            )

        payment = self.get_object()
        payment.archived_at = timezone.now()
        payment.save(update_fields=["archived_at"])

        write_audit(
            request,
            action="payment.archived",
            obj=payment,
            company=payment.company,
            after={
                "archived_at": payment.archived_at.isoformat(),
                "amount": str(payment.amount),
                "status": payment.status,
            },
        )

        return Response(status=204)
