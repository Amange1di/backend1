from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import PermissionDenied

from .models import (
    Attendance, Course, Expense, Group, GroupMonth, Payment, Student, User, Company,
    TaskLead, Task, PublicCourse,
    JobVacancy, TrialLead, Auditorium, HomeworkTask, HomeworkSubmission,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "phone", "address", "telegram")},
        ),
        ("Company", {"fields": ("company", "max_managers", "created_by")}),
        (
            "Permissions",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "phone",
                    "address",
                    "telegram",
                    "company",
                    "max_managers",
                    "role",
                ),
            },
        ),
    )
    list_display = (
        "username",
        "phone",
        "telegram",
        "company",
        "max_managers",
        "role",
        "is_staff",
        "is_active",
    )
    list_filter = ("role", "is_staff", "is_active")
    readonly_fields = ("created_by",)

    def save_model(self, request, obj, form, change):
        if not change and request.user.is_authenticated:
            is_super_admin = request.user.is_superuser or request.user.role == User.Role.ADMIN
            if is_super_admin and obj.role != User.Role.COURSE_ADMIN:
                raise PermissionDenied("Super admins can only create course admins.")
            if is_super_admin and not obj.company:
                raise PermissionDenied("Company is required for course admins.")
            if not obj.created_by:
                obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "created_at")
    search_fields = ("title",)
    filter_horizontal = ()


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "first_name",
        "last_name",
        "phone",
        "telegram",
        "company",
        "primary_course",
        "created_at",
    )
    search_fields = ("first_name", "last_name", "phone", "telegram")
    list_filter = ("primary_course",)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "teacher", "start_date", "end_date")
    search_fields = ("name",)
    list_filter = ("course", "teacher")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("group", "student", "date", "status")
    list_filter = ("group", "status", "date")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("student", "group", "amount", "status", "paid_at")
    list_filter = ("status", "paid_at")


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "city", "category", "students_count", "created_at")
    list_filter = ("city", "category", "is_active")
    search_fields = ("name", "slug")
    readonly_fields = ("slug", "created_at", "updated_at")
    
    def students_count(self, obj):
        return obj.students.count()
    students_count.short_description = "Студентов"


@admin.register(TaskLead)
class TaskLeadAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "role", "team_size", "is_active")
    list_filter = ("role", "is_active", "company")
    search_fields = ("user__username", "user__first_name", "user__last_name", "company__name")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "assigned_to", "status", "priority", "due_date")
    list_filter = ("status", "priority", "company")
    search_fields = ("title", "description", "assigned_to__username")


@admin.register(PublicCourse)
class PublicCourseAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "price", "city", "category", "is_active", "is_promoted")
    list_filter = ("is_active", "is_promoted", "category", "city")
    search_fields = ("title", "description", "company__name")


@admin.register(JobVacancy)
class JobVacancyAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "city", "salary_min", "salary_max", "is_active", "is_promoted")
    list_filter = ("is_active", "is_promoted", "category", "city")
    search_fields = ("title", "description", "company__name")


@admin.register(TrialLead)
class TrialLeadAdmin(admin.ModelAdmin):
    list_display = ("full_name", "company", "status", "trial_attended", "converted_to_student", "created_at")
    list_filter = ("status", "trial_attended", "converted_to_student", "company")
    search_fields = ("full_name", "phone", "company__name")


@admin.register(Auditorium)
class AuditoriumAdmin(admin.ModelAdmin):
    list_display = ("name", "number", "company")
    list_filter = ("company",)
    search_fields = ("name", "number", "company__name")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("description", "amount", "category", "date", "company")
    list_filter = ("category", "date", "company")
    search_fields = ("description",)


@admin.register(HomeworkTask)
class HomeworkTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "group", "teacher", "company", "deadline", "task_type")
    list_filter = ("task_type", "target_type", "company")
    search_fields = ("title", "description", "group__name", "teacher__username")


@admin.register(GroupMonth)
class GroupMonthAdmin(admin.ModelAdmin):
    list_display = ("group", "month_number", "teacher_salary", "status", "completed_at")
    list_filter = ("status", "group__course")
    search_fields = ("group__name",)
    readonly_fields = ("created_at",)


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ("task", "student", "status", "grade", "submitted_at")
    list_filter = ("status", "task__task_type")
    search_fields = ("student__first_name", "student__last_name", "task__title")
