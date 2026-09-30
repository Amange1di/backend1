from django.db import models
from django.shortcuts import get_object_or_404
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

from .serializers import (
    CompanySerializer,
    JobVacancyDetailSerializer,
    JobVacancySerializer,
    PublicCourseSerializer,
)
from .services import (
    BOOST_COST,
    URGENT_COST,
    charge_promotion,
    mark_urgent,
    promote_item,
    resolve_user_company_name,
)


class MarketplaceCompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Company.objects.filter(
            is_active=True
        ).order_by("-created_at")
        user = self.request.user

        if user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(owner=user)

        if user.role == User.Role.MANAGER:
            if user.company:
                return queryset.filter(
                    owner__company=user.company
                )
            return queryset.none()

        if user.role in (
            User.Role.TEACHER,
            User.Role.STUDENT,
        ):
            return queryset.none()

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            raise PermissionDenied(
                "Only course admins and managers can create companies."
            )

        owner = (
            user
            if user.role == User.Role.COURSE_ADMIN
            else user.created_by
        )
        serializer.save(owner=owner)


class MarketplaceCourseViewSet(viewsets.ModelViewSet):
    queryset = (
        PublicCourse.objects.all()
        .order_by(
            "-is_promoted",
            "-created_at",
        )
        .select_related("company")
    )
    serializer_class = PublicCourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    def get_queryset(self):
        queryset = (
            PublicCourse.objects.filter(
                is_active=True
            )
            .select_related("company")
            .prefetch_related(
                "company__landing_pages"
            )
        )
        user = self.request.user

        if not user.is_authenticated:
            return queryset

        if user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(
                company__owner=user
            )

        if user.role == User.Role.MANAGER:
            company_name = resolve_user_company_name(
                user
            )
            if company_name:
                return queryset.filter(
                    company__name=company_name
                )
            return queryset.none()

        if user.role == User.Role.STUDENT:
            return queryset.filter(
                is_active=True
            )

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            raise PermissionDenied(
                "Only course admins and managers can create courses."
            )

        owner = (
            user
            if user.role == User.Role.COURSE_ADMIN
            else user.created_by
        )
        company = serializer.validated_data.get(
            "company"
        )

        if not company:
            company = Company.objects.filter(
                owner=owner
            ).first()
            if not company:
                raise PermissionDenied(
                    "No company found. Create a company first."
                )

        serializer.save(company=company)

    def perform_update(self, serializer):
        user = self.request.user
        course = self.get_object()

        if (
            user.role == User.Role.COURSE_ADMIN
            and course.company.owner != user
        ):
            raise PermissionDenied(
                "Not allowed for this course."
            )

        if (
            user.role == User.Role.MANAGER
            and course.company != user.company
        ):
            raise PermissionDenied(
                "Not allowed for this course."
            )

        serializer.save()


class MarketplaceJobViewSet(viewsets.ModelViewSet):
    queryset = JobVacancy.objects.all().order_by(
        "-is_promoted",
        "-created_at",
    )
    serializer_class = JobVacancySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = JobVacancy.objects.filter(
            is_active=True
        )
        user = self.request.user

        if not user.is_authenticated:
            return queryset

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

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            raise PermissionDenied(
                "Only course admins and managers can create jobs."
            )

        owner = (
            user
            if user.role == User.Role.COURSE_ADMIN
            else user.created_by
        )
        company = serializer.validated_data.get(
            "company"
        )

        if not company:
            company = Company.objects.filter(
                owner=owner
            ).first()
            if not company:
                raise PermissionDenied(
                    "No company found. Create a company first."
                )

        serializer.save(company=company)


class MyCoursesView(APIView):
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

        courses = PublicCourse.objects.filter(
            company=user.company,
            is_active=True,
        )

        data = []
        for course in courses:
            course_data = PublicCourseSerializer(
                course
            ).data
            course_data["views"] = course.views
            course_data["applications"] = (
                course.applications_count
            )
            course_data["status"] = "approved"
            data.append(course_data)

        return Response(data)


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
            is_active=True,
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
            job_data["status"] = "approved"
            data.append(job_data)

        return Response(data)


class BoostCourseView(APIView):
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

        course = get_object_or_404(
            PublicCourse,
            pk=pk,
        )

        if (
            user.role == User.Role.COURSE_ADMIN
            and course.company.owner != user
        ):
            return Response(
                {"detail": "Недостаточно прав."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            user.role == User.Role.MANAGER
            and course.company != user.company
        ):
            return Response(
                {"detail": "Недостаточно прав."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not charge_promotion(
            company=user.company,
            amount=BOOST_COST,
            reason=(
                f"Продвижение курса: {course.title}"
            ),
            transaction_type=(
                Transaction.TransactionType.BOOST
            ),
        ):
            return Response(
                {
                    "detail": (
                        f"Недостаточно средств. Требуется {BOOST_COST} eC."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        promote_item(course, days=7)
        return Response(
            PublicCourseSerializer(course).data
        )


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

        if not charge_promotion(
            company=user.company,
            amount=BOOST_COST,
            reason=(
                f"Продвижение вакансии: {job.title}"
            ),
            transaction_type=(
                Transaction.TransactionType.BOOST
            ),
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


class UrgentCourseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        course = get_object_or_404(
            PublicCourse,
            pk=pk,
        )

        if (
            user.role == User.Role.COURSE_ADMIN
            and course.company.owner != user
        ):
            return Response(
                {"detail": "Недостаточно прав."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            user.role == User.Role.MANAGER
            and course.company != user.company
        ):
            return Response(
                {"detail": "Недостаточно прав."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not charge_promotion(
            company=user.company,
            amount=URGENT_COST,
            reason=(
                f"Срочный бейдж для курса: {course.title}"
            ),
            transaction_type=(
                Transaction.TransactionType.URGENT
            ),
        ):
            return Response(
                {
                    "detail": (
                        f"Недостаточно средств. Требуется {URGENT_COST} eC."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        mark_urgent(course, days=3)
        return Response(
            PublicCourseSerializer(course).data
        )


class UrgentJobView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user = request.user
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

        if not charge_promotion(
            company=user.company,
            amount=URGENT_COST,
            reason=(
                f"Срочный бейдж для вакансии: {job.title}"
            ),
            transaction_type=(
                Transaction.TransactionType.URGENT
            ),
        ):
            return Response(
                {
                    "detail": (
                        f"Недостаточно средств. Требуется {URGENT_COST} eC."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        mark_urgent(job, days=3)
        return Response(
            JobVacancySerializer(job).data
        )


class PublicCourseViewSet(
    viewsets.ReadOnlyModelViewSet
):
    queryset = (
        PublicCourse.objects.filter(
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
    serializer_class = PublicCourseSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        queryset = super().get_queryset()

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

        language = self.request.query_params.get(
            "language"
        )
        if language:
            queryset = queryset.filter(
                models.Q(
                    schedule__icontains=language
                )
                | models.Q(
                    requirements__icontains=language
                )
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

        min_price = self.request.query_params.get(
            "min_price"
        )
        max_price = self.request.query_params.get(
            "max_price"
        )

        if min_price:
            try:
                queryset = queryset.filter(
                    price__gte=float(min_price)
                )
            except (ValueError, TypeError):
                pass

        if max_price:
            try:
                queryset = queryset.filter(
                    price__lte=float(max_price)
                )
            except (ValueError, TypeError):
                pass

        return queryset


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
        queryset = super().get_queryset()

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
