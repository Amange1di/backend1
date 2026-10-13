"""Write endpoints reject foreign-branch references before creating records."""
from django.db import transaction
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from operations_v2.models import TenantGroup, TenantHomework, TenantLibraryItem
from .permissions import authorized_tenant
from .scoping import authorized_branch


class LibraryCreateSerializer(serializers.Serializer):
    branch_id = serializers.IntegerField(min_value=1)
    title = serializers.CharField(max_length=200)
    resource_url = serializers.URLField(max_length=1000, required=False, allow_blank=True)


class HomeworkCreateSerializer(serializers.Serializer):
    group_id = serializers.IntegerField(min_value=1)
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    due_at = serializers.DateTimeField(required=False, allow_null=True)
    library_item_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)


class CompanyLibraryCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, company_id):
        data = LibraryCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        with authorized_tenant(request.user, company_id) as membership:
            if membership.role not in ("owner", "admin", "course_admin", "teacher"):
                return Response({"detail": "Library write access denied"}, status=403)
            branch = authorized_branch(membership, data.validated_data["branch_id"])
            item = TenantLibraryItem.objects.create(
                branch=branch,
                title=data.validated_data["title"],
                resource_url=data.validated_data.get("resource_url", ""),
                created_by_user_id=request.user.pk,
            )
            return Response({"id": item.pk, "branch_id": branch.pk}, status=status.HTTP_201_CREATED)


class CompanyHomeworkCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, company_id):
        data = HomeworkCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        with authorized_tenant(request.user, company_id) as membership:
            if membership.role not in ("owner", "admin", "course_admin", "teacher"):
                return Response({"detail": "Homework write access denied"}, status=403)
            values = data.validated_data
            group = TenantGroup.objects.select_related("branch").filter(
                pk=values["group_id"], branch__company_id=membership.company_id,
                branch__active=True,
            ).first()
            if group is None:
                return Response({"detail": "Group not found"}, status=404)
            authorized_branch(membership, group.branch_id)
            library_item = None
            if values.get("library_item_id") is not None:
                library_item = TenantLibraryItem.objects.filter(
                    pk=values["library_item_id"], branch_id=group.branch_id,
                ).first()
                if library_item is None:
                    return Response({"detail": "Library item not found in group branch"}, status=400)
            with transaction.atomic(using=group._state.db):
                task = TenantHomework.objects.create(
                    group=group, library_item=library_item,
                    title=values["title"],
                    description=values.get("description", ""),
                    due_at=values.get("due_at"),
                )
            return Response({"id": task.pk, "group_id": group.pk}, status=status.HTTP_201_CREATED)
