from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from operations_v2.models import TenantFinanceEntry
from .permissions import authorized_tenant
from .scoping import authorized_branch, scope_to_membership


class CompanyFinanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        with authorized_tenant(request.user, company_id) as membership:
            if membership.role not in ("owner", "admin", "course_admin"):
                return Response({"detail": "Finance access denied"}, status=403)
            entries = scope_to_membership(TenantFinanceEntry.objects.all(), membership)
            branch = request.query_params.get("branch_id")
            if branch is not None:
                try:
                    branch_id = int(branch)
                except (ValueError, TypeError):
                    return Response({"detail": "Invalid branch_id"}, status=400)
                authorized_branch(membership, branch_id)
                entries = entries.filter(branch_id=branch_id)
            return Response([
                {"id": item.id, "branch_id": item.branch_id,
                 "kind": item.kind, "amount": str(item.amount),
                 "occurred_on": item.occurred_on.isoformat(),
                 "description": item.description}
                for item in entries.order_by("-occurred_on", "-id")[:100]
            ])
