from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AttendanceMarkView,
    AttendanceViewSet,
    AuditoriumViewSet,
    BroadcastView,
    CourseViewSet,
    DashboardView,
    CourseAdminCreateView,
    CourseAdminDetailView,
    CrmContactView,
    CspReportView,
    ExpenseViewSet,
    FinanceDashboardView,
    FinanceExportView,
    GroupMonthViewSet,
    GroupViewSet,
    LoginView,
    LogoutView,
    ManagerViewSet,
    MeView,
    PaymentViewSet,
    RegisterView,
    StudentLoginView,
    StudentProfileView,
    StudentSetPasswordView,
    StudentViewSet,
    TeacherViewSet,
    SuperAdminStatsView,
    GenerateTelegramBindCodeView,
    GetTelegramBindCodeView,
    UserBalanceMeView,
)
from .sync_views import SyncExportView, SyncImportView

router = DefaultRouter()
router.register("courses", CourseViewSet)
router.register("teachers", TeacherViewSet)
router.register("managers", ManagerViewSet, basename="managers")
router.register("students", StudentViewSet)
router.register("groups", GroupViewSet)
router.register("auditoriums", AuditoriumViewSet)
router.register("attendance", AttendanceViewSet)
router.register("group-months", GroupMonthViewSet)
router.register("expenses", ExpenseViewSet)
router.register("payments", PaymentViewSet)

# Marketplace routers

# Public marketplace

urlpatterns = [
    path("", include("core.domains.landing.urls")),
    path("", include("core.domains.marketplace.urls")),
    path("", include("core.domains.trials.urls")),
    path("", include("core.domains.tasks.urls")),
    path("", include("core.domains.homework.urls")),
    path("", include("core.domains.contracts.urls")),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/course-admins/", CourseAdminCreateView.as_view(), name="auth-course-admins"),
    path("auth/course-admins/<int:pk>/", CourseAdminDetailView.as_view(), name="auth-course-admin-detail"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/student/login/", StudentLoginView.as_view(), name="auth-student-login"),
    path("auth/student/set-password/", StudentSetPasswordView.as_view(), name="auth-student-set-password"),
    path("auth/student/profile/", StudentProfileView.as_view(), name="auth-student-profile"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("super-admin/stats/", SuperAdminStatsView.as_view(), name="super-admin-stats"),
    
    # Broadcast (mass mailing)
    path("broadcast/send/", BroadcastView.as_view(), name="broadcast-send"),
    
    # Finance endpoints
    path("finance/dashboard/", FinanceDashboardView.as_view(), name="finance-dashboard"),
    path("finance/export/<str:export_format>/", FinanceExportView.as_view(), name="finance-export"),
    path("attendance/mark/", AttendanceMarkView.as_view(), name="attendance-mark"),
    
    # Marketplace endpoints
    
    # Telegram bind code generation
    path("bot/generate-bind-code/", GenerateTelegramBindCodeView.as_view(), name="bot-generate-bind-code"),
    path("bot/bind-code/", GetTelegramBindCodeView.as_view(), name="bot-bind-code"),
    
    # CRM website contact form (public, no slug required)
    path("public/crm-contact/", CrmContactView.as_view(), name="crm-contact"),

    # CSP violation report endpoint (POST only, no auth)
    path("csp-report/", CspReportView.as_view(), name="csp-report"),

    # User balance
    path("user/balance/me/", UserBalanceMeView.as_view(), name="user-balance-me"),

    # Server sync endpoints (для синхронизации БД между серверами)
    path("sync/export/", SyncExportView.as_view(), name="sync-export"),
    path("sync/import/", SyncImportView.as_view(), name="sync-import"),

    # Public landing pages (must be after router.urls to avoid conflicting with public/courses and public/jobs)
    
    # Router URLs (must be before generic public/ paths)
    path("", include(router.urls)),
]
