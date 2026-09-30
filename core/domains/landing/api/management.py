import bleach

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from core.models import (
    LandingHeaderLink,
    LandingPage,
    TrialLead,
    User,
)
from core.domains.trials.serializers import TrialLeadSerializer

from ..serializers import (
    LandingHeaderLinkSerializer,
    LandingPageSerializer,
    LandingPublicPageSerializer,
)
from ..services import validate_landing_page_for_publication

class LandingPageViewSet(viewsets.ModelViewSet):
    queryset = LandingPage.objects.all().prefetch_related(
        "sections"
    )
    serializer_class = LandingPageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(
                company=user.company
            )

        if (
            user.role == User.Role.ADMIN
            or user.is_superuser
        ):
            status_filter = (
                self.request.query_params.get(
                    "status",
                    "",
                ).strip()
            )
            if status_filter:
                queryset = queryset.filter(
                    status=status_filter
                )

            company_name = (
                self.request.query_params.get(
                    "company_name",
                    "",
                ).strip()
            )
            if company_name:
                queryset = queryset.filter(
                    company=company_name
                )

            return queryset

        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user

        if user.role != User.Role.COURSE_ADMIN:
            raise PermissionDenied(
                "Only course admins can create landing pages."
            )

        if not user.can_create_landing_page():
            raise PermissionDenied(
                (
                    "Landing pages limit reached. "
                    f"Maximum: {user.max_pages}, "
                    f"Current: {user.get_pages_count()}"
                )
            )

        serializer.save(
            owner=user,
            company=user.company,
        )

    def perform_update(self, serializer):
        page = self.get_object()
        user = self.request.user

        if user.role == User.Role.COURSE_ADMIN:
            if page.company != user.company:
                raise PermissionDenied(
                    "Not allowed for this landing page."
                )
            serializer.save()
            return

        if (
            user.role == User.Role.ADMIN
            or user.is_superuser
        ):
            serializer.save()
            return

        raise PermissionDenied("Not allowed.")

    def destroy(self, request, *args, **kwargs):
        page = self.get_object()
        user = request.user

        if (
            user.role == User.Role.COURSE_ADMIN
            and page.company != user.company
        ):
            raise PermissionDenied(
                "Not allowed for this landing page."
            )

        if (
            user.role
            not in (
                User.Role.COURSE_ADMIN,
                User.Role.ADMIN,
            )
            and not user.is_superuser
        ):
            raise PermissionDenied(
                "Not allowed to delete this landing page."
            )

        return super().destroy(
            request,
            *args,
            **kwargs,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="submit",
    )
    def submit(self, request, pk=None):
        page = self.get_object()
        user = request.user

        if (
            user.role != User.Role.COURSE_ADMIN
            or page.company != user.company
        ):
            raise PermissionDenied(
                (
                    "Only the owning course admin can "
                    "submit this landing page."
                )
            )

        if page.status == LandingPage.Status.PENDING:
            raise PermissionDenied(
                (
                    "This landing page is already "
                    "pending moderation."
                )
            )

        validate_landing_page_for_publication(
            page,
            user,
        )
        page.status = LandingPage.Status.PENDING
        page.moderation_comment = ""
        page.submitted_at = timezone.now()
        page.save(
            update_fields=[
                "status",
                "moderation_comment",
                "submitted_at",
                "updated_at",
            ]
        )

        return Response(
            self.get_serializer(page).data
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="approve",
    )
    def approve(self, request, pk=None):
        page = self.get_object()
        user = request.user

        if (
            user.role != User.Role.ADMIN
            and not user.is_superuser
        ):
            raise PermissionDenied(
                "Only admins can approve landing pages."
            )

        if page.status != LandingPage.Status.PENDING:
            raise PermissionDenied(
                (
                    "Only pending landing pages "
                    "can be approved."
                )
            )

        validate_landing_page_for_publication(
            page,
            page.owner,
        )
        page.status = LandingPage.Status.ACTIVE
        page.moderation_comment = ""
        page.moderated_at = timezone.now()
        page.moderated_by = user
        page.published_at = (
            page.published_at
            or timezone.now()
        )
        page.save(
            update_fields=[
                "status",
                "moderation_comment",
                "moderated_at",
                "moderated_by",
                "published_at",
                "updated_at",
            ]
        )

        return Response(
            self.get_serializer(page).data
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="reject",
    )
    def reject(self, request, pk=None):
        page = self.get_object()
        user = request.user

        if (
            user.role != User.Role.ADMIN
            and not user.is_superuser
        ):
            raise PermissionDenied(
                "Only admins can reject landing pages."
            )

        if page.status != LandingPage.Status.PENDING:
            raise PermissionDenied(
                (
                    "Only pending landing pages "
                    "can be rejected."
                )
            )

        comment = (
            request.data.get("comment")
            or ""
        ).strip()
        if not comment:
            return Response(
                {
                    "detail": (
                        "Moderation comment is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        page.status = LandingPage.Status.REJECTED
        page.moderation_comment = comment
        page.moderated_at = timezone.now()
        page.moderated_by = user
        page.save(
            update_fields=[
                "status",
                "moderation_comment",
                "moderated_at",
                "moderated_by",
                "updated_at",
            ]
        )

        return Response(
            self.get_serializer(page).data
        )

class LandingHeaderLinkViewSet(
    viewsets.ModelViewSet
):
    queryset = (
        LandingHeaderLink.objects.all()
        .select_related("target_page")
    )
    serializer_class = LandingHeaderLinkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(
                company=user.company
            )

        if (
            user.role == User.Role.ADMIN
            or user.is_superuser
        ):
            company_name = (
                self.request.query_params.get(
                    "company_name",
                    "",
                ).strip()
            )
            if company_name:
                queryset = queryset.filter(
                    company=company_name
                )
            return queryset

        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user

        if user.role != User.Role.COURSE_ADMIN:
            raise PermissionDenied(
                (
                    "Only course admins can manage "
                    "landing header links."
                )
            )

        serializer.save(company=user.company)

    def perform_update(self, serializer):
        link = self.get_object()
        user = self.request.user

        if (
            user.role != User.Role.COURSE_ADMIN
            or link.company != user.company
        ):
            raise PermissionDenied(
                (
                    "Only the owning course admin can "
                    "update this header link."
                )
            )

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        link = self.get_object()

        if (
            request.user.role
            != User.Role.COURSE_ADMIN
            or link.company
            != request.user.company
        ):
            raise PermissionDenied(
                (
                    "Only the owning course admin can "
                    "delete this header link."
                )
            )

        return super().destroy(
            request,
            *args,
            **kwargs,
        )

