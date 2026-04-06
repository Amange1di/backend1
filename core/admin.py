from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import PermissionDenied

from .models import Attendance, Course, Group, Payment, Student, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "phone", "address", "telegram")},
        ),
        ("Company", {"fields": ("company_name", "created_by")}),
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
                    "company_name",
                    "role",
                ),
            },
        ),
    )
    list_display = (
        "username",
        "phone",
        "telegram",
        "company_name",
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
            if is_super_admin and not obj.company_name:
                raise PermissionDenied("Company name is required for course admins.")
            if not obj.created_by:
                obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "duration_weeks", "created_at")
    search_fields = ("title",)
    filter_horizontal = ("admins",)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "phone",
        "telegram",
        "company_name",
        "primary_course",
        "created_at",
    )
    search_fields = ("first_name", "last_name", "phone", "telegram", "company_name")
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
