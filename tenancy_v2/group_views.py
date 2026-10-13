from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from operations_v2.models import TenantGroup
from .permissions import authorized_tenant
from .scoping import authorized_branch, scope_to_membership


class CompanyGroupsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        with authorized_tenant(request.user, company_id) as membership:
            groups = scope_to_membership(TenantGroup.objects.all(), membership)
            branch = request.query_params.get("branch_id")
            if branch is not None:
                try:
                    branch_id = int(branch)
                except (ValueError, TypeError):
                    return Response({"detail": "Invalid branch_id"}, status=400)
                authorized_branch(membership, branch_id)
                groups = groups.filter(branch_id=branch_id)
            return Response([
                {"id": item.id, "name": item.name,
                 "branch_id": item.branch_id, "teacher_user_id": item.teacher_user_id}
                for item in groups.order_by("id")[:100]
            ])
