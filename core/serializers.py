"""Legacy compatibility facade for serializers.

New code should import serializers from core.domains.<domain>.serializers.
"""

from .domains.applications.serializers import (
    StudentApplicationSerializer,
    TeacherApplicationSerializer,
)
from .domains.attendance.serializers import AttendanceSerializer
from .domains.auditoriums.serializers import AuditoriumSerializer
from .domains.contracts.serializers import (
    ContractSerializer,
    ContractTemplateSerializer,
)
from .domains.courses.serializers import CourseSerializer
from .domains.finance.serializers import (
    ExpenseSerializer,
    GroupMonthSerializer,
)
from .domains.groups.serializers import GroupSerializer
from .domains.homework.serializers import (
    HomeworkSubmissionSerializer,
    HomeworkTaskAttachmentSerializer,
    HomeworkTaskSerializer,
)
from .domains.landing.serializers import (
    LandingHeaderLinkSerializer,
    LandingPageSerializer,
    LandingPublicPageSerializer,
    LandingPublicSectionSerializer,
    LandingSectionSerializer,
)
from .domains.marketplace.serializers import (
    CompanyCreateUpdateSerializer,
    CompanySerializer,
    JobVacancyDetailSerializer,
    JobVacancySerializer,
    PublicCourseSerializer,
)
from .domains.payments.serializers import PaymentSerializer
from .domains.promo_codes.serializers import PromoCodeSerializer
from .domains.students.serializers import (
    StudentSerializer,
    TransferGroupSerializer,
)
from .domains.students.services import (
    build_student_username,
    normalize_phone,
    sync_student_user,
)
from .domains.tasks.serializers import TaskSerializer
from .domains.trials.serializers import TrialLeadSerializer
from .domains.users.serializers import (
    CourseAdminUpdateSerializer,
    LoginSerializer,
    RegisterSerializer,
    StudentIdentityLoginSerializer,
    StudentProfileSerializer,
    StudentSetPasswordSerializer,
    TeacherCreateSerializer,
    TeacherUpdateSerializer,
    UserSerializer,
)
