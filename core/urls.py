from django.urls import include, path

from .domains.sync.views import SyncExportView, SyncImportView

urlpatterns = [
    path("", include("core.domains.balances.urls")),
    path("", include("core.domains.public.urls")),
    path("", include("core.domains.telegram.urls")),
    path("", include("core.domains.super_admin.urls")),
    path("", include("core.domains.auth.urls")),
    path("", include("core.domains.finance.urls")),
    path("", include("core.domains.payments.urls")),
    path("", include("core.domains.attendance.urls")),
    path("", include("core.domains.auditoriums.urls")),
    path("", include("core.domains.managers.urls")),
    path("", include("core.domains.teachers.urls")),
    path("", include("core.domains.groups.urls")),
    path("", include("core.domains.students.urls")),
    path("", include("core.domains.courses.urls")),
    path("", include("core.domains.landing.urls")),
    path("", include("core.domains.marketplace.urls")),
    path("", include("core.domains.trials.urls")),
    path("", include("core.domains.tasks.urls")),
    path("", include("core.domains.homework.urls")),
    path("", include("core.domains.contracts.urls")),
    path("sync/export/", SyncExportView.as_view(), name="sync-export"),
    path("sync/import/", SyncImportView.as_view(), name="sync-import"),
]
