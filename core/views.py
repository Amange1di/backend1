from datetime import date, timedelta
import re

from django.db import models
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Attendance, Auditorium, Course, Group, Payment, Student, User
from .permissions import (
    IsAdmin,
    IsCourseAdmin,
    IsCourseAdminOrTeacherReadOnly,
    IsTeacherOrCourseAdminReadOnly,
)
from .serializers import (
    AttendanceSerializer,
    AuditoriumSerializer,
    CourseAdminUpdateSerializer,
    CourseSerializer,
    GroupSerializer,
    LoginSerializer,
    PaymentSerializer,
    RegisterSerializer,
    StudentSerializer,
    UserUpdateSerializer,
    UserSerializer,
)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if (
            request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
        ):
            return Response(
                {"detail": "Admins can only create course admins."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if (
            request.user.is_authenticated
            and request.user.role == User.Role.TEACHER
        ):
            return Response(
                {"detail": "Teachers cannot create users."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if (
            request.user.is_authenticated
            and request.user.role == User.Role.COURSE_ADMIN
        ):
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


class CourseAdminCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        admins = User.objects.filter(role=User.Role.COURSE_ADMIN).order_by("-date_joined")
        return Response(UserSerializer(admins, many=True).data)

    def post(self, request):
        serializer = RegisterSerializer(
            data=request.data, context={"force_role": User.Role.COURSE_ADMIN}
        )
        serializer.is_valid(raise_exception=True)
        company_name = serializer.validated_data.get("company_name", "").strip()
        phone = serializer.validated_data.get("phone", "").strip()
        address = serializer.validated_data.get("address", "").strip()
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
        user = serializer.save(created_by=request.user, company_name=company_name)
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
        serializer = CourseAdminUpdateSerializer(
            admin, data=request.data, partial=True
        )
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
        return Response(
            {
                **data,
                "support_telegram": resolve_support_telegram(request.user),
            }
        )


def resolve_support_telegram(user: User) -> str:
    if user.role == User.Role.COURSE_ADMIN:
        admin = user.created_by if user.created_by and user.created_by.role == User.Role.ADMIN else None
        if admin and admin.telegram:
            return admin.telegram
        admin = User.objects.filter(role=User.Role.ADMIN).order_by("date_joined").first()
        return admin.telegram if admin and admin.telegram else ""
    if user.role == User.Role.TEACHER:
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
            return course_admin.telegram if course_admin and course_admin.telegram else ""
        return ""
    if user.role == User.Role.ADMIN:
        return user.telegram or ""
    return ""


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
        (0, ["mon", "monday", "\u043f\u043d", "\u0434\u04af\u0439", "\u0434\u04af\u0439\u0448"]),
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
    permission_classes = [IsCourseAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(admins=user)
        return queryset

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        admins = serializer.validated_data.get("admins", [])
        if user.role == User.Role.COURSE_ADMIN:
            for admin in admins:
                if admin.company_name != user.company_name:
                    raise PermissionDenied("Course admins can only assign their company admins.")
        course = serializer.save()
        if user.role == User.Role.COURSE_ADMIN:
            course.admins.add(user)
            if admins:
                course.admins.add(*admins)

    def perform_update(self, serializer):
        user = self.request.user
        if user.role == User.Role.COURSE_ADMIN:
            admins = serializer.validated_data.get("admins", None)
            if admins is not None:
                for admin in admins:
                    if admin.company_name != user.company_name:
                        raise PermissionDenied(
                            "Course admins can only assign their company admins."
                        )
        course = serializer.save()
        if user.role == User.Role.COURSE_ADMIN:
            course.admins.add(user)

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        course = self.get_object()
        students_qs = Student.objects.filter(primary_course=course)
        students_count = students_qs.count()
        paid_students = (
            Payment.objects.filter(
                status=Payment.Status.PAID, student__in=students_qs
            )
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
    permission_classes = [IsCourseAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(
                models.Q(primary_course__admins=user)
                | models.Q(groups__course__admins=user)
            ).distinct()
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == User.Role.COURSE_ADMIN:
            course = serializer.validated_data.get("primary_course")
            group_ids = serializer.validated_data.get("group_ids", [])
            auto_course = None
            if course and not course.admins.filter(id=user.id).exists():
                raise PermissionDenied("Not allowed for this course.")
            for group in group_ids:
                if group.course:
                    if not group.course.admins.filter(id=user.id).exists():
                        raise PermissionDenied("Not allowed for this group.")
                elif group.company_name and group.company_name != user.company_name:
                    raise PermissionDenied("Not allowed for this group.")
            if not course and group_ids:
                first_course = group_ids[0].course
                if first_course and all(
                    group.course_id == first_course.id for group in group_ids
                ):
                    auto_course = first_course
            save_kwargs = {"company_name": user.company_name}
            if course:
                save_kwargs["primary_course"] = course
            elif auto_course:
                save_kwargs["primary_course"] = auto_course
            serializer.save(**save_kwargs)
            return
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        if user.role == User.Role.COURSE_ADMIN:
            course = serializer.validated_data.get("primary_course", None)
            if course and not course.admins.filter(id=user.id).exists():
                raise PermissionDenied("Not allowed for this course.")
            group_ids = serializer.validated_data.get("group_ids", [])
            for group in group_ids:
                if group.course:
                    if not group.course.admins.filter(id=user.id).exists():
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
            serializer.save(**save_kwargs)
            return
        serializer.save()


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(role=User.Role.TEACHER).order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsCourseAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(company_name=user.company_name)
        return queryset

    def create(self, request, *args, **kwargs):
        user = request.user
        if user.role == User.Role.ADMIN:
            raise PermissionDenied("Admins cannot create teachers.")
        serializer = RegisterSerializer(
            data=request.data, context={"force_role": User.Role.TEACHER}
        )
        serializer.is_valid(raise_exception=True)
        teacher = serializer.save(
            created_by=user, company_name=user.company_name
        )
        return Response(
            UserSerializer(teacher).data,
            status=status.HTTP_201_CREATED,
        )

    def perform_update(self, serializer):
        user = self.request.user
        if user.role == User.Role.COURSE_ADMIN:
            if "role" in serializer.validated_data and serializer.validated_data[
                "role"
            ] != User.Role.TEACHER:
                raise PermissionDenied("Course admins cannot change roles.")
            if (
                "company_name" in serializer.validated_data
                and serializer.validated_data["company_name"] != user.company_name
            ):
                raise PermissionDenied("Not allowed for this company.")
        serializer.save()

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
                models.Q(course__admins=user)
                | models.Q(company_name=user.company_name)
            ).distinct()
        if user.is_authenticated and user.role == User.Role.TEACHER:
            return queryset.filter(teacher=user)
        return queryset

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == User.Role.COURSE_ADMIN:
            course = serializer.validated_data.get("course")
            if not course or not course.admins.filter(id=user.id).exists():
                raise PermissionDenied("Not allowed for this course.")
            teacher = serializer.validated_data.get("teacher")
            if teacher and teacher.company_name != user.company_name:
                raise PermissionDenied("Teacher must belong to the same company.")
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
        if user.role == User.Role.COURSE_ADMIN:
            course = serializer.validated_data.get("course", None)
            if course and not course.admins.filter(id=user.id).exists():
                raise PermissionDenied("Not allowed for this course.")
            teacher = serializer.validated_data.get("teacher")
            if teacher and teacher.company_name != user.company_name:
                raise PermissionDenied("Teacher must belong to the same company.")
            auditorium = serializer.validated_data.get("auditorium")
            if auditorium and auditorium.company_name != user.company_name:
                raise PermissionDenied("Auditorium must belong to the same company.")
            student_ids = serializer.validated_data.get("student_ids", [])
            for student in student_ids:
                if student.company_name != user.company_name:
                    raise PermissionDenied("Student must belong to the same company.")
        instance = self.get_object()
        self._ensure_auditorium_available(serializer, instance=instance)
        start_date = serializer.validated_data.get("start_date", instance.start_date)
        schedule_days = serializer.validated_data.get("schedule_days", instance.schedule_days)
        lessons_count = serializer.validated_data.get("lessons_count", instance.lessons_count)
        end_date = compute_group_end_date(start_date, schedule_days, lessons_count)
        serializer.save(end_date=end_date)

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
            other_duration = group.course.lesson_duration_minutes if group.course else None
            if not other_duration:
                continue
            other_start = parse_time_to_minutes(group.schedule_time)
            if other_start is None:
                continue
            other_end = other_start + other_duration
            if not time_ranges_overlap(start_minutes, end_minutes, other_start, other_end):
                continue
            other_days = parse_schedule_days(group.schedule_days)
            if not other_days or not days_set.intersection(other_days):
                continue
            if not ranges_overlap(start_date, end_date, group.start_date, group.end_date):
                continue
            raise PermissionDenied("Auditorium is busy at this time.")


class AuditoriumViewSet(viewsets.ModelViewSet):
    queryset = Auditorium.objects.all().order_by("-created_at")
    serializer_class = AuditoriumSerializer
    permission_classes = [IsCourseAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(company_name=user.company_name)
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(company_name=user.company_name)


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all().order_by("-created_at")
    serializer_class = AttendanceSerializer
    permission_classes = [IsTeacherOrCourseAdminReadOnly]

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
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == User.Role.COURSE_ADMIN:
            raise permissions.PermissionDenied("Course admins cannot mark attendance.")
        group = serializer.validated_data.get("group")
        if user.role == User.Role.TEACHER and group.teacher_id != user.id:
            raise permissions.PermissionDenied("Not allowed for this group.")
        serializer.save()


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().order_by("-created_at")
    serializer_class = PaymentSerializer
    permission_classes = [IsCourseAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.COURSE_ADMIN:
            return queryset.filter(
                models.Q(student__primary_course__admins=user)
                | models.Q(group__course__admins=user)
                | models.Q(group__company_name=user.company_name)
            )
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == User.Role.COURSE_ADMIN:
            student = serializer.validated_data.get("student")
            group = serializer.validated_data.get("group")
            allowed = False
            if student and student.primary_course and student.primary_course.admins.filter(
                id=user.id
            ).exists():
                allowed = True
            if group:
                if group.course and group.course.admins.filter(id=user.id).exists():
                    allowed = True
                if group.company_name and group.company_name == user.company_name:
                    allowed = True
            if not allowed:
                raise PermissionDenied("Not allowed for this course.")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        if request.user.role == User.Role.COURSE_ADMIN:
            raise PermissionDenied("Course admins cannot delete payments.")
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
        if user.role == User.Role.COURSE_ADMIN:
            allowed = False
            if group.course and group.course.admins.filter(id=user.id).exists():
                allowed = True
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
        if request.user.role == User.Role.COURSE_ADMIN:
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
