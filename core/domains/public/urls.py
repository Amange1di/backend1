from django.urls import path

from .views import (
    CrmContactView,
    CspReportView,
)

urlpatterns = [
    path(
        "public/crm-contact/",
        CrmContactView.as_view(),
        name="crm-contact",
    ),
    path(
        "csp-report/",
        CspReportView.as_view(),
        name="csp-report",
    ),
]
