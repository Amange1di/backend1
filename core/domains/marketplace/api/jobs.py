from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    Company,
    JobVacancy,
    PublicCourse,
    Transaction,
    User,
)

from ..serializers import (
    CompanySerializer,
    JobVacancyDetailSerializer,
    JobVacancySerializer,
    PublicCourseSerializer,
)
from ..services import (
    BOOST_COST,
    URGENT_COST,
    charge_promotion,
    mark_urgent,
    promote_item,
)

class MarketplaceJobViewSet(viewsets.ModelViewSet):
    queryset = JobVacancy.objects.all().order_by(
        "-is_promoted",
        "-created_at",
    )
    serializer_class = JobVacancySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = JobVacancy.objects.all()
        user = self.request.user

        if not user.is_authenticated:
            return queryset.filter(is_active=True)

        if user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(
                company__owner=user
            )

        if user.role == User.Role.MANAGER:
            if user.company:
                return queryset.filter(
                    company=user.company
                )
            return queryset.none()

        return queryset.filter(is_active=True)

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            raise PermissionDenied(
                "Only course admins and managers can create jobs."
            )

        company = user.company
        if not company and user.role == User.Role.MANAGER:
            company = getattr(
                getattr(user, "created_by", None),
                "company",
                None,
            )

        if not company:
            raise PermissionDenied(
                "No company found. Create a company first."
            )

        serializer.save(company=company)

    def perform_update(self, serializer):
        user = self.request.user
        job = self.get_object()

        if (
            user.role == User.Role.COURSE_ADMIN
            and job.company.owner != user
        ):
            raise PermissionDenied(
                "Not allowed for this job."
            )

        if (
            user.role == User.Role.MANAGER
            and job.company != user.company
        ):
            raise PermissionDenied(
                "Not allowed for this job."
            )

        serializer.save()

class MyJobsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role not in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            return Response(
                {
                    "detail": (
                        "Доступно только для course_admin и manager."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user.company:
            return Response([])

        jobs = JobVacancy.objects.filter(
            company=user.company,
        )

        data = []
        for job in jobs:
            job_data = JobVacancySerializer(
                job
            ).data
            job_data["views"] = getattr(
                job,
                "views",
                0,
            )
            job_data["applications"] = getattr(
                job,
                "applications_count",
                0,
            )
            job_data["status"] = (
                "approved"
                if job.is_active
                else "draft"
            )
            data.append(job_data)

        return Response(data)

class BoostJobView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        if user.role not in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            return Response(
                {
                    "detail": (
                        "Доступно только для course_admin и manager."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        job = get_object_or_404(
            JobVacancy,
            pk=pk,
        )

        if (
            user.role == User.Role.COURSE_ADMIN
            and job.company.owner != user
        ):
            return Response(
                {"detail": "Недостаточно прав."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            user.role == User.Role.MANAGER
            and job.company != user.company
        ):
            return Response(
                {"detail": "Недостаточно прав."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            job.is_promoted
            and job.promoted_until
            and job.promoted_until > timezone.now()
        ):
            return Response(
                {"detail": "Эта вакансия уже находится в ТОП."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not charge_promotion(
            company=user.company,
            amount=BOOST_COST,
            reason=(
                f"Продвижение вакансии: {job.title}"
            ),
            transaction_type=(
                Transaction.Type.WITHDRAWAL
            ),
            user=user,
        ):
            return Response(
                {
                    "detail": (
                        f"Недостаточно средств. Требуется {BOOST_COST} eC."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        promote_item(job, days=7)
        return Response(
            JobVacancySerializer(job).data
        )

class UrgentJobView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        if user.role not in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            return Response(
                {"detail": "Доступно только для course_admin и manager."},
                status=status.HTTP_403_FORBIDDEN,
            )

        job = get_object_or_404(
            JobVacancy,
            pk=pk,
        )

        if (
            user.role == User.Role.COURSE_ADMIN
            and job.company.owner != user
        ):
            return Response(
                {"detail": "Недостаточно прав."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            user.role == User.Role.MANAGER
            and job.company != user.company
        ):
            return Response(
                {"detail": "Недостаточно прав."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            days = int(request.data.get("days", 3))
        except (TypeError, ValueError):
            return Response(
                {"detail": "Некорректный срок продвижения."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if days < 3 or days > 30 or days % 3 != 0:
            return Response(
                {"detail": "Срок должен быть от 3 до 30 дней с шагом 3 дня."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        blocks = days // 3
        cost = URGENT_COST * blocks

        if not charge_promotion(
            company=user.company,
            amount=cost,
            reason=(
                f"Срочное продвижение вакансии: "
                f"{job.title} · {days} дн."
            ),
            transaction_type=(
                Transaction.Type.WITHDRAWAL
            ),
            user=user,
        ):
            return Response(
                {
                    "detail": (
                        f"Недостаточно средств. Требуется {cost} eC."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        mark_urgent(job, days=days)
        data = JobVacancySerializer(job).data
        data["promotion_days"] = days
        data["promotion_cost"] = cost
        return Response(data)

class PublicJobViewSet(
    viewsets.ReadOnlyModelViewSet
):
    queryset = (
        JobVacancy.objects.filter(
            is_active=True
        )
        .order_by(
            "-is_promoted",
            "-created_at",
        )
        .select_related("company")
        .prefetch_related(
            "company__landing_pages"
        )
    )
    serializer_class = JobVacancySerializer
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return JobVacancyDetailSerializer
        return JobVacancySerializer

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .annotate(
                promotion_rank=models.Case(
                    models.When(
                        promoted_until__gt=timezone.now(),
                        then=models.Value(1),
                    ),
                    default=models.Value(0),
                    output_field=models.IntegerField(),
                )
            )
            .order_by(
                "-promotion_rank",
                "-created_at",
            )
        )

        category = self.request.query_params.get(
            "category"
        )
        if category:
            queryset = queryset.filter(
                category=category
            )

        city = self.request.query_params.get(
            "city"
        )
        if city:
            queryset = queryset.filter(
                city=city
            )

        schedule = self.request.query_params.get(
            "schedule"
        )
        if schedule:
            queryset = queryset.filter(
                schedule__icontains=schedule
            )

        search = self.request.query_params.get(
            "search"
        )
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search)
                | models.Q(
                    description__icontains=search
                )
            )

        salary_min = self.request.query_params.get(
            "salary_min"
        )
        salary_max = self.request.query_params.get(
            "salary_max"
        )

        if salary_min:
            try:
                queryset = queryset.filter(
                    salary_min__gte=int(
                        salary_min
                    )
                )
            except (ValueError, TypeError):
                pass

        if salary_max:
            try:
                queryset = queryset.filter(
                    salary_max__lte=int(
                        salary_max
                    )
                )
            except (ValueError, TypeError):
                pass

        return queryset

