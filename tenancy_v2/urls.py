from django.urls import path
from .views import MyCompaniesView, CompanyAccessView
from .branch_views import CompanyBranchesView
from .student_views import CompanyStudentsView

urlpatterns = [
    path('companies/', MyCompaniesView.as_view(), name='v2-my-companies'),
    path('companies/<int:company_id>/access/', CompanyAccessView.as_view(), name='v2-company-access'),
    path('companies/<int:company_id>/branches/', CompanyBranchesView.as_view(), name='v2-company-branches'),
    path('companies/<int:company_id>/students/', CompanyStudentsView.as_view(), name='v2-company-students'),
]
