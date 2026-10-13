"""Authenticated company discovery for the isolated API v2."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import available_companies, resolve_membership


class MyCompaniesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = available_companies(request.user)
        return Response([
            {
                'id': membership.company_id,
                'name': membership.company.name,
                'slug': membership.company.slug,
                'role': membership.role,
            }
            for membership in memberships
        ])


class CompanyAccessView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        membership = resolve_membership(request.user, company_id)
        return Response({
            'id': membership.company_id,
            'name': membership.company.name,
            'role': membership.role,
        })
