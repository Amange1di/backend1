import logging
import random
from datetime import timedelta

import bleach
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Group, Student, TelegramBindCode, User
from core.permissions import IsCourseAdminOrManager

logger = logging.getLogger(__name__)


class GenerateTelegramBindCodeView(APIView):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request):
        user = request.user

        TelegramBindCode.objects.filter(
            user=user,
            is_used=False,
            expires_at__gt=timezone.now(),
        ).update(is_used=True)

        code = (
            f"{random.randint(0, 999999):06d}"
        )
        expires_at = (
            timezone.now()
            + timedelta(minutes=10)
        )

        bind_code = TelegramBindCode.objects.create(
            user=user,
            code=code,
            expires_at=expires_at,
            is_used=False,
        )

        return Response(
            {
                "code": bind_code.code,
                "expires_at": (
                    bind_code.expires_at.isoformat()
                ),
                "message": (
                    "Код действителен 10 минут. "
                    "Используйте в Telegram: "
                    f"/start {user.username} "
                    f"{bind_code.code}"
                ),
            }
        )


class GetTelegramBindCodeView(APIView):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request):
        pending_code = (
            TelegramBindCode.objects.filter(
                user=request.user,
                is_used=False,
                expires_at__gt=timezone.now(),
            ).first()
        )

        if not pending_code:
            return Response(
                {
                    "code": None,
                    "message": (
                        "Нет активного кода. "
                        "Сгенерируйте новый."
                    ),
                }
            )

        return Response(
            {
                "code": pending_code.code,
                "expires_at": (
                    pending_code.expires_at
                    .isoformat()
                ),
            }
        )


class BroadcastView(APIView):
    permission_classes = [
        IsCourseAdminOrManager
    ]

    def post(self, request):
        user = request.user
        company = user.company

        if not company:
            return Response(
                {
                    "detail": (
                        "Компания не найдена."
                    )
                },
                status=400,
            )

        text = (
            request.data.get("text")
            or ""
        ).strip()
        target = (
            request.data.get("target")
            or ""
        ).strip()
        group_id = request.data.get(
            "group_id"
        )

        if not text:
            return Response(
                {
                    "detail": (
                        "Текст сообщения обязателен."
                    )
                },
                status=400,
            )

        text = bleach.clean(
            text,
            tags=[
                "b",
                "i",
                "u",
                "s",
                "a",
                "code",
                "pre",
            ],
            attributes={
                "a": ["href"]
            },
            protocols=[
                "http",
                "https",
                "mailto",
            ],
            strip=True,
        )

        if len(text) > 4000:
            return Response(
                {
                    "detail": (
                        "Текст сообщения не может "
                        "превышать 4000 символов."
                    )
                },
                status=400,
            )

        recipients = []

        if target == "students":
            students = Student.objects.filter(
                company=company,
                user__isnull=False,
            )
            for student in students:
                if (
                    student.user
                    and student.user.telegram_chat_id
                ):
                    recipients.append(
                        {
                            "name": str(student),
                            "chat_id": (
                                student.user
                                .telegram_chat_id
                            ),
                        }
                    )

        elif target == "teachers":
            teachers = User.objects.filter(
                company=company,
                role=User.Role.TEACHER,
            )
            for teacher in teachers:
                if teacher.telegram_chat_id:
                    recipients.append(
                        {
                            "name": (
                                teacher.get_full_name()
                                or teacher.username
                            ),
                            "chat_id": (
                                teacher.telegram_chat_id
                            ),
                        }
                    )

        elif target == "managers":
            managers = User.objects.filter(
                company=company,
                role=User.Role.MANAGER,
            )
            for manager in managers:
                if manager.telegram_chat_id:
                    recipients.append(
                        {
                            "name": (
                                manager.get_full_name()
                                or manager.username
                            ),
                            "chat_id": (
                                manager.telegram_chat_id
                            ),
                        }
                    )

        elif target == "group" and group_id:
            try:
                group = Group.objects.get(
                    id=group_id,
                    company=company,
                )
            except Group.DoesNotExist:
                return Response(
                    {
                        "detail": (
                            "Группа не найдена."
                        )
                    },
                    status=404,
                )

            for student in group.students.filter(
                user__isnull=False
            ):
                if (
                    student.user
                    and student.user.telegram_chat_id
                ):
                    recipients.append(
                        {
                            "name": str(student),
                            "chat_id": (
                                student.user
                                .telegram_chat_id
                            ),
                        }
                    )
        else:
            return Response(
                {
                    "detail": (
                        f"Неверный target: {target}"
                    )
                },
                status=400,
            )

        if not recipients:
            return Response(
                {
                    "detail": (
                        "Нет получателей с "
                        "привязанным Telegram."
                    )
                },
                status=400,
            )

        from telegram_bot.config import (
            BOT_TOKEN,
            _get_application,
        )

        sent_count = 0
        failed_count = 0
        errors = []

        async def send_messages():
            nonlocal sent_count, failed_count

            if not BOT_TOKEN:
                raise Exception(
                    (
                        "TELEGRAM_BOT_TOKEN "
                        "не настроен"
                    )
                )

            application = _get_application()
            full_text = (
                "📢 <b>Массовая рассылка</b>"
                f"\n\n{text}"
            )

            for recipient in recipients:
                try:
                    await application.bot.send_message(
                        chat_id=recipient[
                            "chat_id"
                        ],
                        text=full_text,
                        parse_mode="HTML",
                    )
                    sent_count += 1
                except Exception as exc:
                    failed_count += 1
                    errors.append(
                        (
                            f"{recipient['name']}: "
                            f"{str(exc)[:100]}"
                        )
                    )
                    logger.warning(
                        (
                            "Broadcast failed for %s: %s"
                        ),
                        recipient["name"],
                        exc,
                    )

        try:
            from asgiref.sync import async_to_sync

            async_to_sync(send_messages)()
        except Exception as exc:
            return Response(
                {
                    "detail": (
                        "Ошибка отправки: "
                        f"{str(exc)}"
                    )
                },
                status=500,
            )

        return Response(
            {
                "sent": sent_count,
                "failed": failed_count,
                "total": len(recipients),
                "errors": errors[:10],
            }
        )
