from django.urls import path
from .views import MyCompaniesView, CompanyAccessView
from .branch_views import CompanyBranchesView
from .student_views import CompanyStudentsView
from .group_views import CompanyGroupsView
from .attendance_views import CompanyAttendanceView
from .schedule_views import CompanyScheduleView
from .finance_views import CompanyFinanceView
from .learning_views import CompanyLibraryView, CompanyHomeworkView
from .learning_write_views import CompanyLibraryCreateView, CompanyHomeworkCreateView

urlpatterns = [
    path('companies/', MyCompaniesView.as_view(), name='v2-my-companies'),
    path('companies/<int:company_id>/access/', CompanyAccessView.as_view(), name='v2-company-access'),
    path('companies/<int:company_id>/branches/', CompanyBranchesView.as_view(), name='v2-company-branches'),
    path('companies/<int:company_id>/students/', CompanyStudentsView.as_view(), name='v2-company-students'),
    path('companies/<int:company_id>/groups/', CompanyGroupsView.as_view(), name='v2-company-groups'),
    path('companies/<int:company_id>/attendance/', CompanyAttendanceView.as_view(), name='v2-company-attendance'),
    path('companies/<int:company_id>/schedule/', CompanyScheduleView.as_view(), name='v2-company-schedule'),
    path('companies/<int:company_id>/finance/', CompanyFinanceView.as_view(), name='v2-company-finance'),
    path('companies/<int:company_id>/library/', CompanyLibraryView.as_view(), name='v2-company-library'),
    path('companies/<int:company_id>/homework/', CompanyHomeworkView.as_view(), name='v2-company-homework'),
    path('companies/<int:company_id>/library/create/', CompanyLibraryCreateView.as_view(), name='v2-library-create'),
    path('companies/<int:company_id>/homework/create/', CompanyHomeworkCreateView.as_view(), name='v2-homework-create'),
]
