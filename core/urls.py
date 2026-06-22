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
    HomeworkSubmissionViewSet,
    HomeworkTaskViewSet,
    LandingHeaderLinkViewSet,
    LandingPageViewSet,
    LoginView,
    LogoutView,
    ManagerViewSet,
    MeView,
    PaymentViewSet,
    PublicLandingDetailView,
    PublicLandingLeadCreateView,
    RegisterView,
    StudentLoginView,
    StudentProfileView,
    StudentSetPasswordView,
    StudentViewSet,
    TaskViewSet,
    TeacherViewSet,
    TrialLeadViewSet,
    MarketplaceCompanyViewSet,
    MarketplaceCourseViewSet,
    MarketplaceJobViewSet,
    MyCoursesView,
    MyJobsView,
    PublicCourseViewSet,
    PublicJobViewSet,
    SuperAdminStatsView,
    GenerateTelegramBindCodeView,
    GetTelegramBindCodeView,
    UserBalanceMeView,
    ContractViewSet,
    ContractTemplateViewSet,
    StudentContractsView,
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
router.register("landing-pages", LandingPageViewSet, basename="landing-pages")
router.register("landing-header-links", LandingHeaderLinkViewSet, basename="landing-header-links")
router.register("homework-tasks", HomeworkTaskViewSet, basename="homework-tasks")
router.register("homework-submissions", HomeworkSubmissionViewSet, basename="homework-submissions")
router.register("trial-leads", TrialLeadViewSet, basename="trial-leads")
router.register("tasks", TaskViewSet, basename="tasks")
router.register("contracts", ContractViewSet, basename="contracts")
router.register("contract-templates", ContractTemplateViewSet, basename="contract-templates")

# Marketplace routers
router.register("marketplace/companies", MarketplaceCompanyViewSet, basename="marketplace-companies")
router.register("marketplace/courses", MarketplaceCourseViewSet, basename="marketplace-courses")
router.register("marketplace/jobs", MarketplaceJobViewSet, basename="marketplace-jobs")

# Public marketplace
router.register("public/courses", PublicCourseViewSet, basename="public-courses")
router.register("public/jobs", PublicJobViewSet, basename="public-jobs")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/course-admins/", CourseAdminCreateView.as_view(), name="auth-course-admins"),
    path("auth/course-admins/<int:pk>/", CourseAdminDetailView.as_view(), name="auth-course-admin-detail"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/student/login/", StudentLoginView.as_view(), name="auth-student-login"),
    path("auth/student/set-password/", StudentSetPasswordView.as_view(), name="auth-student-set-password"),
    path("auth/student/profile/", StudentProfileView.as_view(), name="auth-student-profile"),
    path("auth/student/contracts/", StudentContractsView.as_view(), name="auth-student-contracts"),
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
    path("marketplace/my-courses/", MyCoursesView.as_view(), name="marketplace-my-courses"),
    path("marketplace/my-jobs/", MyJobsView.as_view(), name="marketplace-my-jobs"),
    
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
    path("public/landing-pages/<slug:slug>/", PublicLandingDetailView.as_view(), name="public-landing-detail"),
    path("public/landing-pages/<slug:slug>/lead/", PublicLandingLeadCreateView.as_view(), name="public-landing-lead"),
    
    # Router URLs (must be before generic public/ paths)
    path("", include(router.urls)),
]
