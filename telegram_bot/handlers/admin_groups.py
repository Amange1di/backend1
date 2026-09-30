"""
Course-admin handlers.

Commands:
  /tasks_stats  — task statistics for the company
  /resubmit_group <id> — resubmit group request to teacher

Callbacks:
  menu_tasks_stats  — statistics from menu button
  resubmit_group:   — resubmit group after rejection
"""

import bleach
from core.models import User, Task, Group

from ..config import (
    Update,
    ContextTypes,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    logger,
    _get_application,
    sync_to_async,
)
from ..helpers import (
    _get_user_by_chat_id,
    _get_task_stats_for_company,
    _get_group_by_id,
    _get_group_course_name,
    _get_group_company_name,
    _get_course_admins_for_company,
)
from asgiref.sync import async_to_sync
from telegram_bot.notifications import send_group_request_notification

async def resubmit_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resubmit a rejected group to teacher.
    
    Usage: /resubmit_group <group_id>
    Course-admin can resend the group request to the teacher.
    """
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "❌ Используйте: /resubmit_group <group_id>\n"
            "Пример: /resubmit_group 89"
        )
        return

    chat_id = update.effective_chat.id
    user = await _get_user_by_chat_id(chat_id)

    if not user or user.role not in (User.Role.COURSE_ADMIN, User.Role.MANAGER):
        await update.message.reply_text("❌ Доступно только для course-admin или менеджера.")
        return

    try:
        group_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Неверный ID группы. Используйте число.")
        return

    try:
        group = await _get_group_by_id(group_id)
    except Group.DoesNotExist:
        await update.message.reply_text("❌ Группа не найдена.")
        return

    # Check if user has permission (same company)
    if user.role == User.Role.COURSE_ADMIN:
        if not user.company or user.company != group.company:
            await update.message.reply_text("❌ У вас нет прав для этой группы.")
            return

    if group.status != Group.Status.REJECTED:
        await update.message.reply_text(
            f"❌ Можно повторить отправку только для отклонённых групп. "
            f"Текущий статус: {group.status}"
        )
        return

    if not group.teacher:
        await update.message.reply_text("❌ У группы не назначен учитель.")
        return

    # Update status
    group.status = Group.Status.PENDING
    await sync_to_async(group.save)()

    # Send notification to teacher
    try:
        await send_group_request_notification(group)
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

    course_name = await _get_group_course_name(group)
    teacher_name = f"{group.teacher.first_name} {group.teacher.last_name}".strip() or group.teacher.username

    await update.message.reply_text(
        f"✅ Запрос повторно отправлен!\n\n"
        f"📚 <b>Группа:</b> {group.name}\n"
        f"📖 <b>Курс:</b> {course_name}\n"
        f"👨‍🏫 <b>Учитель:</b> {teacher_name}\n\n"
        f"Учитель получил уведомление в Telegram.",
        parse_mode="HTML"
    )

async def resubmit_group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback for resubmit_group from inline button."""
    query = update.callback_query
    
    # Игнорируем устаревшие кнопки
    try:
        await query.answer()
    except Exception:
        # Кнопка устарела - отправляем новое сообщение
        pass

    data = query.data
    if not data.startswith("resubmit_group:"):
        return

    group_id = int(data.split(":")[1])
    chat_id = update.effective_chat.id

    user = await _get_user_by_chat_id(chat_id)
    if not user or user.role not in (User.Role.COURSE_ADMIN, User.Role.MANAGER):
        try:
            await query.answer("❌ Доступно только для course-admin или менеджера.", show_alert=True)
        except Exception:
            pass
        return

    try:
        group = await _get_group_by_id(group_id)
    except Group.DoesNotExist:
        await query.edit_message_text("❌ Группа не найдена.")
        return

    # Check permission - use sync_to_async for company access
    user_company = await sync_to_async(lambda: user.company)()
    group_company = await sync_to_async(lambda: group.company)()
    
    if user.role == User.Role.COURSE_ADMIN:
        if not user_company or user_company != group_company:
            try:
                await query.answer("❌ У вас нет прав для этой группы.", show_alert=True)
            except Exception:
                pass
            return

    if group.status != Group.Status.REJECTED:
        await query.edit_message_text("❌ Можно повторить только для отклонённых групп.")
        return

    if not group.teacher:
        await query.edit_message_text("❌ У группы не назначен учитель.")
        return

    # Update status
    group.status = Group.Status.PENDING
    await sync_to_async(group.save)()

    # Send notification
    try:
        await send_group_request_notification(group)
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

    course_name = await _get_group_course_name(group)
    teacher_name = f"{group.teacher.first_name} {group.teacher.last_name}".strip() or group.teacher.username

    try:
        await query.edit_message_text(
            f"✅ Запрос повторно отправлен!\n\n"
            f"📚 <b>Группа:</b> {group.name}\n"
            f"📖 <b>Курс:</b> {course_name}\n"
            f"👨‍🏫 <b>Учитель:</b> {teacher_name}\n\n"
            f"Учитель получил уведомление.",
            parse_mode="HTML"
        )
    except Exception:
        # Если не удалось отредактировать, отправляем новое сообщение
        await update.effective_message.reply_text(
            f"✅ Запрос повторно отправлен!\n\n"
            f"📚 <b>Группа:</b> {group.name}\n"
            f"📖 <b>Курс:</b> {course_name}\n"
            f"👨‍🏫 <b>Учитель:</b> {teacher_name}\n\n"
            f"Учитель получил уведомление.",
            parse_mode="HTML"
        )
    
    try:
        await query.answer("✅ Запрос отправлен!")
    except Exception:
        pass

