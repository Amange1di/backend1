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

class PublicSubmitThrottle(AnonRateThrottle):
    rate = "10/minute"

class PublicReadThrottle(AnonRateThrottle):
    rate = "60/minute"

class PublicLandingDetailView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [
        AnonRateThrottle,
        PublicReadThrottle,
    ]

    def get(self, request, slug: str):
        page = get_object_or_404(
            LandingPage.objects.prefetch_related(
                "sections"
            ),
            slug=slug,
            status=LandingPage.Status.ACTIVE,
        )
        return Response(
            LandingPublicPageSerializer(
                page,
                context={"request": request},
            ).data
        )

class PublicLandingLeadCreateView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [
        AnonRateThrottle,
        PublicSubmitThrottle,
    ]
    parser_classes = [JSONParser]

    def post(self, request, slug: str):
        page = get_object_or_404(
            LandingPage,
            slug=slug,
            status=LandingPage.Status.ACTIVE,
        )

        full_name = (
            request.data.get("full_name")
            or ""
        ).strip()
        phone = (
            request.data.get("phone")
            or ""
        ).strip()

        if not full_name or not phone:
            return Response(
                {
                    "detail": (
                        "full_name_phone_required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        safe_full_name = bleach.clean(
            full_name,
            tags=[],
            strip=True,
        )[:200]
        safe_course_interest = bleach.clean(
            (
                request.data.get(
                    "course_interest"
                )
                or ""
            ).strip(),
            tags=[],
            strip=True,
        )[:200]
        safe_comment = bleach.clean(
            (
                request.data.get("comment")
                or ""
            ).strip(),
            tags=[],
            strip=True,
        )[:1000]

        lead = TrialLead.objects.create(
            full_name=safe_full_name,
            phone=phone,
            course_interest=safe_course_interest,
            source=f"landing:{page.slug}",
            comment=safe_comment,
            company=page.company,
        )

        return Response(
            TrialLeadSerializer(lead).data,
            status=status.HTTP_201_CREATED,
        )

