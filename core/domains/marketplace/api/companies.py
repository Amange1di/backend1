from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    Company,
    JobVacancy,
    PublicCourse,
    Transaction,
    User,
)

from ..serializers import (
    CompanySerializer,
    JobVacancyDetailSerializer,
    JobVacancySerializer,
    PublicCourseSerializer,
)
from ..services import (
    BOOST_COST,
    URGENT_COST,
    charge_promotion,
    mark_urgent,
    promote_item,
)

class MarketplaceCompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Company.objects.filter(
            is_active=True
        ).order_by("-created_at")
        user = self.request.user

        if user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(owner=user)

        if user.role == User.Role.MANAGER:
            if user.company:
                return queryset.filter(
                    owner__company=user.company
                )
            return queryset.none()

        if user.role in (
            User.Role.TEACHER,
            User.Role.STUDENT,
        ):
            return queryset.none()

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            raise PermissionDenied(
                "Only course admins and managers can create companies."
            )

        owner = (
            user
            if user.role == User.Role.COURSE_ADMIN
            else user.created_by
        )
        serializer.save(owner=owner)

