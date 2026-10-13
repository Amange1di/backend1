from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from operations_v2.models import TenantBranch
from .permissions import authorized_tenant


class CompanyBranchesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        with authorized_tenant(request.user, company_id) as membership:
            branches = TenantBranch.objects.filter(
                company_id=membership.company_id,
                active=True,
            ).order_by("name")
            if membership.role not in ("owner", "admin"):
                if membership.branch_id is None:
                    branches = branches.none()
                else:
                    branches = branches.filter(id=membership.branch_id)
            return Response([
                {"id": item.id, "name": item.name, "company_id": item.company_id}
                for item in branches
            ])
