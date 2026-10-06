from django.urls import include, path

from .domains.applications import urls as applications_urls
from .domains.attendance import urls as attendance_urls
from .domains.auditoriums import urls as auditoriums_urls
from .domains.auth import urls as auth_urls
from .domains.balances import urls as balances_urls
from .domains.contracts import urls as contracts_urls
from .domains.courses import urls as courses_urls
from .domains.finance import urls as finance_urls
from .domains.groups import urls as groups_urls
from .domains.homework import urls as homework_urls
from .domains.landing import urls as landing_urls
from .domains.library import urls as library_urls
from .domains.managers import urls as managers_urls
from .domains.marketplace import urls as marketplace_urls
from .domains.payments import urls as payments_urls
from .domains.promo_codes import urls as promo_codes_urls
from .domains.public_api import urls as public_urls
from .domains.students import urls as students_urls
from .domains.super_admin import urls as super_admin_urls
from .domains.sync.views import SyncExportView, SyncImportView
from .domains.tasks import urls as tasks_urls
from .domains.teachers import urls as teachers_urls
from .domains.telegram import urls as telegram_urls
from .domains.trials import urls as trials_urls

urlpatterns = [
    path("", include(balances_urls)),
    path("", include(public_urls)),
    path("", include(promo_codes_urls)),
    path("", include(telegram_urls)),
    path("", include(super_admin_urls)),
    path("", include(auth_urls)),
    path("", include(finance_urls)),
    path("", include(payments_urls)),
    path("", include(attendance_urls)),
    path("", include(auditoriums_urls)),
    path("", include(managers_urls)),
    path("", include(teachers_urls)),
    path("", include(groups_urls)),
    path("", include(students_urls)),
    path("", include(courses_urls)),
    path("", include(landing_urls)),
    path("", include(marketplace_urls)),
    path("", include(applications_urls)),
    path("", include(trials_urls)),
    path("", include(tasks_urls)),
    path("", include(homework_urls)),
    path("", include(library_urls)),
    path("", include(contracts_urls)),
    path("sync/export/", SyncExportView.as_view(), name="sync-export"),
    path("sync/import/", SyncImportView.as_view(), name="sync-import"),
]
