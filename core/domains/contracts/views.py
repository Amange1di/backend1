import logging
from datetime import date

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Contract, ContractTemplate, Group, Student, User
from core.permissions import IsCourseAdminOrManager

from .serializers import ContractSerializer, ContractTemplateSerializer
from .services import generate_contract_pdf

logger = logging.getLogger(__name__)


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all().order_by("-created_at")
    serializer_class = ContractSerializer
    permission_classes = [IsCourseAdminOrManager]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == User.Role.COURSE_ADMIN:
            return qs.filter(company=user.company)
        if user.role == User.Role.MANAGER and user.company:
            return qs.filter(company=user.company)
        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in (User.Role.COURSE_ADMIN, User.Role.MANAGER):
            raise PermissionDenied(
                "Only course admins and managers can create contracts."
            )

        student = serializer.validated_data.get("student")
        if student.company != user.company:
            raise PermissionDenied("Student must belong to the same company.")

        group = serializer.validated_data.get("group")
        if group and group.company != user.company:
            raise PermissionDenied("Group must belong to the same company.")

        contract = serializer.save(company=user.company, created_by=user)
        try:
            generate_contract_pdf(contract)
        except Exception:
            logger.exception(
                "PDF auto-generation failed for contract %s",
                contract.contract_number,
            )

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()
        if instance.company != user.company:
            raise PermissionDenied("Not allowed for this contract.")
        if instance.status != Contract.Status.DRAFT:
            raise PermissionDenied("Only draft contracts can be edited.")
        serializer.save()

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        contract = self.get_object()
        if contract.company != request.user.company:
            raise PermissionDenied("Not allowed for this contract.")
        if contract.status != Contract.Status.DRAFT:
            return Response(
                {"detail": "Договор уже отправлен."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contract.status = Contract.Status.SENT
        contract.save(update_fields=["status"])
        return Response(ContractSerializer(contract).data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def sign(self, request, pk=None):
        contract = get_object_or_404(Contract, pk=pk)
        student = getattr(request.user, "student_profile", None)

        if not student or contract.student.id != student.id:
            raise PermissionDenied("Вы не можете подписать этот договор.")
        if contract.status != Contract.Status.SENT:
            return Response(
                {"detail": "Можно подписать только отправленный договор."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contract.status = Contract.Status.SIGNED
        contract.signed_at = timezone.now()
        contract.save(update_fields=["status", "signed_at"])
        return Response(ContractSerializer(contract).data)

    @action(detail=False, methods=["get", "post"], url_path="auto-fill")
    def auto_fill(self, request):
        student_id = (
            request.data.get("student_id")
            or request.query_params.get("student_id")
        )
        group_id = (
            request.data.get("group_id")
            or request.query_params.get("group_id")
        )

        if not student_id or not group_id:
            return Response(
                {"detail": "student_id и group_id обязательны."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            student = Student.objects.get(
                id=student_id,
                company=request.user.company,
            )
            group = Group.objects.get(
                id=group_id,
                company=request.user.company,
            )
        except (Student.DoesNotExist, Group.DoesNotExist):
            raise PermissionDenied("Студент или группа не найдены.")

        course = group.course
        amount = course.price if course else 0
        data = {
            "student": student.id,
            "student_name": str(student),
            "student_phone": student.phone,
            "group": group.id,
            "group_name": group.name,
            "course_name": course.title if course else "—",
            "amount": float(amount),
            "start_date": (
                group.start_date.isoformat()
                if group.start_date
                else date.today().isoformat()
            ),
            "end_date": (
                group.end_date.isoformat()
                if group.end_date
                else ""
            ),
        }

        if request.method == "POST":
            serializer = self.get_serializer(
                data={
                    "student": student.id,
                    "group": group.id,
                    "amount": amount,
                    "start_date": group.start_date or date.today(),
                    "end_date": group.end_date,
                }
            )
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers,
            )

        return Response(data)

    @action(detail=True, methods=["get"], url_path="pdf")
    def download_pdf(self, request, pk=None):
        contract = self.get_object()
        if contract.company != request.user.company:
            raise PermissionDenied("Not allowed for this contract.")

        try:
            pdf_file = generate_contract_pdf(
                contract,
                save_to_model=False,
            )
        except ImportError:
            pdf_file = None
        except Exception as exc:
            logger.exception(
                "PDF generation failed for contract %s",
                contract.contract_number,
            )
            return Response(
                {"detail": f"Ошибка генерации PDF: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if pdf_file is None:
            return Response(
                {"detail": "PDF generation is not available."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="contract_{contract.contract_number}.pdf"'
        )
        return response


class ContractTemplateViewSet(viewsets.ModelViewSet):
    queryset = ContractTemplate.objects.all().order_by(
        "-is_default",
        "-created_at",
    )
    serializer_class = ContractTemplateSerializer
    permission_classes = [IsCourseAdminOrManager]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == User.Role.COURSE_ADMIN:
            return qs.filter(company=user.company)
        if user.role == User.Role.MANAGER and user.company:
            return qs.filter(company=user.company)
        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in (User.Role.COURSE_ADMIN, User.Role.MANAGER):
            raise PermissionDenied(
                "Only course admins and managers can create contract templates."
            )

        if serializer.validated_data.get("is_default"):
            ContractTemplate.objects.filter(
                company=user.company
            ).update(is_default=False)

        serializer.save(company=user.company)

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()

        if instance.company != user.company:
            raise PermissionDenied("Not allowed for this template.")

        if serializer.validated_data.get("is_default"):
            ContractTemplate.objects.filter(
                company=user.company
            ).exclude(id=instance.id).update(is_default=False)

        serializer.save()


class StudentContractsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.STUDENT:
            raise PermissionDenied(
                "Only students can access their contracts."
            )

        student = getattr(request.user, "student_profile", None)
        if not student:
            return Response(
                {"detail": "Student profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        contracts = Contract.objects.filter(
            student=student
        ).order_by("-created_at")
        serializer = ContractSerializer(
            contracts,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)
