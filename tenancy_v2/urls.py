from django.urls import path
from .views import MyCompaniesView, CompanyAccessView

urlpatterns = [
    path('companies/', MyCompaniesView.as_view(), name='v2-my-companies'),
    path('companies/<int:company_id>/access/', CompanyAccessView.as_view(), name='v2-company-access'),
]
