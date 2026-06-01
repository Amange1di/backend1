from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import PermissionDenied

from .models import (
    Attendance, Course, Group, Payment, Student, User, Company,
    CompanyBalance, Transaction, TaskLead, Task, PublicCourse,
    JobVacancy, TrialLead, Auditorium, HomeworkTask, HomeworkSubmission,
    UserBalance, UserTransaction, PromoBalance, PromoTransaction, PromoCode
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "phone", "address", "telegram")},
        ),
        ("Company", {"fields": ("company_name", "max_managers", "created_by")}),
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
        "company_name",
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
            if is_super_admin and not obj.company_name:
                raise PermissionDenied("Company name is required for course admins.")
            if not obj.created_by:
                obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "duration_weeks", "created_at")
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


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "city", "category", "students_count", "balance_display", "created_at")
    list_filter = ("city", "category", "is_active")
    search_fields = ("name", "slug")
    readonly_fields = ("slug", "created_at", "updated_at", "stats_summary")
    
    def students_count(self, obj):
        return obj.students.count()
    students_count.short_description = "Студентов"
    
    def balance_display(self, obj):
        balance = CompanyBalance.objects.filter(company=obj).first()
        if balance:
            return f"{balance.balance} eC"
        return "0 eC"
    balance_display.short_description = "Баланс"
    
    def stats_summary(self, obj):
        students = obj.students.count()
        managers = obj.users.filter(role=User.Role.MANAGER).count()
        teachers = obj.users.filter(role=User.Role.TEACHER).count()
        groups = obj.groups.count()
        balance = CompanyBalance.objects.filter(company=obj).first()
        bal = balance.balance if balance else 0
        return f"Студентов: {students}, Менеджеров: {managers}, Преподавателей: {teachers}, Групп: {groups}, Баланс: {bal} eC"
    stats_summary.short_description = "Статистика компании"
    stats_summary.help_text = "Общая информация о компании"


@admin.register(CompanyBalance)
class CompanyBalanceAdmin(admin.ModelAdmin):
    list_display = ("company", "company_name", "balance", "last_update")
    list_filter = ("company",)
    search_fields = ("company_name", "company__name")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("company", "company_name", "user", "amount", "transaction_type", "timestamp")
    list_filter = ("transaction_type", "timestamp")
    search_fields = ("company_name", "company__name", "user__username")
    readonly_fields = ("timestamp",)


@admin.register(UserBalance)
class UserBalanceAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "last_update")
    list_filter = ("user__role",)
    search_fields = ("user__username", "user__first_name", "user__last_name")


@admin.register(UserTransaction)
class UserTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "transaction_type", "timestamp")
    list_filter = ("transaction_type", "timestamp")
    search_fields = ("user__username",)
    readonly_fields = ("timestamp",)


@admin.register(PromoBalance)
class PromoBalanceAdmin(admin.ModelAdmin):
    list_display = ("promo_code", "balance", "last_update")
    list_filter = ("promo_code__is_active",)
    search_fields = ("promo_code__code",)


@admin.register(PromoTransaction)
class PromoTransactionAdmin(admin.ModelAdmin):
    list_display = ("promo_code", "user", "amount", "transaction_type", "timestamp")
    list_filter = ("transaction_type", "timestamp")
    search_fields = ("promo_code__code", "user__username")
    readonly_fields = ("timestamp",)


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "reward_type", "reward_value", "balance_display", "max_usages", "current_usages", "is_active", "expiry_date")
    list_filter = ("is_active", "reward_type", "expiry_date")
    search_fields = ("code",)
    readonly_fields = ("current_usages", "created_at")
    
    def balance_display(self, obj):
        balance = PromoBalance.objects.filter(promo_code=obj).first()
        if balance:
            return f"{balance.balance} eC"
        return "0 eC"
    balance_display.short_description = "Баланс промокода"


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
    list_display = ("name", "number", "company", "company_name")
    list_filter = ("company",)
    search_fields = ("name", "number", "company_name")


@admin.register(HomeworkTask)
class HomeworkTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "group", "teacher", "company", "deadline", "task_type")
    list_filter = ("task_type", "target_type", "company")
    search_fields = ("title", "description", "group__name", "teacher__username")


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ("task", "student", "status", "grade", "submitted_at")
    list_filter = ("status", "task__task_type")
    search_fields = ("student__first_name", "student__last_name", "task__title")
