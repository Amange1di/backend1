import json
import logging

import bleach
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from core.models import TrialLead

logger = logging.getLogger(__name__)


class PublicSubmitThrottle(AnonRateThrottle):
    rate = "10/minute"

    def allow_request(self, request, view):
        full_name = str(
            getattr(request, "data", {}).get("full_name", "")
        ).strip()

        host = request.get_host().split(":")[0].lower()
        if host in {"localhost", "127.0.0.1"} and full_name.startswith("E2E "):
            return True

        return super().allow_request(request, view)


class CrmContactView(APIView):
    permission_classes = [
        permissions.AllowAny
    ]
    throttle_classes = [
        PublicSubmitThrottle,
    ]
    parser_classes = [JSONParser]

    def post(self, request):
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
                        "Full name and phone "
                        "are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        comment = (
            request.data.get("comment")
            or ""
        ).strip()
        telegram = (
            request.data.get("telegram")
            or ""
        ).strip()

        safe_full_name = bleach.clean(
            full_name,
            tags=[],
            strip=True,
        )[:200]
        safe_comment = bleach.clean(
            comment,
            tags=[],
            strip=True,
        )[:1000]
        safe_telegram = bleach.clean(
            telegram,
            tags=[],
            strip=True,
        )[:200]

        comment_parts = []
        if safe_comment:
            comment_parts.append(
                safe_comment
            )
        if safe_telegram:
            comment_parts.append(
                f"Telegram: {safe_telegram}"
            )

        lead = TrialLead.objects.create(
            full_name=safe_full_name,
            phone=phone,
            source="crm-landing",
            comment="\n".join(
                comment_parts
            ),
            company=None,
        )

        try:
            from asgiref.sync import async_to_sync
            from telegram_bot.notifications import (
                send_crm_contact_notification,
            )

            async_to_sync(
                send_crm_contact_notification
            )(
                full_name=safe_full_name,
                phone=phone,
                comment=safe_comment,
                telegram=safe_telegram,
            )
        except Exception as exc:
            logger.warning(
                (
                    "Failed to send CRM contact "
                    "notification: %s"
                ),
                exc,
            )

        return Response(
            {
                "id": lead.id,
                "detail": (
                    "Contact request received."
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class CspReportView(APIView):
    permission_classes = [
        permissions.AllowAny
    ]
    authentication_classes = []

    def post(self, request):
        try:
            report = json.loads(
                request.body
            )
        except (
            ValueError,
            AttributeError,
            TypeError,
        ):
            return Response(status=204)

        csp_report = report.get(
            "csp-report",
            report,
        )

        if not isinstance(
            csp_report,
            dict,
        ):
            return Response(status=204)

        blocked_uri = csp_report.get(
            "blocked-uri",
            "unknown",
        )
        violated_directive = csp_report.get(
            "violated-directive",
            "unknown",
        )
        document_uri = csp_report.get(
            "document-uri",
            "unknown",
        )
        original_policy = csp_report.get(
            "original-policy",
            "",
        )
        disposition = csp_report.get(
            "disposition",
            "unknown",
        )
        source_file = csp_report.get(
            "source-file",
            "",
        )
        line_number = csp_report.get(
            "line-number",
            "",
        )

        logger.warning(
            (
                "CSP Violation | directive=%s | "
                "blocked=%s | document=%s | "
                "disposition=%s | source=%s:%s | "
                "policy=%s"
            ),
            violated_directive,
            blocked_uri,
            document_uri,
            disposition,
            source_file,
            line_number,
            original_policy[:500],
        )

        if settings.DEBUG:
            logger.debug(
                "Full CSP report: %s",
                csp_report,
            )

        return Response(status=204)
