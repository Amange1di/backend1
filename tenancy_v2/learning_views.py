from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from operations_v2.models import TenantHomework, TenantLibraryItem
from .permissions import authorized_tenant
from .scoping import scope_to_membership


class CompanyLibraryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        with authorized_tenant(request.user, company_id) as membership:
            items = scope_to_membership(TenantLibraryItem.objects.all(), membership)
            return Response([
                {"id": item.id, "branch_id": item.branch_id,
                 "title": item.title, "resource_url": item.resource_url}
                for item in items.order_by("-id")[:100]
            ])


class CompanyHomeworkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        with authorized_tenant(request.user, company_id) as membership:
            tasks = scope_to_membership(
                TenantHomework.objects.all(), membership, "group__branch_id"
            )
            return Response([
                {"id": task.id, "group_id": task.group_id,
                 "title": task.title, "description": task.description,
                 "due_at": task.due_at.isoformat() if task.due_at else None}
                for task in tasks.order_by("-id")[:100]
            ])
