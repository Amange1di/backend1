from django.urls import path
from .views import MyCompaniesView, CompanyAccessView, CompanyBranchesView

urlpatterns = [
    path('companies/', MyCompaniesView.as_view(), name='v2-my-companies'),
    path('companies/<int:company_id>/access/', CompanyAccessView.as_view(), name='v2-company-access'),
    path('companies/<int:company_id>/branches/', CompanyBranchesView.as_view(), name='v2-company-branches'),
]
