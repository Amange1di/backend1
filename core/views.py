from datetime import date, timedelta
from calendar import monthrange
import re

from django.db import models
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Attendance,
    Auditorium,
    Course,
    Group,
    LandingHeaderLink,
    LandingPage,
    LandingSection,
    HomeworkTaskAttachment,
    HomeworkSubmission,
    HomeworkTask,
    Payment,
    Student,
    TrialLead,
    Task,
    User,
)
from .permissions import (
    IsAdmin,
    IsCourseAdmin,
    IsCourseAdminOrManager,
    IsCourseAdminOrManagerReadOnly,
    IsCourseAdminOrTeacherReadOnly,
    IsCourseAdminOrManagerOrStudentReadOnly,
    IsCourseAdminOrStudentReadOnly,
    IsCourseAdminOrManagerOrStudentReadOnly,
    IsTeacherOrCourseAdminReadOnly,
)
from .serializers import (
    AttendanceSerializer,
    AuditoriumSerializer,
    CourseAdminUpdateSerializer,
    CourseSerializer,
    GroupSerializer,
    LandingHeaderLinkSerializer,
    LandingPageSerializer,
    LandingPublicPageSerializer,
    HomeworkSubmissionSerializer,
    HomeworkTaskSerializer,
    LoginSerializer,
    PaymentSerializer,
    RegisterSerializer,
    StudentIdentityLoginSerializer,
    StudentProfileSerializer,
    StudentSetPasswordSerializer,
    StudentSerializer,
    TeacherCreateSerializer,
    TeacherUpdateSerializer,
    TrialLeadSerializer,
    TaskSerializer,
    UserUpdateSerializer,
    UserSerializer,
    normalize_phone,
    sync_student_user,
)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if request.user.is_authenticated and request.user.role == User.Role.ADMIN:
            return Response(
                {"detail": "Admins can only create course admins."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if request.user.is_authenticated and request.user.role == User.Role.TEACHER:
            return Response(
                {"detail": "Teachers cannot create users."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if request.user.is_authenticated and request.user.role == User.Role.MANAGER:
            return Response(
                {"detail": "Managers cannot create users."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if request.user.is_authenticated and request.user.role == User.Role.STUDENT:
            return Response(
                {"detail": "Students cannot create users."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        requested_role = serializer.validated_data.get("role")
        if (
            (not request.user.is_authenticated
             or request.user.role != User.Role.COURSE_ADMIN)
            and requested_role == User.Role.MANAGER
        ):
            return Response(
                {"detail": "Managers can only be created by course admins."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if (
            request.user.is_authenticated
            and request.user.role == User.Role.COURSE_ADMIN
        ):
            if requested_role == User.Role.MANAGER:
                # Check if course admin can create more managers
                if not request.user.can_create_manager():
                    return Response(
                        {
                            "detail": f"Manager limit reached. Maximum: {request.user.max_managers}, "
                            f"Current: {request.user.get_managers_count()}"
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
                user = serializer.save(
                    force_role=User.Role.MANAGER,
                    company_name=request.user.company_name,
                    created_by=request.user,
                )
            else:
                user = serializer.save(
                    force_role=User.Role.TEACHER,
                    company_name=request.user.company_name,
                    created_by=request.user,
                )
        else:
            user = serializer.save(force_role=User.Role.TEACHER, company_name="")
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {"token": token.key, "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data})


class StudentLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = StudentIdentityLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"].strip()
        first_name = serializer.validated_data["first_name"].strip()
        password = serializer.validated_data.get("password", "")
        normalized_phone = normalize_phone(phone_number)

        candidates = [
            student
            for student in Student.objects.select_related("user")
            .filter(first_name__iexact=first_name)
            .order_by("id")
            if normalize_phone(student.phone) == normalized_phone
        ]

        if not candidates:
            return Response(
                {"detail": "Invalid student credentials."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        accessible_students = []
        for student in candidates:
            if not student.user:
                sync_student_user(student)
                student.refresh_from_db()
            try:
                ensure_student_access_allowed(student)
                accessible_students.append(student)
            except PermissionDenied:
                continue

        if not accessible_students:
            return Response(
                {"detail": "Student access is disabled."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if len(accessible_students) > 1:
            return Response(
                {"detail": "Multiple student accounts matched. Contact your administrator."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student = accessible_students[0]
        user = student.user
        token, _ = Token.objects.get_or_create(user=user)

        if user.must_set_password or not user.has_usable_password():
            return Response(
                {
                    "token": token.key,
                    "user": UserSerializer(user).data,
                    "student": StudentSerializer(student, context={"request": request}).data,
                    "requires_password_setup": True,
                }
            )

        if not password:
            return Response(
                {
                    "detail": "Password is required.",
                    "code": "password_required",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(password):
            return Response(
                {"detail": "Invalid student credentials."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "token": token.key,
                "user": UserSerializer(user).data,
                "student": StudentSerializer(student, context={"request": request}).data,
                "requires_password_setup": False,
            }
        )


class StudentSetPasswordView(APIView):
    def post(self, request):
        if request.user.role != User.Role.STUDENT:
            raise PermissionDenied("Only students can set this password.")
        serializer = StudentSetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["password"])
        request.user.must_set_password = False
        request.user.save(update_fields=["password", "must_set_password"])
        token, _ = Token.objects.get_or_create(user=request.user)
        return Response({"token": token.key, "user": UserSerializer(request.user).data})


class StudentProfileView(APIView):
    def get(self, request):
        if request.user.role != User.Role.STUDENT:
            raise PermissionDenied("Only students can access this profile.")
        student = getattr(request.user, "student_profile", None)
        if not student:
            return Response({"detail": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)
        ensure_student_access_allowed(student)
        return Response(
            {
                "id": student.id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "phone": student.phone,
                "telegram": student.telegram,
                "company_name": student.company_name,
                "can_login": student.can_login,
                "must_set_password": request.user.must_set_password,
            }
        )

    def patch(self, request):
        if request.user.role != User.Role.STUDENT:
            raise PermissionDenied("Only students can update this profile.")
        student = getattr(request.user, "student_profile", None)
        if not student:
            return Response({"detail": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)
        ensure_student_access_allowed(student)
        serializer = StudentProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        student_fields = []
        user_fields = []
        phone = serializer.validated_data.get("phone")
        telegram = serializer.validated_data.get("telegram")
        password = serializer.validated_data.get("password")

        if phone is not None and phone != student.phone:
            student.phone = phone
            request.user.phone = phone
            student_fields.append("phone")
            user_fields.append("phone")
        if telegram is not None and telegram != student.telegram:
            student.telegram = telegram
            request.user.telegram = telegram
            student_fields.append("telegram")
            user_fields.append("telegram")
        if student_fields:
            student.save(update_fields=student_fields)
        if password:
            request.user.set_password(password)
            request.user.must_set_password = False
            user_fields.extend(["password", "must_set_password"])
        if user_fields:
            request.user.save(update_fields=list(dict.fromkeys(user_fields)))

        return self.get(request)


class CourseAdminCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        admins = User.objects.filter(role=User.Role.COURSE_ADMIN).order_by(
            "-date_joined"
        )
        return Response(UserSerializer(admins, many=True).data)

    def post(self, request):
        serializer = RegisterSerializer(
            data=request.data, context={"force_role": User.Role.COURSE_ADMIN}
        )
        serializer.is_valid(raise_exception=True)
        company_name = serializer.validated_data.get("company_name", "").strip()
        phone = serializer.validated_data.get("phone", "").strip()
        address = serializer.validated_data.get("address", "").strip()
        max_managers = serializer.validated_data.get("max_managers", 0) or 0
        if not company_name:
            return Response(
                {"detail": "Company name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not phone or not address:
            return Response(
                {"detail": "Phone and address are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if max_managers < 0:
            return Response(
                {"detail": "Manager limit must be 0 or more."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = serializer.save(
            created_by=request.user,
            company_name=company_name,
            max_managers=max_managers,
        )
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {"token": token.key, "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class CourseAdminDetailView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, pk: int):
        admin = get_object_or_404(User, pk=pk, role=User.Role.COURSE_ADMIN)
        return Response(UserSerializer(admin).data)

    def patch(self, request, pk: int):
        admin = get_object_or_404(User, pk=pk, role=User.Role.COURSE_ADMIN)
        serializer = CourseAdminUpdateSerializer(admin, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        admin = serializer.save()
        return Response(UserSerializer(admin).data)

    def delete(self, request, pk: int):
        admin = get_object_or_404(User, pk=pk, role=User.Role.COURSE_ADMIN)
        admin.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        data = UserSerializer(request.user).data
        if request.user.is_superuser and data.get("role") != User.Role.ADMIN:
            data["role"] = User.Role.ADMIN
        if request.user.role == User.Role.STUDENT:
            data["student_id"] = (
                request.user.student_profile.id
                if hasattr(request.user, "student_profile")
                and request.user.student_profile
                else None
            )
        return Response(
            {
                **data,
                "support_telegram": resolve_support_telegram(request.user),
            }
        )


def resolve_support_telegram(user: User) -> str:
    if user.role == User.Role.COURSE_ADMIN:
        admin = (
            user.created_by
            if user.created_by and user.created_by.role == User.Role.ADMIN
            else None
        )
        if admin and admin.telegram:
            return admin.telegram
        admin = (
            User.objects.filter(role=User.Role.ADMIN).order_by("date_joined").first()
        )
        return admin.telegram if admin and admin.telegram else ""
    if user.role in (User.Role.TEACHER, User.Role.MANAGER, User.Role.STUDENT):
        if user.created_by and user.created_by.telegram:
            return user.created_by.telegram
        if user.company_name:
            course_admin = (
                User.objects.filter(
                    role=User.Role.COURSE_ADMIN, company_name=user.company_name
                )
                .order_by("date_joined")
                .first()
            )
            return (
                course_admin.telegram if course_admin and course_admin.telegram else ""
            )
        return ""
    if user.role == User.Role.ADMIN:
        return user.telegram or ""
    return ""


def get_company_student_cabinet_enabled(company_name: str) -> bool:
    if not company_name:
        return False
    return User.objects.filter(
        role=User.Role.COURSE_ADMIN,
        company_name=company_name,
        is_student_cabinet_enabled=True,
    ).exists()


def student_has_allowed_group(student: Student) -> bool:
    groups = student.groups.all()
    if not groups.exists():
        return True
    return groups.filter(is_login_allowed=True).exists()


def ensure_student_access_allowed(student: Student):
    if not student.company_name or not get_company_student_cabinet_enabled(student.company_name):
        raise PermissionDenied("Student cabinet is disabled for this company.")
    if not student.can_login:
        raise PermissionDenied("Student login is disabled for this account.")
    if not student_has_allowed_group(student):
        raise PermissionDenied("Student login is disabled for this group.")
    if not student.user or student.user.role != User.Role.STUDENT:
        raise PermissionDenied("Student account is not configured.")
    if not student.user.is_active:
        raise PermissionDenied("Student account is inactive.")


def _student_can_access_homework_task(task: HomeworkTask, student: Student) -> bool:
    if task.target_type == HomeworkTask.TargetType.SPECIFIC_STUDENTS:
        return task.students.filter(id=student.id).exists()
    return task.group.students.filter(id=student.id).exists()


def _is_submission_locked(task: HomeworkTask) -> bool:
    if not task.hard_deadline:
        return False
    grace_delta = timedelta(minutes=task.grace_period_minutes or 0)
    if task.allow_late:
        return False
    return timezone.now() > (task.deadline + grace_delta)


def parse_schedule_days(value: str) -> set[int]:
    normalized = (
        value.lower()
        .replace(".", " ")
        .replace(",", " ")
        .replace(";", " ")
        .replace("/", " ")
    )
    tokens = [token for token in normalized.split() if token]
    mapping = [
        (
            0,
            [
                "mon",
                "monday",
                "\u043f\u043d",
                "\u0434\u04af\u0439",
                "\u0434\u04af\u0439\u0448",
            ],
        ),
        (1, ["tue", "tuesday", "\u0432\u0442", "\u0448\u0435\u0439"]),
        (2, ["wed", "wednesday", "\u0441\u0440", "\u0448\u0430\u0440"]),
        (3, ["thu", "thursday", "\u0447\u0442", "\u0431\u0435\u0439"]),
        (4, ["fri", "friday", "\u043f\u0442", "\u0436\u0443\u043c"]),
        (5, ["sat", "saturday", "\u0441\u0431", "\u0438\u0448"]),
        (6, ["sun", "sunday", "\u0432\u0441", "\u0436\u0435\u043a"]),
    ]
    result: set[int] = set()
    for token in tokens:
        for idx, keys in mapping:
            if any(token.startswith(key) for key in keys):
                result.add(idx)
                break
    return result


def parse_time_to_minutes(value: str):
    if not value:
        return None
    match = re.match(r"^(\d{1,2})[:.](\d{2})$", value.strip())
    if not match:
        return None
    hours = int(match.group(1))
    minutes = int(match.group(2))
    if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
        return None
    return hours * 60 + minutes


def ranges_overlap(start_a, end_a, start_b, end_b):
    a_start = start_a or date(1970, 1, 1)
    a_end = end_a or date(2999, 12, 31)
    b_start = start_b or date(1970, 1, 1)
    b_end = end_b or date(2999, 12, 31)
    return a_start <= b_end and b_start <= a_end


def time_ranges_overlap(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    return start_a < end_b and start_b < end_a


def compute_group_end_date(start_date, schedule_days: str, lessons_count):
    if not start_date or not lessons_count:
        return None
    if not schedule_days:
        return None
    days_set = parse_schedule_days(schedule_days)
    if not days_set:
        return None
    total = int(lessons_count)
    if total <= 0:
        return None
    current = start_date
    count = 0
    while count < total:
        if current.weekday() in days_set:
            count += 1
            if count == total:
                break
        current = current + timedelta(days=1)
    return current


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by("-created_at")
    serializer_class = CourseSerializer
    permission_classes = [IsCourseAdminOrManagerReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(admins=user)
        if user.is_authenticated and user.role == User.Role.MANAGER:
            if not user.company_name:
                return queryset.none()
            return queryset.filter(admins__company_name=user.company_name).distinct()
        return queryset

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == User.Role.MANAGER:
            raise PermissionDenied("Managers cannot create courses.")
        admins = serializer.validated_data.get("admins", [])
        if user.role == User.Role.COURSE_ADMIN:
            for admin in admins:
                if admin.company_name != user.company_name:
                    raise PermissionDenied(
                        "Course admins can only assign their company admins."
                    )
            course = serializer.save()
            course.admins.add(user)
            if admins:
                course.admins.add(*admins)
            return
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        if user.role == User.Role.MANAGER:
            raise PermissionDenied("Managers cannot update courses.")
        if user.role == User.Role.COURSE_ADMIN:
            admins = serializer.validated_data.get("admins", None)
            if admins is not None:
                for admin in admins:
                    if admin.company_name != user.company_name:
                        raise PermissionDenied(
                            "Course admins can only assign their company admins."
                        )
            course = serializer.save()
            course.admins.add(user)
            return
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        if request.user.role == User.Role.MANAGER:
            raise PermissionDenied("Managers cannot delete courses.")
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        course = self.get_object()
        students_qs = Student.objects.filter(primary_course=course)
        students_count = students_qs.count()
        paid_students = (
            Payment.objects.filter(status=Payment.Status.PAID, student__in=students_qs)
            .values("student")
            .distinct()
            .count()
        )
        attendance_qs = Attendance.objects.filter(group__course=course)
        total_attendance = attendance_qs.count()
        present_count = attendance_qs.filter(status=Attendance.Status.PRESENT).count()
        excused_count = attendance_qs.filter(status=Attendance.Status.EXCUSED).count()
        absent_count = attendance_qs.filter(status=Attendance.Status.ABSENT).count()
        attendance_rate = (
            (present_count + excused_count) / total_attendance
            if total_attendance
            else 0
        )
        return Response(
            {
                "students_total": students_count,
                "students_paid": paid_students,
                "attendance_total": total_attendance,
                "attendance_present": present_count,
                "attendance_excused": excused_count,
                "attendance_absent": absent_count,
                "attendance_rate": round(attendance_rate, 4),
            }
        )


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all().order_by("-created_at")
    serializer_class = StudentSerializer
    permission_classes = [IsCourseAdminOrManagerOrStudentReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(
                models.Q(primary_course__admins=user)
                | models.Q(groups__course__admins=user)
            ).distinct()
        if user.is_authenticated and user.role == User.Role.MANAGER:
            if not user.company_name:
                return queryset.none()
            return queryset.filter(
                models.Q(company_name=user.company_name)
                | models.Q(primary_course__admins__company_name=user.company_name)
                | models.Q(groups__company_name=user.company_name)
            ).distinct()
        if user.is_authenticated and user.role == User.Role.STUDENT:
            return queryset.filter(user=user)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.role in (User.Role.COURSE_ADMIN, User.Role.MANAGER):
            course = serializer.validated_data.get("primary_course")
            group_ids = serializer.validated_data.get("group_ids", [])
            account = serializer.validated_data.get("user")
            auto_course = None
            if course:
                allowed = course.admins.filter(id=user.id).exists()
                if user.role == User.Role.MANAGER:
                    allowed = course.admins.filter(
                        company_name=user.company_name
                    ).exists()
                if not allowed:
                    raise PermissionDenied("Not allowed for this course.")
            for group in group_ids:
                if group.course:
                    allowed = group.course.admins.filter(id=user.id).exists()
                    if user.role == User.Role.MANAGER:
                        allowed = group.course.admins.filter(
                            company_name=user.company_name
                        ).exists()
                    if not allowed:
                        raise PermissionDenied("Not allowed for this group.")
                elif group.company_name and group.company_name != user.company_name:
                    raise PermissionDenied("Not allowed for this group.")
            if not course and group_ids:
                first_course = group_ids[0].course
                if first_course and all(
                    group.course_id == first_course.id for group in group_ids
                ):
                    auto_course = first_course
            if (
                account
                and account.company_name
                and account.company_name != user.company_name
            ):
                raise PermissionDenied("Not allowed for this user.")
            save_kwargs = {"company_name": user.company_name}
            if course:
                save_kwargs["primary_course"] = course
            elif auto_course:
                save_kwargs["primary_course"] = auto_course
            student = serializer.save(**save_kwargs)
            sync_student_user(student, created_by=user)
            return
        student = serializer.save()
        sync_student_user(student, created_by=user if user.is_authenticated else None)

    def perform_update(self, serializer):
        user = self.request.user
        if user.role in (User.Role.COURSE_ADMIN, User.Role.MANAGER):
            if user.role == User.Role.MANAGER and "can_login" in serializer.validated_data:
                raise PermissionDenied("Managers cannot change student login access.")
            course = serializer.validated_data.get("primary_course", None)
            if course:
                allowed = course.admins.filter(id=user.id).exists()
                if user.role == User.Role.MANAGER:
                    allowed = course.admins.filter(
                        company_name=user.company_name
                    ).exists()
                if not allowed:
                    raise PermissionDenied("Not allowed for this course.")
            group_ids = serializer.validated_data.get("group_ids", [])
            for group in group_ids:
                if group.course:
                    allowed = group.course.admins.filter(id=user.id).exists()
                    if user.role == User.Role.MANAGER:
                        allowed = group.course.admins.filter(
                            company_name=user.company_name
                        ).exists()
                    if not allowed:
                        raise PermissionDenied("Not allowed for this group.")
                elif group.company_name and group.company_name != user.company_name:
                    raise PermissionDenied("Not allowed for this group.")
            auto_course = None
            if not course and group_ids:
                first_course = group_ids[0].course
                if first_course and all(
                    group.course_id == first_course.id for group in group_ids
                ):
                    auto_course = first_course
            save_kwargs = {}
            if course:
                save_kwargs["primary_course"] = course
            elif auto_course:
                save_kwargs["primary_course"] = auto_course
            student = serializer.save(**save_kwargs)
            sync_student_user(student, created_by=user)
            return
        student = serializer.save()
        sync_student_user(student, created_by=user if user.is_authenticated else None)

    def destroy(self, request, *args, **kwargs):
        if request.user.role in (User.Role.MANAGER, User.Role.STUDENT):
            raise PermissionDenied("Not allowed to delete students.")
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        if request.user.role != User.Role.COURSE_ADMIN:
            raise PermissionDenied("Only course admins can reset student passwords.")
        student = self.get_object()
        if student.company_name != request.user.company_name:
            raise PermissionDenied("Not allowed for this student.")
        if not student.user:
            sync_student_user(student, created_by=request.user)
            student.refresh_from_db()
        student.user.set_unusable_password()
        student.user.must_set_password = True
        student.user.save(update_fields=["password", "must_set_password"])
        Token.objects.filter(user=student.user).delete()
        return Response({"detail": "Student password was reset.", "must_set_password": True})


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(role=User.Role.TEACHER).order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsCourseAdminOrManagerReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related("teaching_courses")
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.COURSE_ADMIN:
            queryset = queryset.filter(company_name=user.company_name)
        elif user.is_authenticated and user.role == User.Role.MANAGER:
            queryset = queryset.filter(company_name=user.company_name)
        course_param = self.request.query_params.get("course")
        if course_param:
            try:
                course_id = int(course_param)
            except (TypeError, ValueError):
                return queryset.none()
            queryset = queryset.filter(teaching_courses__id=course_id)
        return queryset.distinct()

    def create(self, request, *args, **kwargs):
        user = request.user
        if user.role == User.Role.ADMIN:
            raise PermissionDenied("Admins cannot create teachers.")
        if user.role == User.Role.MANAGER:
            raise PermissionDenied("Managers cannot create teachers.")
        serializer = TeacherCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        teacher = serializer.save()
        return Response(
            UserSerializer(teacher).data,
            status=status.HTTP_201_CREATED,
        )

    def perform_update(self, serializer):
        user = self.request.user
        if user.role == User.Role.MANAGER:
            raise PermissionDenied("Managers cannot update teachers.")
        if user.role == User.Role.COURSE_ADMIN:
            if (
                "role" in serializer.validated_data
                and serializer.validated_data["role"] != User.Role.TEACHER
            ):
                raise PermissionDenied("Course admins cannot change roles.")
            if (
                "company_name" in serializer.validated_data
                and serializer.validated_data["company_name"] != user.company_name
            ):
                raise PermissionDenied("Not allowed for this company.")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        if request.user.role == User.Role.MANAGER:
            raise PermissionDenied("Managers cannot delete teachers.")
        return super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return TeacherUpdateSerializer
        return super().get_serializer_class()


class ManagerViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(role=User.Role.MANAGER).order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsCourseAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(created_by=user)
        return queryset.none()

    def create(self, request, *args, **kwargs):
        user = request.user
        if user.role != User.Role.COURSE_ADMIN:
            raise PermissionDenied("Only course admins can create managers.")
        if not user.can_create_manager():
            raise PermissionDenied(
                f"Manager limit reached. Maximum: {user.max_managers}, "
                f"Current: {user.get_managers_count()}"
            )
        serializer = RegisterSerializer(
            data=request.data, context={"force_role": User.Role.MANAGER}
        )
        serializer.is_valid(raise_exception=True)
        manager = serializer.save(created_by=user, company_name=user.company_name)
        return Response(UserSerializer(manager).data, status=status.HTTP_201_CREATED)

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return super().get_serializer_class()


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by("-created_at")
    serializer_class = GroupSerializer
    permission_classes = [IsCourseAdminOrTeacherReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(
                models.Q(course__admins=user) | models.Q(company_name=user.company_name)
            ).distinct()
        if user.is_authenticated and user.role == User.Role.MANAGER:
            return queryset.filter(
                models.Q(course__admins__company_name=user.company_name)
                | models.Q(company_name=user.company_name)
            ).distinct()
        if user.is_authenticated and user.role == User.Role.TEACHER:
            return queryset.filter(teacher=user)
        if user.is_authenticated and user.role == User.Role.STUDENT:
            return queryset.filter(students__user=user).distinct()
        return queryset

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        if user.role in (User.Role.COURSE_ADMIN, User.Role.MANAGER):
            course = serializer.validated_data.get("course")
            if not course:
                raise PermissionDenied("Not allowed for this course.")
            allowed = course.admins.filter(id=user.id).exists()
            if user.role == User.Role.MANAGER:
                allowed = course.admins.filter(company_name=user.company_name).exists()
            if not allowed:
                raise PermissionDenied("Not allowed for this course.")
            teacher = serializer.validated_data.get("teacher")
            if teacher and teacher.company_name != user.company_name:
                raise PermissionDenied("Teacher must belong to the same company.")
            if teacher and not teacher.teaching_courses.filter(id=course.id).exists():
                raise PermissionDenied("Teacher is not assigned to this course.")
            auditorium = serializer.validated_data.get("auditorium")
            if auditorium and auditorium.company_name != user.company_name:
                raise PermissionDenied("Auditorium must belong to the same company.")
            student_ids = serializer.validated_data.get("student_ids", [])
            for student in student_ids:
                if student.company_name != user.company_name:
                    raise PermissionDenied("Student must belong to the same company.")
        self._ensure_auditorium_available(serializer)
        end_date = compute_group_end_date(
            serializer.validated_data.get("start_date"),
            serializer.validated_data.get("schedule_days", ""),
            serializer.validated_data.get("lessons_count"),
        )
        serializer.save(company_name=user.company_name, end_date=end_date)

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()
        if user.role in (User.Role.COURSE_ADMIN, User.Role.MANAGER):
            if user.role == User.Role.MANAGER and "is_login_allowed" in serializer.validated_data:
                raise PermissionDenied("Managers cannot change group login access.")
            course = serializer.validated_data.get("course", None)
            if course:
                allowed = course.admins.filter(id=user.id).exists()
                if user.role == User.Role.MANAGER:
                    allowed = course.admins.filter(
                        company_name=user.company_name
                    ).exists()
                if not allowed:
                    raise PermissionDenied("Not allowed for this course.")
            selected_teacher = serializer.validated_data.get("teacher", instance.teacher)
            if selected_teacher and selected_teacher.company_name != user.company_name:
                raise PermissionDenied("Teacher must belong to the same company.")
            course_for_teacher = course or instance.course
            if (
                selected_teacher
                and course_for_teacher
                and not selected_teacher.teaching_courses.filter(
                    id=course_for_teacher.id
                ).exists()
            ):
                raise PermissionDenied("Teacher is not assigned to this course.")
            auditorium = serializer.validated_data.get("auditorium")
            if auditorium and auditorium.company_name != user.company_name:
                raise PermissionDenied("Auditorium must belong to the same company.")
            student_ids = serializer.validated_data.get("student_ids", [])
            for student in student_ids:
                if student.company_name != user.company_name:
                    raise PermissionDenied("Student must belong to the same company.")
        self._ensure_auditorium_available(serializer, instance=instance)
        start_date = serializer.validated_data.get("start_date", instance.start_date)
        schedule_days = serializer.validated_data.get(
            "schedule_days", instance.schedule_days
        )
        lessons_count = serializer.validated_data.get(
            "lessons_count", instance.lessons_count
        )
        end_date = compute_group_end_date(start_date, schedule_days, lessons_count)
        serializer.save(end_date=end_date)

    def destroy(self, request, *args, **kwargs):
        if request.user.role == User.Role.MANAGER:
            raise PermissionDenied("Managers cannot delete groups.")
        return super().destroy(request, *args, **kwargs)

    def _ensure_auditorium_available(self, serializer, instance=None):
        auditorium = serializer.validated_data.get(
            "auditorium",
            instance.auditorium if instance else None,
        )
        schedule_time = serializer.validated_data.get(
            "schedule_time",
            instance.schedule_time if instance else "",
        )
        schedule_days = serializer.validated_data.get(
            "schedule_days",
            instance.schedule_days if instance else "",
        )
        start_date = serializer.validated_data.get(
            "start_date",
            instance.start_date if instance else None,
        )
        end_date = serializer.validated_data.get(
            "end_date",
            instance.end_date if instance else None,
        )
        course = serializer.validated_data.get(
            "course",
            instance.course if instance else None,
        )
        if not auditorium or not schedule_time or not schedule_days or not course:
            return
        duration = course.lesson_duration_minutes or None
        if not duration:
            return
        start_minutes = parse_time_to_minutes(schedule_time)
        if start_minutes is None:
            return
        end_minutes = start_minutes + duration
        days_set = parse_schedule_days(schedule_days)
        if not days_set:
            return

        qs = Group.objects.filter(auditorium=auditorium)
        if instance:
            qs = qs.exclude(id=instance.id)

        for group in qs:
            if not group.schedule_time or not group.schedule_days:
                continue
            other_duration = (
                group.course.lesson_duration_minutes if group.course else None
            )
            if not other_duration:
                continue
            other_start = parse_time_to_minutes(group.schedule_time)
            if other_start is None:
                continue
            other_end = other_start + other_duration
            if not time_ranges_overlap(
                start_minutes, end_minutes, other_start, other_end
            ):
                continue
            other_days = parse_schedule_days(group.schedule_days)
            if not other_days or not days_set.intersection(other_days):
                continue
            if not ranges_overlap(
                start_date, end_date, group.start_date, group.end_date
            ):
                continue
            raise PermissionDenied("Auditorium is busy at this time.")


class AuditoriumViewSet(viewsets.ModelViewSet):
    queryset = Auditorium.objects.all().order_by("-created_at")
    serializer_class = AuditoriumSerializer
    permission_classes = [IsCourseAdminOrManagerReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(company_name=user.company_name)
        if user.is_authenticated and user.role == User.Role.MANAGER:
            return queryset.filter(company_name=user.company_name)
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == User.Role.MANAGER:
            raise PermissionDenied("Managers cannot create auditoriums.")
        serializer.save(company_name=user.company_name)


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all().order_by("-created_at")
    serializer_class = AttendanceSerializer
    permission_classes = [IsCourseAdminOrTeacherReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(
                models.Q(group__course__admins=user)
                | models.Q(group__company_name=user.company_name)
            ).distinct()
        if user.is_authenticated and user.role == User.Role.TEACHER:
            return queryset.filter(group__teacher=user)
        if user.is_authenticated and user.role == User.Role.STUDENT:
            return queryset.filter(student__user=user)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.role in (User.Role.COURSE_ADMIN, User.Role.MANAGER):
            raise permissions.PermissionDenied("Course admins cannot mark attendance.")
        group = serializer.validated_data.get("group")
        if user.role == User.Role.TEACHER and group.teacher_id != user.id:
            raise permissions.PermissionDenied("Not allowed for this group.")
        serializer.save()


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().order_by("-created_at")
    serializer_class = PaymentSerializer
    permission_classes = [IsCourseAdminOrManagerOrStudentReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(
                models.Q(student__primary_course__admins=user)
                | models.Q(group__course__admins=user)
                | models.Q(group__company_name=user.company_name)
            )
        if user.is_authenticated and user.role == User.Role.MANAGER:
            if not user.company_name:
                return queryset.none()
            return queryset.filter(
                models.Q(student__company_name=user.company_name)
                | models.Q(student__primary_course__admins__company_name=user.company_name)
                | models.Q(group__company_name=user.company_name)
                | models.Q(group__course__admins__company_name=user.company_name)
            ).distinct()
        if user.is_authenticated and user.role == User.Role.STUDENT:
            return queryset.filter(student__user=user)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.role in (User.Role.COURSE_ADMIN, User.Role.MANAGER):
            student = serializer.validated_data.get("student")
            group = serializer.validated_data.get("group")
            allowed = False
            if student and student.primary_course:
                if user.role == User.Role.COURSE_ADMIN:
                    if student.primary_course.admins.filter(id=user.id).exists():
                        allowed = True
                else:
                    if student.primary_course.admins.filter(
                        company_name=user.company_name
                    ).exists():
                        allowed = True
            if student and student.company_name == user.company_name:
                allowed = True
            if group:
                if group.course:
                    if user.role == User.Role.COURSE_ADMIN:
                        if group.course.admins.filter(id=user.id).exists():
                            allowed = True
                    else:
                        if group.course.admins.filter(
                            company_name=user.company_name
                        ).exists():
                            allowed = True
                if group.company_name and group.company_name == user.company_name:
                    allowed = True
            if not allowed:
                raise PermissionDenied("Not allowed for this course.")
        elif user.role == User.Role.STUDENT:
            raise PermissionDenied("Students cannot create payments.")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        if request.user.role in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
            User.Role.STUDENT,
        ):
            raise PermissionDenied("Not allowed to delete payments.")
        return super().destroy(request, *args, **kwargs)


class DashboardView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        total_students = Student.objects.count()
        total_income = (
            Payment.objects.filter(status=Payment.Status.PAID).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )
        total_debt = (
            Payment.objects.filter(status=Payment.Status.DEBT).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )
        return Response(
            {
                "total_students": total_students,
                "total_income": total_income,
                "total_debt": total_debt,
            }
        )


class LandingPageViewSet(viewsets.ModelViewSet):
    queryset = LandingPage.objects.all().prefetch_related("sections")
    serializer_class = LandingPageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(company_name=user.company_name)
        if user.role == User.Role.ADMIN or user.is_superuser:
            status_filter = self.request.query_params.get("status", "").strip()
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            company_name = self.request.query_params.get("company_name", "").strip()
            if company_name:
                queryset = queryset.filter(company_name=company_name)
            return queryset
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != User.Role.COURSE_ADMIN:
            raise PermissionDenied("Only course admins can create landing pages.")
        if not user.can_create_landing_page():
            raise PermissionDenied(
                f"Landing pages limit reached. Maximum: {user.max_pages}, "
                f"Current: {user.get_pages_count()}"
            )
        serializer.save(owner=user, company_name=user.company_name)

    def perform_update(self, serializer):
        page = self.get_object()
        user = self.request.user
        if user.role == User.Role.COURSE_ADMIN:
            if page.company_name != user.company_name:
                raise PermissionDenied("Not allowed for this landing page.")
            serializer.save()
            return
        if user.role == User.Role.ADMIN or user.is_superuser:
            serializer.save()
            return
        raise PermissionDenied("Not allowed.")

    def destroy(self, request, *args, **kwargs):
        page = self.get_object()
        user = request.user
        if user.role == User.Role.COURSE_ADMIN and page.company_name != user.company_name:
            raise PermissionDenied("Not allowed for this landing page.")
        if user.role not in (User.Role.COURSE_ADMIN, User.Role.ADMIN) and not user.is_superuser:
            raise PermissionDenied("Not allowed to delete this landing page.")
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        page = self.get_object()
        user = request.user
        if user.role != User.Role.COURSE_ADMIN or page.company_name != user.company_name:
            raise PermissionDenied("Only the owning course admin can submit this landing page.")
        if page.status == LandingPage.Status.PENDING:
            raise PermissionDenied("This landing page is already pending moderation.")
        validate_landing_page_for_publication(page, user)
        page.status = LandingPage.Status.PENDING
        page.moderation_comment = ""
        page.submitted_at = timezone.now()
        page.save(update_fields=["status", "moderation_comment", "submitted_at", "updated_at"])
        return Response(self.get_serializer(page).data)

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        page = self.get_object()
        user = request.user
        if user.role != User.Role.ADMIN and not user.is_superuser:
            raise PermissionDenied("Only admins can approve landing pages.")
        if page.status != LandingPage.Status.PENDING:
            raise PermissionDenied("Only pending landing pages can be approved.")
        validate_landing_page_for_publication(page, page.owner)
        page.status = LandingPage.Status.ACTIVE
        page.moderation_comment = ""
        page.moderated_at = timezone.now()
        page.moderated_by = user
        page.published_at = page.published_at or timezone.now()
        page.save(
            update_fields=[
                "status",
                "moderation_comment",
                "moderated_at",
                "moderated_by",
                "published_at",
                "updated_at",
            ]
        )
        return Response(self.get_serializer(page).data)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        page = self.get_object()
        user = request.user
        if user.role != User.Role.ADMIN and not user.is_superuser:
            raise PermissionDenied("Only admins can reject landing pages.")
        if page.status != LandingPage.Status.PENDING:
            raise PermissionDenied("Only pending landing pages can be rejected.")
        comment = (request.data.get("comment") or "").strip()
        if not comment:
            return Response(
                {"detail": "Moderation comment is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        page.status = LandingPage.Status.REJECTED
        page.moderation_comment = comment
        page.moderated_at = timezone.now()
        page.moderated_by = user
        page.save(
            update_fields=[
                "status",
                "moderation_comment",
                "moderated_at",
                "moderated_by",
                "updated_at",
            ]
        )
        return Response(self.get_serializer(page).data)


class LandingHeaderLinkViewSet(viewsets.ModelViewSet):
    queryset = LandingHeaderLink.objects.all().select_related("target_page")
    serializer_class = LandingHeaderLinkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(company_name=user.company_name)
        if user.role == User.Role.ADMIN or user.is_superuser:
            company_name = self.request.query_params.get("company_name", "").strip()
            if company_name:
                queryset = queryset.filter(company_name=company_name)
            return queryset
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != User.Role.COURSE_ADMIN:
            raise PermissionDenied("Only course admins can manage landing header links.")
        serializer.save(company_name=user.company_name)

    def perform_update(self, serializer):
        link = self.get_object()
        user = self.request.user
        if user.role != User.Role.COURSE_ADMIN or link.company_name != user.company_name:
            raise PermissionDenied("Only the owning course admin can update this header link.")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        link = self.get_object()
        if request.user.role != User.Role.COURSE_ADMIN or link.company_name != request.user.company_name:
            raise PermissionDenied("Only the owning course admin can delete this header link.")
        return super().destroy(request, *args, **kwargs)


class PublicLandingDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug: str):
        page = get_object_or_404(
            LandingPage.objects.prefetch_related("sections"),
            slug=slug,
            status=LandingPage.Status.ACTIVE,
        )
        return Response(LandingPublicPageSerializer(page, context={"request": request}).data)


class PublicLandingLeadCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, slug: str):
        page = get_object_or_404(
            LandingPage,
            slug=slug,
            status=LandingPage.Status.ACTIVE,
        )
        full_name = (request.data.get("full_name") or "").strip()
        phone = (request.data.get("phone") or "").strip()
        if not full_name or not phone:
            return Response(
                {"detail": "Full name and phone are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        lead = TrialLead.objects.create(
            full_name=full_name,
            phone=phone,
            course_interest=(request.data.get("course_interest") or "").strip(),
            source=f"landing:{page.slug}",
            comment=(request.data.get("comment") or "").strip(),
            company_name=page.company_name,
        )
        return Response(TrialLeadSerializer(lead).data, status=status.HTTP_201_CREATED)


class TrialLeadViewSet(viewsets.ModelViewSet):
    queryset = TrialLead.objects.all().order_by("-created_at")
    serializer_class = TrialLeadSerializer
    permission_classes = [IsCourseAdminOrManager]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(company_name=user.company_name)
        if user.is_authenticated and user.role == User.Role.MANAGER:
            return queryset.filter(company_name=user.company_name)
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != User.Role.MANAGER:
            raise PermissionDenied("Only managers can create trial leads.")
        group = serializer.validated_data.get("group_assigned")
        if group and group.company_name != user.company_name:
            raise PermissionDenied("Not allowed for this group.")
        serializer.save(company_name=user.company_name)

    def perform_update(self, serializer):
        user = self.request.user
        if user.role != User.Role.MANAGER:
            raise PermissionDenied("Only managers can update trial leads.")
        group = serializer.validated_data.get("group_assigned")
        if group and group.company_name != user.company_name:
            raise PermissionDenied("Not allowed for this group.")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        if request.user.role != User.Role.MANAGER:
            raise PermissionDenied("Only managers can delete trial leads.")
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="analytics")
    def analytics(self, request):
        months_param = request.query_params.get("months", "").strip()
        months = [m.strip() for m in months_param.split(",") if m.strip()]
        if not months:
            today = date.today()
            months = [f"{today.year:04d}-{today.month:02d}"]
        if len(months) < 1 or len(months) > 6:
            return Response(
                {"detail": "Months count must be between 1 and 6."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        parsed_months = []
        for value in months:
            parts = value.split("-")
            if len(parts) != 2:
                return Response(
                    {"detail": "Invalid month format. Use YYYY-MM."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                year = int(parts[0])
                month = int(parts[1])
                if month < 1 or month > 12:
                    raise ValueError()
            except ValueError:
                return Response(
                    {"detail": "Invalid month format. Use YYYY-MM."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            parsed_months.append((value, year, month))

        qs = self.get_queryset()
        monthly_data = []
        sources_by_month = []
        ages_by_month = []

        total_leads = 0
        attended_total = 0
        not_attended_total = 0
        converted_total = 0

        for value, year, month in parsed_months:
            last_day = monthrange(year, month)[1]
            start_date = date(year, month, 1)
            end_date = date(year, month, last_day)
            month_qs = qs.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )
            total = month_qs.count()
            attended = month_qs.filter(trial_attended=True).count()
            not_attended = month_qs.filter(
                status=TrialLead.Status.NOT_ATTENDED
            ).count()
            converted = month_qs.filter(
                models.Q(converted_to_student=True)
                | models.Q(status=TrialLead.Status.CONVERTED)
            ).count()
            rate = round((converted / total * 100) if total else 0, 2)

            total_leads += total
            attended_total += attended
            not_attended_total += not_attended
            converted_total += converted

            monthly_data.append(
                {
                    "month": value,
                    "total_leads": total,
                    "attended_trial": attended,
                    "not_attended": not_attended,
                    "converted_students": converted,
                    "conversion_rate": rate,
                }
            )

            sources_raw = (
                month_qs.values("source")
                .annotate(total=models.Count("id"))
                .order_by("-total")
            )
            sources_items = [
                {
                    "label": item["source"] or "—",
                    "total": item["total"],
                }
                for item in sources_raw
            ]
            sources_by_month.append({"month": value, "items": sources_items})

            ages_by_month.append(
                {
                    "month": value,
                    "items": compute_age_groups(month_qs),
                }
            )

        summary_rate = round(
            (converted_total / total_leads * 100) if total_leads else 0, 2
        )

        return Response(
            {
                "months": [value for value, _, _ in parsed_months],
                "summary": {
                    "total_leads": total_leads,
                    "attended_trial": attended_total,
                    "not_attended": not_attended_total,
                    "converted_students": converted_total,
                    "conversion_rate": summary_rate,
                },
                "monthly_data": monthly_data,
                "sources": sources_by_month,
                "age_groups": ages_by_month,
            }
        )


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().order_by("-created_at")
    serializer_class = TaskSerializer
    permission_classes = [IsCourseAdminOrManager]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(company_name=user.company_name)
        if user.is_authenticated and user.role == User.Role.MANAGER:
            return queryset.filter(assigned_to=user)
        return queryset.none()

    def create(self, request, *args, **kwargs):
        user = request.user
        if user.role != User.Role.COURSE_ADMIN:
            raise PermissionDenied("Only course admins can create tasks.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assigned_to = serializer.validated_data.get("assigned_to")
        if not assigned_to or assigned_to.role != User.Role.MANAGER:
            raise PermissionDenied("Task must be assigned to a manager.")
        if assigned_to.company_name != user.company_name:
            raise PermissionDenied("Manager must belong to the same company.")

        tasks = build_task_instances(serializer.validated_data, user)
        Task.objects.bulk_create(tasks)
        data = TaskSerializer(tasks, many=True).data
        return Response(data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        user = self.request.user
        if user.role == User.Role.MANAGER:
            # Managers can only update status of their tasks
            if self.get_object().assigned_to_id != user.id:
                raise PermissionDenied("Not allowed for this task.")
            allowed_fields = {"status", "is_seen"}
            update_fields = set(serializer.validated_data.keys())
            if not update_fields.issubset(allowed_fields):
                raise PermissionDenied("Managers can only update status or seen flag.")
            serializer.save()
            return
        if user.role == User.Role.COURSE_ADMIN:
            assigned_to = serializer.validated_data.get("assigned_to")
            if assigned_to and assigned_to.company_name != user.company_name:
                raise PermissionDenied("Manager must belong to the same company.")
            serializer.save()
            return
        raise PermissionDenied("Not allowed.")

    def destroy(self, request, *args, **kwargs):
        if request.user.role != User.Role.COURSE_ADMIN:
            raise PermissionDenied("Only course admins can delete tasks.")
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["post"], url_path="mark-seen")
    def mark_seen(self, request):
        user = request.user
        if user.role != User.Role.MANAGER:
            raise PermissionDenied("Only managers can mark tasks as seen.")
        ids = request.data.get("ids", [])
        queryset = self.get_queryset()
        if ids:
            queryset = queryset.filter(id__in=ids)
        updated = queryset.update(is_seen=True)
        return Response({"updated": updated})


def validate_landing_page_for_publication(page: LandingPage, owner: User | None):
    if owner and owner.role == User.Role.COURSE_ADMIN and page.sections.count() > owner.max_blocks:
        raise PermissionDenied(
            f"Page exceeds the allowed number of blocks ({owner.max_blocks})."
        )
    total_pages = LandingPage.objects.filter(company_name=page.company_name).count()
    if total_pages > 1:
        links = LandingHeaderLink.objects.filter(company_name=page.company_name)
        if not links.exists():
            raise PermissionDenied(
                "Header navigation must be configured when more than one landing page exists."
            )
        invalid_target_exists = links.exclude(target_page__company_name=page.company_name).exists()
        if invalid_target_exists:
            raise PermissionDenied("All header links must target pages from the same company.")


class HomeworkTaskViewSet(viewsets.ModelViewSet):
    queryset = HomeworkTask.objects.all().select_related("group", "teacher").prefetch_related("attachments", "students", "submissions").order_by("-created_at")
    serializer_class = HomeworkTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.STUDENT:
            now = timezone.now()
            return queryset.filter(
                is_published=True,
            ).filter(
                models.Q(publish_at__isnull=True) | models.Q(publish_at__lte=now)
            ).filter(
                models.Q(
                    target_type=HomeworkTask.TargetType.ALL_GROUP,
                    group__students__user=user,
                )
                | models.Q(
                    target_type=HomeworkTask.TargetType.SPECIFIC_STUDENTS,
                    students__user=user,
                )
            ).distinct()
        if user.is_authenticated and user.role == User.Role.TEACHER:
            return queryset.filter(teacher=user)
        if user.is_authenticated and user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(company_name=user.company_name)
        return queryset.none()

    def create(self, request, *args, **kwargs):
        user = request.user
        if user.role != User.Role.TEACHER:
            raise PermissionDenied("Only teachers can create homework tasks.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.validated_data.get("group")
        if not group or group.teacher_id != user.id:
            raise PermissionDenied("Homework can only be created for your own groups.")
        instance = serializer.save(teacher=user, company_name=user.company_name)
        self._save_attachments(instance)
        data = self.get_serializer(instance).data
        headers = self.get_success_headers(data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()
        if user.role == User.Role.TEACHER:
            if instance.teacher_id != user.id:
                raise PermissionDenied("Not allowed for this homework task.")
            group = serializer.validated_data.get("group", instance.group)
            if group.teacher_id != user.id:
                raise PermissionDenied("Homework can only belong to your own groups.")
            instance = serializer.save()
            self._save_attachments(instance, replace=True)
            return
        if user.role == User.Role.COURSE_ADMIN:
            if instance.company_name != user.company_name:
                raise PermissionDenied("Not allowed for this homework task.")
            updated = serializer.save()
            self._save_attachments(updated, replace=True)
            return
        raise PermissionDenied("Not allowed.")

    def destroy(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()
        if user.role == User.Role.TEACHER and instance.teacher_id == user.id:
            return super().destroy(request, *args, **kwargs)
        if user.role == User.Role.COURSE_ADMIN and instance.company_name == user.company_name:
            return super().destroy(request, *args, **kwargs)
        raise PermissionDenied("Not allowed to delete this homework task.")

    def _save_attachments(self, instance: HomeworkTask, replace: bool = False):
        files = self.request.FILES.getlist("files")
        if replace:
            clear_files = self.request.data.get("clear_files")
            if str(clear_files).lower() in {"1", "true", "yes"}:
                instance.attachments.all().delete()
        for file_obj in files:
            HomeworkTaskAttachment.objects.create(task=instance, file=file_obj)


class HomeworkSubmissionViewSet(viewsets.ModelViewSet):
    queryset = HomeworkSubmission.objects.all().select_related("task", "student", "student__user").order_by("-submitted_at")
    serializer_class = HomeworkSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.STUDENT:
            return queryset.filter(student__user=user)
        if user.is_authenticated and user.role == User.Role.TEACHER:
            return queryset.filter(task__teacher=user)
        if user.is_authenticated and user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(task__company_name=user.company_name)
        return queryset.none()

    def create(self, request, *args, **kwargs):
        user = request.user
        if user.role != User.Role.STUDENT:
            raise PermissionDenied("Only students can submit homework.")
        student = getattr(user, "student_profile", None)
        if not student:
            raise PermissionDenied("Student profile not found.")
        task_id = request.data.get("task")
        task = get_object_or_404(HomeworkTask, pk=task_id)
        if not _student_can_access_homework_task(task, student):
            raise PermissionDenied("You can submit homework only for your own groups.")
        if _is_submission_locked(task):
            raise PermissionDenied("Submission deadline has passed.")
        if HomeworkSubmission.objects.filter(task=task, student=student).exists():
            raise PermissionDenied("Submission already exists for this task.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(student=student)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()
        if user.role == User.Role.STUDENT:
            if instance.student.user_id != user.id:
                raise PermissionDenied("Not allowed for this submission.")
            allowed_fields = {"answer_text", "file"}
            update_fields = set(serializer.validated_data.keys())
            if not update_fields.issubset(allowed_fields):
                raise PermissionDenied("Students can only update submission content.")
            if _is_submission_locked(instance.task):
                raise PermissionDenied("Submission deadline has passed.")
            serializer.save(status=HomeworkSubmission.Status.PENDING)
            return
        if user.role == User.Role.TEACHER:
            if instance.task.teacher_id != user.id:
                raise PermissionDenied("Not allowed for this submission.")
            allowed_fields = {"status", "grade", "teacher_comment"}
            update_fields = set(serializer.validated_data.keys())
            if not update_fields.issubset(allowed_fields):
                raise PermissionDenied("Teachers can only review homework submissions.")
            serializer.save()
            return
        raise PermissionDenied("Not allowed.")

    def destroy(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()
        if user.role == User.Role.STUDENT and instance.student.user_id == user.id:
            return super().destroy(request, *args, **kwargs)
        if user.role == User.Role.TEACHER and instance.task.teacher_id == user.id:
            return super().destroy(request, *args, **kwargs)
        raise PermissionDenied("Not allowed to delete this submission.")


def build_task_instances(validated_data, user):
    repeat_type = validated_data.get("repeat_type", Task.RepeatType.NONE)
    start_date = validated_data["due_date"]
    end_date = start_date + timedelta(days=180)
    dates = []

    if repeat_type == Task.RepeatType.DAILY:
        current = start_date
        while current <= end_date:
            dates.append(current)
            current = current + timedelta(days=1)
    elif repeat_type == Task.RepeatType.WEEKLY:
        current = start_date
        while current <= end_date:
            dates.append(current)
            current = current + timedelta(days=7)
    elif repeat_type == Task.RepeatType.MONTHLY:
        current = start_date
        while current <= end_date:
            dates.append(current)
            current = add_months(current, 1)
    else:
        dates.append(start_date)

    tasks = []
    for due_date in dates:
        tasks.append(
            Task(
                title=validated_data.get("title", ""),
                description=validated_data.get("description", ""),
                assigned_to=validated_data.get("assigned_to"),
                company_name=user.company_name,
                created_by=user,
                due_date=due_date,
                due_time=validated_data.get("due_time"),
                status=validated_data.get("status", Task.Status.PENDING),
                priority=validated_data.get("priority", Task.Priority.MEDIUM),
                repeat_type=repeat_type,
            )
        )
    return tasks


def add_months(value: date, months: int) -> date:
    month = value.month - 1 + months
    year = value.year + month // 12
    month = month % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)
def compute_age_groups(queryset):
    buckets = [
        ("<13", 0, 12),
        ("13-17", 13, 17),
        ("18-24", 18, 24),
        ("25-34", 25, 34),
        ("35+", 35, 200),
    ]
    counts = {label: 0 for label, _, _ in buckets}
    for age in queryset.values_list("age", flat=True):
        if age is None:
            continue
        for label, start, end in buckets:
            if start <= age <= end:
                counts[label] += 1
                break
    return [{"label": label, "total": total} for label, total in counts.items()]


class AttendanceMarkView(APIView):
    permission_classes = [IsTeacherOrCourseAdminReadOnly]

    def get(self, request):
        group_id = request.query_params.get("group")
        date_str = request.query_params.get("date")
        if not group_id or not date_str:
            return Response(
                {"detail": "group and date are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group = get_object_or_404(Group, pk=group_id)
        user = request.user
        if user.role == User.Role.MANAGER:
            raise permissions.PermissionDenied("Not allowed for managers.")
        if user.role == User.Role.STUDENT:
            raise permissions.PermissionDenied("Not allowed for students.")
        if user.role in (User.Role.COURSE_ADMIN, User.Role.MANAGER):
            allowed = False
            if group.course:
                if user.role == User.Role.COURSE_ADMIN:
                    allowed = group.course.admins.filter(id=user.id).exists()
                else:
                    allowed = group.course.admins.filter(
                        company_name=user.company_name
                    ).exists()
            if group.company_name and group.company_name == user.company_name:
                allowed = True
            if not allowed:
                raise permissions.PermissionDenied("Not allowed for this course.")
        if user.role == User.Role.TEACHER and group.teacher_id != user.id:
            raise permissions.PermissionDenied("Not allowed for this group.")

        students = list(group.students.all().order_by("first_name", "last_name"))
        existing = Attendance.objects.filter(group=group, date=target_date)
        status_map = {item.student_id: item.status for item in existing}

        return Response(
            {
                "group": {"id": group.id, "name": group.name},
                "date": target_date.isoformat(),
                "students": [
                    {
                        "id": student.id,
                        "first_name": student.first_name,
                        "last_name": student.last_name,
                        "status": status_map.get(student.id),
                    }
                    for student in students
                ],
            }
        )

    def post(self, request):
        if request.user.role in (User.Role.COURSE_ADMIN, User.Role.MANAGER):
            raise permissions.PermissionDenied("Course admins cannot mark attendance.")
        group_id = request.data.get("group")
        date_str = request.data.get("date")
        items = request.data.get("items", [])
        if not group_id or not date_str:
            return Response(
                {"detail": "group and date are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group = get_object_or_404(Group, pk=group_id)
        user = request.user
        if user.role == User.Role.MANAGER:
            raise permissions.PermissionDenied("Not allowed for managers.")
        if user.role == User.Role.STUDENT:
            raise permissions.PermissionDenied("Not allowed for students.")
        if user.role == User.Role.TEACHER and group.teacher_id != user.id:
            raise permissions.PermissionDenied("Not allowed for this group.")

        students = {student.id: student for student in group.students.all()}
        updated = []

        for item in items:
            student_id = item.get("student")
            status_value = item.get("status")
            if student_id not in students:
                continue
            if status_value not in dict(Attendance.Status.choices):
                continue
            record, _ = Attendance.objects.update_or_create(
                group=group,
                student=students[student_id],
                date=target_date,
                defaults={"status": status_value},
            )
            updated.append(record)

        return Response(
            {
                "saved": len(updated),
                "date": target_date.isoformat(),
            }
        )


# Create your views here.

