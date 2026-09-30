from django.conf import settings
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
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

class LoginThrottle(ScopedRateThrottle):
    scope = "login"


class RegisterThrottle(ScopedRateThrottle):
    scope = "register"

class RegisterView(APIView):
    permission_classes = [
        permissions.AllowAny
    ]
    throttle_classes = [RegisterThrottle]
    throttle_scope = "register"

    def post(self, request):
        if (
            request.user.is_authenticated
            and request.user.role
            == User.Role.ADMIN
        ):
            return Response(
                {
                    "detail": (
                        "Admins can only create "
                        "course admins."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            request.user.is_authenticated
            and request.user.role
            == User.Role.TEACHER
        ):
            return Response(
                {
                    "detail": (
                        "Teachers cannot create users."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            request.user.is_authenticated
            and request.user.role
            == User.Role.MANAGER
        ):
            return Response(
                {
                    "detail": (
                        "Managers cannot create users."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            request.user.is_authenticated
            and request.user.role
            == User.Role.STUDENT
        ):
            return Response(
                {
                    "detail": (
                        "Students cannot create users."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = RegisterSerializer(
            data=request.data
        )
        serializer.is_valid(
            raise_exception=True
        )
        requested_role = (
            serializer.validated_data.get(
                "role"
            )
        )

        if (
            (
                not request.user.is_authenticated
                or request.user.role
                != User.Role.COURSE_ADMIN
            )
            and requested_role
            == User.Role.MANAGER
        ):
            return Response(
                {
                    "detail": (
                        "Managers can only be created "
                        "by course admins."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            request.user.is_authenticated
            and request.user.role
            == User.Role.COURSE_ADMIN
        ):
            if requested_role not in (
                User.Role.MANAGER,
                User.Role.TEACHER,
            ):
                return Response(
                    {
                        "detail": (
                            "Course admins can only create "
                            "teachers or managers."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if not request.user.company_id:
                return Response(
                    {"detail": "Company is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if requested_role == User.Role.MANAGER:
                if not request.user.can_create_manager():
                    return Response(
                        {
                            "detail": (
                                "Manager limit reached. "
                                f"Maximum: "
                                f"{request.user.max_managers}, "
                                f"Current: "
                                f"{request.user.get_managers_count()}"
                            )
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

                user = serializer.save(
                    force_role=User.Role.MANAGER,
                    created_by=request.user,
                    company=request.user.company,
                )
            else:
                user = serializer.save(
                    force_role=User.Role.TEACHER,
                    created_by=request.user,
                    company=request.user.company,
                )
        else:
            user = serializer.save(
                force_role=User.Role.TEACHER,
                company=None,
                created_by=None,
                max_managers=0,
                max_pages=1,
                max_blocks=7,
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

@method_decorator(
    ensure_csrf_cookie,
    name="dispatch",
)
class LoginView(APIView):
    permission_classes = [
        permissions.AllowAny
    ]
    throttle_classes = [LoginThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data
        )
        serializer.is_valid(
            raise_exception=True
        )
        user = serializer.validated_data[
            "user"
        ]
        token, _ = Token.objects.get_or_create(
            user=user
        )

        response = Response(
            {
                "token": token.key,
                "user": UserSerializer(user).data,
            }
        )
        response.set_cookie(
            key="csrftoken",
            value=get_token(request),
            max_age=60 * 60 * 24 * 30,
            httponly=False,
            samesite="Lax",
            secure=settings.DEBUG is False,
        )
        response.set_cookie(
            key="token",
            value=token.key,
            max_age=60 * 60 * 24 * 30,
            httponly=True,
            samesite="Lax",
            secure=not settings.DEBUG,
            path="/",
        )
        return response

class LogoutView(APIView):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass

        response = Response(
            {
                "detail": (
                    "Successfully logged out."
                )
            }
        )
        response.delete_cookie("csrftoken")
        response.delete_cookie(
            "token",
            path="/",
        )
        return response

class MeView(APIView):
    def get(self, request):
        data = UserSerializer(
            request.user
        ).data

        if (
            request.user.is_superuser
            and data.get("role")
            != User.Role.ADMIN
        ):
            data["role"] = User.Role.ADMIN

        if (
            request.user.role
            == User.Role.STUDENT
        ):
            data["student_id"] = (
                request.user.student_profile.id
                if (
                    hasattr(
                        request.user,
                        "student_profile",
                    )
                    and request.user.student_profile
                )
                else None
            )

        return Response(
            {
                **data,
                "support_telegram": (
                    resolve_support_telegram(
                        request.user
                    )
                ),
            }
        )

