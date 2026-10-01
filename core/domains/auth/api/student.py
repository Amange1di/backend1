from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import User
from core.domains.users.serializers import StudentProfileSerializer

from ..services import ensure_student_access_allowed


class StudentProfileView(APIView):
    @staticmethod
    def _get_student_profile(user):
        profiles = user.student_profiles.filter(
            archived_at__isnull=True
        ).order_by("created_at")
        if user.company_id:
            profile = profiles.filter(
                company_id=user.company_id
            ).first()
            if profile:
                return profile
        return profiles.first()

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

        student = self._get_student_profile(
            request.user
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

        student = self._get_student_profile(
            request.user
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

        password_changed = bool(password)
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

        if password_changed:
            Token.objects.filter(
                user=request.user
            ).delete()

        return self.get(request)

