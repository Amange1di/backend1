from django.urls import path
from rest_framework.routers import DefaultRouter

from .document_views import DocumentDispatchView, MyDocumentsView, DocumentReceiptActionView
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
    path('document-dispatches/', DocumentDispatchView.as_view(), name='document-dispatches'),
    path('my-documents/', MyDocumentsView.as_view(), name='my-documents'),
    path('my-documents/<int:pk>/<str:action>/', DocumentReceiptActionView.as_view(), name='my-document-action'),
    path(
        "auth/student/contracts/",
        StudentContractsView.as_view(),
        name="auth-student-contracts",
    ),
    *router.urls,
]
