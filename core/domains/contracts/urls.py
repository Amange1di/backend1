from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ContractTemplateViewSet,
    ContractViewSet,
    StudentContractsView,
)

router = DefaultRouter()
router.register("contracts", ContractViewSet, basename="contracts")
router.register(
    "contract-templates",
    ContractTemplateViewSet,
    basename="contract-templates",
)

urlpatterns = [
    path(
        "auth/student/contracts/",
        StudentContractsView.as_view(),
        name="auth-student-contracts",
    ),
    *router.urls,
]
