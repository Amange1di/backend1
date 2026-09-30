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

from ..services import (
    ensure_student_access_allowed,
    resolve_support_telegram,
)

class StudentLoginView(APIView):
    permission_classes = [
        permissions.AllowAny
    ]

    def post(self, request):
        serializer = (
            StudentIdentityLoginSerializer(
                data=request.data
            )
        )
        serializer.is_valid(
            raise_exception=True
        )

        phone_number = (
            serializer.validated_data[
                "phone_number"
            ].strip()
        )
        password = (
            serializer.validated_data.get(
                "password",
                "",
            )
        )
        normalized_phone = normalize_phone(
            phone_number
        )

        candidates = [
            student
            for student
            in (
                Student.objects
                .select_related("user")
                .all()
                .order_by("id")
            )
            if normalize_phone(
                student.phone
            )
            == normalized_phone
        ]

        if not candidates:
            return Response(
                {
                    "detail": (
                        "Invalid student credentials."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        accessible_students = []

        for student in candidates:
            if not student.user:
                sync_student_user(student)
                student.refresh_from_db()

            try:
                ensure_student_access_allowed(
                    student
                )
                accessible_students.append(
                    student
                )
            except PermissionDenied:
                continue

        if not accessible_students:
            return Response(
                {
                    "detail": (
                        "Student access is disabled."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if len(accessible_students) > 1:
            return Response(
                {
                    "detail": (
                        "Multiple student accounts "
                        "matched. Contact your "
                        "administrator."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        student = accessible_students[0]
        user = student.user
        token, _ = Token.objects.get_or_create(
            user=user
        )

        if (
            user.must_set_password
            or not user.has_usable_password()
        ):
            return Response(
                {
                    "token": token.key,
                    "user": (
                        UserSerializer(user).data
                    ),
                    "student": (
                        StudentSerializer(
                            student,
                            context={
                                "request": request
                            },
                        ).data
                    ),
                    "requires_password_setup": True,
                }
            )

        if not password:
            return Response(
                {
                    "detail": (
                        "Password is required."
                    ),
                    "code": "password_required",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(password):
            return Response(
                {
                    "detail": (
                        "Invalid student credentials."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "token": token.key,
                "user": UserSerializer(user).data,
                "student": StudentSerializer(
                    student,
                    context={
                        "request": request
                    },
                ).data,
                "requires_password_setup": False,
            }
        )

class StudentSetPasswordView(APIView):
    def post(self, request):
        if (
            request.user.role
            != User.Role.STUDENT
        ):
            raise PermissionDenied(
                (
                    "Only students can set "
                    "this password."
                )
            )

        serializer = (
            StudentSetPasswordSerializer(
                data=request.data
            )
        )
        serializer.is_valid(
            raise_exception=True
        )

        request.user.set_password(
            serializer.validated_data[
                "password"
            ]
        )
        request.user.must_set_password = False
        request.user.save(
            update_fields=[
                "password",
                "must_set_password",
            ]
        )
        token, _ = Token.objects.get_or_create(
            user=request.user
        )

        return Response(
            {
                "token": token.key,
                "user": UserSerializer(
                    request.user
                ).data,
            }
        )

class StudentProfileView(APIView):
    def get(self, request):
        if (
            request.user.role
            != User.Role.STUDENT
        ):
            raise PermissionDenied(
                (
                    "Only students can access "
                    "this profile."
                )
            )

        student = getattr(
            request.user,
            "student_profile",
            None,
        )
        if not student:
            return Response(
                {
                    "detail": (
                        "Student profile not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        ensure_student_access_allowed(
            student
        )

        return Response(
            {
                "id": student.id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "phone": student.phone,
                "telegram": student.telegram,
                "company_name": (
                    student.company.name
                    if student.company
                    else ""
                ),
                "can_login": student.can_login,
                "must_set_password": (
                    request.user.must_set_password
                ),
            }
        )

    def patch(self, request):
        if (
            request.user.role
            != User.Role.STUDENT
        ):
            raise PermissionDenied(
                (
                    "Only students can update "
                    "this profile."
                )
            )

        student = getattr(
            request.user,
            "student_profile",
            None,
        )
        if not student:
            return Response(
                {
                    "detail": (
                        "Student profile not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        ensure_student_access_allowed(
            student
        )
        serializer = StudentProfileSerializer(
            data=request.data,
            partial=True,
        )
        serializer.is_valid(
            raise_exception=True
        )

        student_fields = []
        user_fields = []

        phone = (
            serializer.validated_data.get(
                "phone"
            )
        )
        telegram = (
            serializer.validated_data.get(
                "telegram"
            )
        )
        password = (
            serializer.validated_data.get(
                "password"
            )
        )

        if (
            phone is not None
            and phone != student.phone
        ):
            student.phone = phone
            request.user.phone = phone
            student_fields.append("phone")
            user_fields.append("phone")

        if (
            telegram is not None
            and telegram != student.telegram
        ):
            student.telegram = telegram
            request.user.telegram = telegram
            student_fields.append("telegram")
            user_fields.append("telegram")

        if student_fields:
            student.save(
                update_fields=student_fields
            )

        if password:
            request.user.set_password(password)
            request.user.must_set_password = False
            user_fields.extend(
                [
                    "password",
                    "must_set_password",
                ]
            )

        if user_fields:
            request.user.save(
                update_fields=list(
                    dict.fromkeys(user_fields)
                )
            )

        return self.get(request)

