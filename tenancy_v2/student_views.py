from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from operations_v2.models import TenantStudent
from .permissions import authorized_tenant
from .scoping import scope_to_membership, authorized_branch


class CompanyStudentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        with authorized_tenant(request.user, company_id) as membership:
            queryset = scope_to_membership(TenantStudent.objects.all(), membership)
            branch = request.query_params.get("branch_id")
            if branch is not None:
                try:
                    branch_id = int(branch)
                except (TypeError, ValueError):
                    return Response({"detail": "Invalid branch_id"}, status=400)
                authorized_branch(membership, branch_id)
                queryset = queryset.filter(branch_id=branch_id)
            return Response([
                {"id": item.id, "first_name": item.first_name,
                 "last_name": item.last_name, "branch_id": item.branch_id}
                for item in queryset.order_by("id")[:100]
            ])
