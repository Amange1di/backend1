from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from operations_v2.models import TenantLesson
from .permissions import authorized_tenant
from .scoping import authorized_branch, scope_to_membership


class CompanyScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        with authorized_tenant(request.user, company_id) as membership:
            lessons = scope_to_membership(
                TenantLesson.objects.all(), membership, "group__branch_id"
            )
            branch = request.query_params.get("branch_id")
            if branch is not None:
                try:
                    branch_id = int(branch)
                except (ValueError, TypeError):
                    return Response({"detail": "Invalid branch_id"}, status=400)
                authorized_branch(membership, branch_id)
                lessons = lessons.filter(group__branch_id=branch_id)
            return Response([
                {"id": item.id, "group_id": item.group_id,
                 "starts_at": item.starts_at.isoformat(),
                 "ends_at": item.ends_at.isoformat(),
                 "room_name": item.room_name}
                for item in lessons.order_by("starts_at", "id")[:100]
            ])
