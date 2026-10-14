from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ContractTemplate, DocumentDispatch, DocumentReceipt, Group, Student, User


def can_manage(user):
    return user.is_authenticated and user.company_id and user.role in (
        User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN, User.Role.MANAGER
    )


class DocumentDispatchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not can_manage(request.user):
            raise PermissionDenied("staff_only")
        dispatches = DocumentDispatch.objects.filter(company_id=request.user.company_id).prefetch_related("receipts")
        return Response([{
            "id": d.id, "title": d.title, "created_at": d.created_at.isoformat(),
            "total": len(d.receipts.all()),
            "accepted": sum(bool(r.accepted_at) for r in d.receipts.all()),
        } for d in dispatches[:100]])

    def post(self, request):
        user = request.user
        if not can_manage(user):
            raise PermissionDenied("staff_only")
        template = get_object_or_404(ContractTemplate, pk=request.data.get("template_id"), company_id=user.company_id)
        audience = request.data.get("audience")
        student_qs = Student.objects.filter(company_id=user.company_id, archived_at__isnull=True, can_login=True, user__isnull=False, user__is_active=True)
        if audience == "student":
            student_qs = student_qs.filter(pk=request.data.get("recipient_id"))
            recipients = User.objects.filter(pk__in=student_qs.values_list("user_id", flat=True), company_id=user.company_id)
        elif audience == "group":
            group = get_object_or_404(Group, pk=request.data.get("group_id"), company_id=user.company_id)
            if user.role != User.Role.COMPANY_OWNER and not user.branches.filter(pk=group.branch_id).exists():
                raise PermissionDenied("branch_access_denied")
            student_qs = student_qs.filter(groups=group)
            recipients = User.objects.filter(pk__in=student_qs.values_list("user_id", flat=True), company_id=user.company_id)
        elif audience == "all_students":
            recipients = User.objects.filter(pk__in=student_qs.values_list("user_id", flat=True), company_id=user.company_id)
        elif audience == "teacher":
            recipients = User.objects.filter(pk=request.data.get("recipient_id"), company_id=user.company_id, role=User.Role.TEACHER, is_active=True)
        elif audience == "all_teachers":
            recipients = User.objects.filter(company_id=user.company_id, role=User.Role.TEACHER, is_active=True)
        else:
            raise ValidationError({"audience": "invalid_audience"})
        recipient_ids = list(recipients.values_list("id", flat=True).distinct()[:1001])
        if not recipient_ids:
            raise ValidationError({"recipients": "no_eligible_recipients"})
        if len(recipient_ids) > 1000:
            raise ValidationError({"recipients": "too_many_recipients"})
        if request.data.get("confirmed") is not True:
            raise ValidationError({"confirmed": "confirmation_required"})
        with transaction.atomic():
            dispatch = DocumentDispatch.objects.create(
                company_id=user.company_id, template=template,
                title=template.name, content_snapshot=template.html_content, created_by=user
            )
            DocumentReceipt.objects.bulk_create([
                DocumentReceipt(dispatch=dispatch, recipient_id=pk) for pk in recipient_ids
            ])
        return Response({"id": dispatch.id, "total": len(recipient_ids)}, status=status.HTTP_201_CREATED)


class MyDocumentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = DocumentReceipt.objects.filter(recipient=request.user, dispatch__company_id=request.user.company_id).select_related("dispatch")
        return Response([{
            "id": r.id, "title": r.dispatch.title, "content": r.dispatch.content_snapshot,
            "sent_at": r.sent_at.isoformat(), "viewed_at": r.viewed_at.isoformat() if r.viewed_at else None,
            "accepted_at": r.accepted_at.isoformat() if r.accepted_at else None,
        } for r in qs[:200]])


class DocumentReceiptActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, action):
        receipt = get_object_or_404(DocumentReceipt, pk=pk, recipient=request.user, dispatch__company_id=request.user.company_id)
        if action == "view":
            if receipt.viewed_at is None:
                receipt.viewed_at = timezone.now()
                receipt.save(update_fields=["viewed_at"])
        elif action == "accept":
            if not receipt.accepted_at:
                receipt.viewed_at = receipt.viewed_at or timezone.now()
                receipt.accepted_at = timezone.now()
                receipt.save(update_fields=["viewed_at", "accepted_at"])
        else:
            raise ValidationError({"action": "invalid_action"})
        return Response({"id": receipt.id, "viewed_at": receipt.viewed_at, "accepted_at": receipt.accepted_at})
