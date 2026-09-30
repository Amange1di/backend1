from django.conf import settings
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from core.models import (
    Company,
    CompanyBalance,
    CompanyCategory,
    CompanyCity,
    Student,
    User,
)
from core.permissions import IsAdmin
from core.domains.students.serializers import StudentSerializer
from core.domains.students.services import (
    normalize_phone,
    sync_student_user,
)
from core.domains.users.serializers import (
    CourseAdminUpdateSerializer,
    LoginSerializer,
    RegisterSerializer,
    StudentIdentityLoginSerializer,
    StudentProfileSerializer,
    StudentSetPasswordSerializer,
    UserSerializer,
)

from .services import (
    ensure_student_access_allowed,
    resolve_support_telegram,
)

class CourseAdminCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        admins = User.objects.filter(
            role=User.Role.COURSE_ADMIN
        ).order_by("-date_joined")

        return Response(
            UserSerializer(
                admins,
                many=True,
            ).data
        )

    def post(self, request):
        serializer = RegisterSerializer(
            data=request.data,
            context={
                "force_role": (
                    User.Role.COURSE_ADMIN
                )
            },
        )
        serializer.is_valid(
            raise_exception=True
        )

        company_name = (
            serializer.validated_data.get(
                "company_name",
                "",
            ).strip()
        )
        phone = (
            serializer.validated_data.get(
                "phone",
                "",
            ).strip()
        )
        address = (
            serializer.validated_data.get(
                "address",
                "",
            ).strip()
        )
        max_managers = (
            serializer.validated_data.get(
                "max_managers",
                0,
            )
            or 0
        )

        if not company_name:
            return Response(
                {
                    "detail": (
                        "Company name is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not phone or not address:
            return Response(
                {
                    "detail": (
                        "Phone and address are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if max_managers < 0:
            return Response(
                {
                    "detail": (
                        "Manager limit must be "
                        "0 or more."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save(
            created_by=request.user,
            company=None,
            max_managers=max_managers,
        )

        company = Company.objects.create(
            name=company_name,
            owner=user,
            category=CompanyCategory.OTHER,
            city=CompanyCity.ONLINE,
            description=(
                f"Company for {company_name}"
            ),
            is_active=True,
        )

        user.company = company
        user.save()

        CompanyBalance.objects.create(
            company=company,
            balance=0,
        )

        token, _ = Token.objects.get_or_create(
            user=user
        )
        return Response(
            {
                "token": token.key,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )

class CourseAdminDetailView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, pk: int):
        admin = get_object_or_404(
            User,
            pk=pk,
            role=User.Role.COURSE_ADMIN,
        )
        return Response(
            UserSerializer(admin).data
        )

    def patch(self, request, pk: int):
        admin = get_object_or_404(
            User,
            pk=pk,
            role=User.Role.COURSE_ADMIN,
        )
        serializer = (
            CourseAdminUpdateSerializer(
                admin,
                data=request.data,
                partial=True,
            )
        )
        serializer.is_valid(
            raise_exception=True
        )
        admin = serializer.save()

        return Response(
            UserSerializer(admin).data
        )

    def delete(self, request, pk: int):
        admin = get_object_or_404(
            User,
            pk=pk,
            role=User.Role.COURSE_ADMIN,
        )
        admin.delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

