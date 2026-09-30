"""Legacy compatibility facade for views.

New code should import views and services from core.domains.<domain>.
"""

from .domains.attendance.views import (
    AttendanceMarkView,
    AttendanceViewSet,
)
from .domains.auditoriums.views import AuditoriumViewSet
from .domains.auth.services import (
    ensure_student_access_allowed,
    get_company_student_cabinet_enabled,
    resolve_support_telegram,
    student_has_allowed_group,
)
from .domains.auth.views import (
    CourseAdminCreateView,
    CourseAdminDetailView,
    LoginThrottle,
    LoginView,
    LogoutView,
    MeView,
    RegisterThrottle,
    RegisterView,
    StudentLoginView,
    StudentProfileView,
    StudentSetPasswordView,
)
from .domains.balances.views import (
    UserBalanceHistoryView,
    UserBalanceMeView,
)
from .domains.contracts.views import (
    ContractTemplateViewSet,
    ContractViewSet,
    StudentContractsView,
)
from .domains.courses.views import CourseViewSet
from .domains.finance.views import (
    ExpenseViewSet,
    FinanceDashboardView,
    FinanceExportView,
    GroupMonthViewSet,
)
from .domains.groups.views import GroupViewSet
from .domains.homework.views import (
    HomeworkSubmissionViewSet,
    HomeworkTaskViewSet,
)
from .domains.landing.views import (
    LandingHeaderLinkViewSet,
    LandingPageViewSet,
    PublicLandingDetailView,
    PublicLandingLeadCreateView,
    PublicReadThrottle,
)
from .domains.managers.views import ManagerViewSet
from .domains.marketplace.views import (
    BoostCourseView,
    BoostJobView,
    MarketplaceCompanyViewSet,
    MarketplaceCourseViewSet,
    MarketplaceJobViewSet,
    MyCoursesView,
    MyJobsView,
    PublicCourseViewSet,
    PublicJobViewSet,
    UrgentCourseView,
    UrgentJobView,
)
from .domains.payments.views import PaymentViewSet
from .domains.promo_codes.views import PromoCodeViewSet
from .domains.public.views import (
    CrmContactView,
    CspReportView,
    PublicSubmitThrottle,
)
from .domains.students.views import StudentViewSet
from .domains.super_admin.views import (
    DashboardView,
    SuperAdminStatsView,
)
from .domains.tasks.views import TaskViewSet
from .domains.teachers.views import TeacherViewSet
from .domains.telegram.views import (
    BroadcastView,
    GenerateTelegramBindCodeView,
    GetTelegramBindCodeView,
)
from .domains.trials.views import TrialLeadViewSet
from .domains.users.services import resolve_user_company_name
