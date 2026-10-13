from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from operations_v2.models import TenantAttendance
from .permissions import authorized_tenant
from .scoping import authorized_branch, scope_to_membership


class CompanyAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        with authorized_tenant(request.user, company_id) as membership:
            records = scope_to_membership(
                TenantAttendance.objects.all(), membership, "group__branch_id"
            )
            branch = request.query_params.get("branch_id")
            if branch is not None:
                try:
                    branch_id = int(branch)
                except (ValueError, TypeError):
                    return Response({"detail": "Invalid branch_id"}, status=400)
                authorized_branch(membership, branch_id)
                records = records.filter(group__branch_id=branch_id)
            return Response([
                {"id": item.id, "group_id": item.group_id,
                 "student_id": item.student_id, "date": item.date.isoformat(),
                 "present": item.present}
                for item in records.order_by("-date", "id")[:100]
            ])
