from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    ApplicationStatus,
    Company,
    StudentApplication,
    TeacherApplication,
    User,
)

from .serializers import (
    StudentApplicationSerializer,
    TeacherApplicationSerializer,
)


def _user_company(user):
    company = getattr(user, "company", None)
    if company:
        return company

    if getattr(user, "role", None) == User.Role.COURSE_ADMIN:
        return Company.objects.filter(owner=user).first()

    created_by = getattr(user, "created_by", None)
    return getattr(created_by, "company", None)


def _ensure_staff(user):
    if user.role not in (
        User.Role.COURSE_ADMIN,
        User.Role.MANAGER,
    ):
        raise PermissionDenied(
            "staff_only"
        )


class TeacherApplicationCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TeacherApplicationSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        application = serializer.save()
        return Response(
            TeacherApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED,
        )


class StudentApplicationCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = StudentApplicationSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        application = serializer.save()
        return Response(
            StudentApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED,
        )


class MarketplaceApplicationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        _ensure_staff(request.user)
        company = _user_company(request.user)
        if not company:
            return Response([])

        application_type = request.query_params.get("type")
        application_status = request.query_params.get("status")
        company_name = request.query_params.get("company_name")

        if (
            company_name
            and company.name.casefold() != company_name.strip().casefold()
        ):
            return Response([])

        result = []

        if application_type in (None, "", "teacher"):
            teachers = TeacherApplication.objects.filter(
                company=company
            )
            if application_status:
                teachers = teachers.filter(status=application_status)
            result.extend(
                TeacherApplicationSerializer(
                    teachers,
                    many=True,
                ).data
            )

        if application_type in (None, "", "student"):
            students = StudentApplication.objects.filter(
                company=company
            )
            if application_status:
                students = students.filter(status=application_status)
            result.extend(
                StudentApplicationSerializer(
                    students,
                    many=True,
                ).data
            )

        result.sort(
            key=lambda item: item.get("created_at") or "",
            reverse=True,
        )
        return Response(result)


class MarketplaceApplicationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        _ensure_staff(request.user)
        company = _user_company(request.user)
        if not company:
            raise PermissionDenied("company_not_found")

        requested_type = request.data.get("type")
        new_status = request.data.get("status")

        if new_status not in ApplicationStatus.values:
            return Response(
                {"status": "invalid_application_status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application = None
        serializer_class = None

        if requested_type in (None, "", "teacher"):
            application = TeacherApplication.objects.filter(
                pk=pk,
                company=company,
            ).first()
            if application:
                serializer_class = TeacherApplicationSerializer

        if (
            application is None
            and requested_type in (None, "", "student")
        ):
            application = StudentApplication.objects.filter(
                pk=pk,
                company=company,
            ).first()
            if application:
                serializer_class = StudentApplicationSerializer

        if application is None or serializer_class is None:
            return Response(
                {"detail": "application_not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        application.status = new_status
        application.save(update_fields=["status", "updated_at"])

        return Response(
            serializer_class(application).data
        )
