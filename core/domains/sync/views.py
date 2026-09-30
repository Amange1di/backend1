"""
Views for bidirectional database synchronization between servers.

Каждый сервер может отправить свои данные на другой сервер и получить данные с него.
Используется с management командой `sync_servers`.

Безопасность:
- Требуется заголовок `X-Sync-Secret` с значением из env SYNC_SECRET
- Требуется валидный `Authorization: Token <token>` админа

ВАЖНО: Для production рекомендуется использовать единую БД вместо синхронизации.
См. README для инструкции.
"""

import json
import logging

from django.conf import settings
from django.core import serializers
from django.db import transaction
from django.http import HttpResponse
from rest_framework import permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def _check_sync_secret(request) -> bool:
    """Проверяет заголовок X-Sync-Secret."""
    sync_secret = getattr(settings, "SYNC_SECRET", None) or ""
    if not sync_secret:
        logger.warning("SYNC_SECRET not configured — sync endpoints disabled")
        return False
    header_secret = request.headers.get("X-Sync-Secret", "")
    return header_secret == sync_secret


# Модели в порядке зависимостей (FK: родитель ДО дочернего)
SYNC_MODELS_ORDERED = [
    # 1. Базовые справочники
    "core.Company",
    "core.Course",
    "core.User",
    "core.Auditorium",
    # 2. Зависимые от базовых
    "core.Student",
    "core.Group",
    "core.GroupMonth",
    "core.Payment",
    # 3. Образование / посещаемость
    "core.Attendance",
    "core.HomeworkTask",
    "core.HomeworkTaskAttachment",
    "core.HomeworkSubmission",
    # 4. Маркетплейс
    "core.PublicCourse",
    "core.JobVacancy",
    "core.StudentApplication",
    "core.TeacherApplication",
    "core.CourseApplication",
    # 5. Лендинги
    "core.LandingPage",
    "core.LandingSection",
    "core.LandingHeaderLink",
    # 6. Лиды / задачи
    "core.TrialLead",
    "core.LeadAssignment",
    "core.Task",
    "core.TaskLead",
    # 7. Финансы
    "core.CompanyBalance",
    "core.Transaction",
    "core.UserBalance",
    "core.UserTransaction",
    "core.PromoCode",
    "core.PromoBalance",
    "core.PromoTransaction",
    # 8. Расходы
    "core.Expense",
    # 9. Telegram
    "core.TelegramBindCode",
    # 10. Finance app
    "finance.ExpenseItem",
]


def _get_sync_objects():
    """Возвращает все объекты для синхронизации, упорядоченные по зависимостям."""
    from django.apps import apps

    for label in SYNC_MODELS_ORDERED:
        if "." not in label:
            continue
        try:
            app_label, model_name = label.split(".", 1)
            model = apps.get_model(app_label, model_name)
            if model and model._meta.managed:
                yield from model.objects.all().iterator()
        except (LookupError, ValueError):
            continue


def _save_or_update(deserialized_obj):
    """
    Сохраняет объект: если запись с таким PK уже есть — обновляет поля,
    иначе создаёт новую. Избегает IntegrityError при дублировании PK.
    """
    obj = deserialized_obj.object
    model_class = obj.__class__
    pk = obj.pk

    try:
        existing = model_class.objects.get(pk=pk)
        # Обновляем существующую запись (только concrete поля, без PK)
        concrete_fields = [
            f for f in model_class._meta.local_concrete_fields if not f.primary_key
        ]
        for field in concrete_fields:
            setattr(existing, field.attname, getattr(obj, field.attname))
        existing.save()

        # Сохраняем M2M отношения через DeserializedObject
        if hasattr(deserialized_obj, "save_m2m") and deserialized_obj.save_m2m is not None:
            # Временно подменяем объект, чтобы save_m2m работала с existing
            original_obj = deserialized_obj.object
            deserialized_obj.object = existing
            try:
                deserialized_obj.save_m2m()
            finally:
                deserialized_obj.object = original_obj
    except model_class.DoesNotExist:
        deserialized_obj.save()


class SyncExportView(APIView):
    """
    GET /api/sync/export/
    Экспортирует данные в формате JSON.
    Только для супер-админа с SYNC_SECRET.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not _check_sync_secret(request):
            return Response(
                {"detail": "Invalid sync secret."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if request.user.role not in ("admin", "super_admin"):
            return Response(
                {"detail": "Only admins can export data."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            objects = list(_get_sync_objects())
            data = serializers.serialize(
                "json",
                objects,
                indent=2,
                use_natural_foreign_keys=True,
                use_natural_primary_keys=True,
            )
            logger.info(
                f"Sync export: {len(objects)} objects exported by "
                f"{request.user.username}"
            )
            return HttpResponse(data, content_type="application/json")
        except Exception as e:
            logger.error(f"Sync export failed: {e}")
            return Response(
                {"detail": f"Export failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SyncImportView(APIView):
    """
    POST /api/sync/import/
    Принимает JSON-дамп и загружает его с обновлением существующих записей.
    Только для супер-админа с SYNC_SECRET.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not _check_sync_secret(request):
            return Response(
                {"detail": "Invalid sync secret."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if request.user.role not in ("admin", "super_admin"):
            return Response(
                {"detail": "Only admins can import data."},
                status=status.HTTP_403_FORBIDDEN,
            )

        raw_data = request.body
        if not raw_data:
            return Response(
                {"detail": "No data provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data = json.loads(raw_data)
            if not isinstance(data, list):
                return Response(
                    {"detail": "Expected a JSON array."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except json.JSONDecodeError:
            return Response(
                {"detail": "Invalid JSON."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                objects = serializers.deserialize("json", raw_data)
                count = 0
                for obj in objects:
                    _save_or_update(obj)
                    count += 1

            logger.info(
                f"Sync import: {count} objects imported from "
                f"{request.META.get('REMOTE_ADDR', 'unknown')}"
            )

            return Response({
                "status": "ok",
                "imported": count,
            })
        except Exception as e:
            logger.error(f"Sync import failed: {e}")
            return Response(
                {"detail": f"Import failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
