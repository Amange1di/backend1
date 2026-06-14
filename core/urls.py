from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AttendanceMarkView,
    AttendanceViewSet,
    AuditoriumViewSet,
    CourseViewSet,
    DashboardView,
    CourseAdminCreateView,
    CourseAdminDetailView,
    CrmContactView,
    GroupViewSet,
    HomeworkSubmissionViewSet,
    HomeworkTaskViewSet,
    LandingHeaderLinkViewSet,
    LandingPageViewSet,
    LoginView,
    LogoutView,
    ManagerViewSet,
    MeView,
    UserBalanceHistoryView,
    UserBalanceMeView,
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
    PromoCodeViewSet,
    MarketplaceCompanyViewSet,
    MarketplaceCourseViewSet,
    MarketplaceJobViewSet,
    MyCoursesView,
    MyJobsView,
    BoostCourseView,
    BoostJobView,
    UrgentCourseView,
    UrgentJobView,
    PublicCourseViewSet,
    PublicJobViewSet,
    SuperAdminStatsView,
    GenerateTelegramBindCodeView,
    GetTelegramBindCodeView,
)

router = DefaultRouter()
router.register("courses", CourseViewSet)
router.register("teachers", TeacherViewSet)
router.register("managers", ManagerViewSet, basename="managers")
router.register("students", StudentViewSet)
router.register("groups", GroupViewSet)
router.register("auditoriums", AuditoriumViewSet)
router.register("attendance", AttendanceViewSet)
router.register("payments", PaymentViewSet)
router.register("landing-pages", LandingPageViewSet, basename="landing-pages")
router.register("landing-header-links", LandingHeaderLinkViewSet, basename="landing-header-links")
router.register("homework-tasks", HomeworkTaskViewSet, basename="homework-tasks")
router.register("homework-submissions", HomeworkSubmissionViewSet, basename="homework-submissions")
router.register("trial-leads", TrialLeadViewSet, basename="trial-leads")
router.register("tasks", TaskViewSet, basename="tasks")
router.register("admin/promo-codes", PromoCodeViewSet, basename="promo-codes")

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
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("user/balance/me/", UserBalanceMeView.as_view(), name="user-balance-me"),
    path("user/balance/history/", UserBalanceHistoryView.as_view(), name="user-balance-history"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("super-admin/stats/", SuperAdminStatsView.as_view(), name="super-admin-stats"),
    path("attendance/mark/", AttendanceMarkView.as_view(), name="attendance-mark"),
    
    # Marketplace endpoints
    path("marketplace/my-courses/", MyCoursesView.as_view(), name="marketplace-my-courses"),
    path("marketplace/my-jobs/", MyJobsView.as_view(), name="marketplace-my-jobs"),
    path("marketplace/boost-course/<int:pk>/", BoostCourseView.as_view(), name="marketplace-boost-course"),
    path("marketplace/boost-job/<int:pk>/", BoostJobView.as_view(), name="marketplace-boost-job"),
    path("marketplace/urgent-course/<int:pk>/", UrgentCourseView.as_view(), name="marketplace-urgent-course"),
    path("marketplace/urgent-job/<int:pk>/", UrgentJobView.as_view(), name="marketplace-urgent-job"),
    
    # Telegram bind code generation
    path("bot/generate-bind-code/", GenerateTelegramBindCodeView.as_view(), name="bot-generate-bind-code"),
    path("bot/bind-code/", GetTelegramBindCodeView.as_view(), name="bot-bind-code"),
    
    # CRM website contact form (public, no slug required)
    path("public/crm-contact/", CrmContactView.as_view(), name="crm-contact"),

    # Public landing pages (must be after router.urls to avoid conflicting with public/courses and public/jobs)
    path("public/landing-pages/<slug:slug>/", PublicLandingDetailView.as_view(), name="public-landing-detail"),
    path("public/landing-pages/<slug:slug>/lead/", PublicLandingLeadCreateView.as_view(), name="public-landing-lead"),
    
    # Router URLs (must be before generic public/ paths)
    path("", include(router.urls)),
]
