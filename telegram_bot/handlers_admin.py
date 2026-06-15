"""
Course-admin handlers.

Commands:
  /tasks_stats  — task statistics for the company
  /resubmit_group <id> — resubmit group request to teacher

Callbacks:
  menu_tasks_stats  — statistics from menu button
  resubmit_group:   — resubmit group after rejection
"""

from core.models import User, Task, Group

from .config import (
    Update,
    ContextTypes,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    logger,
    _get_application,
    sync_to_async,
)
from .helpers import (
    _get_user_by_chat_id,
    _get_task_stats_for_company,
    _get_group_by_id,
    _get_group_course_name,
    _get_group_company_name,
    _get_course_admins_for_company,
)
from asgiref.sync import async_to_sync
from telegram_bot.notifications import send_group_request_notification


async def tasks_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show task statistics for a course-admin's company.

    Usage: /tasks_stats
    Shows total tasks, by status, overdue, completed on time vs overdue.
    """
    chat_id = update.effective_chat.id
    user = await _get_user_by_chat_id(chat_id)

    if not user:
        await update.message.reply_text("❌ Вы не зарегистрированы. Используйте /start ваш_username")
        return

    if user.role != User.Role.COURSE_ADMIN:
        await update.message.reply_text("❌ Команда /tasks_stats доступна только для course-admin.")
        return

    if not user.company:
        await update.message.reply_text("❌ У вас не привязана компания. Обратитесь к администратору.")
        return

    stats = await _get_task_stats_for_company(user.company)

    lines = [f"📊 <b>Статистика задач</b>"]
    lines.append(f"🏢 <b>{user.company.name}</b>\n")

    lines.append(f"📋 <b>Всего задач:</b> {stats['total']}")
    lines.append(f"🕐 Ожидают: {stats['pending']}")
    lines.append(f"🔄 В работе: {stats['in_progress']}")
    lines.append(f"✅ Завершено: {stats['completed']}")
    lines.append(f"👥 Менеджеров: {stats['managers_count']}\n")

    lines.append(f"⚠️ <b>Просрочено:</b> {stats['overdue']}")
    if stats['overdue'] > 0:
        lines.append(f"   🔴 Высокий приоритет: {stats['high']} задач")

    if stats['completed'] > 0:
        pct_on_time = round(stats['completed_on_time'] / stats['completed'] * 100)
        lines.append(f"\n✅ <b>Качество выполнения:</b>")
        lines.append(f"   🟢 В срок: {stats['completed_on_time']} ({pct_on_time}%)")
        lines.append(f"   🔴 С опозданием: {stats['completed_overdue']}")

    if stats['top_overdue']:
        priority_emoji = {
            Task.Priority.LOW: "🟢",
            Task.Priority.MEDIUM: "🟡",
            Task.Priority.HIGH: "🔴",
        }
        lines.append(f"\n⏰ <b>Самые просроченные:</b>")
        for t in stats['top_overdue']:
            pr = priority_emoji.get(t.priority, "🟡")
            manager_name = (
                f"{t.assigned_to.first_name} {t.assigned_to.last_name}".strip()
                or t.assigned_to.username
                if t.assigned_to
                else "—"
            )
            deadline = t.due_date.strftime("%d.%m.%Y")
            lines.append(f"   {pr} <b>{t.title[:30]}</b>")
            lines.append(f"      👤 {manager_name} — ⏰ {deadline}")

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 В меню", callback_data="menu_back")
    ]])

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def menu_tasks_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle menu 'Статистика задач' button — calls tasks_stats logic."""
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    user = await _get_user_by_chat_id(chat_id)
    if not user or user.role != User.Role.COURSE_ADMIN:
        await query.answer("❌ Доступно только для course-admin.", show_alert=True)
        return

    if not user.company:
        await query.edit_message_text("❌ У вас не привязана компания.")
        return

    stats = await _get_task_stats_for_company(user.company)

    lines = [f"📊 <b>Статистика задач</b>"]
    lines.append(f"🏢 <b>{user.company.name}</b>\n")

    lines.append(f"📋 <b>Всего задач:</b> {stats['total']}")
    lines.append(f"🕐 Ожидают: {stats['pending']}")
    lines.append(f"🔄 В работе: {stats['in_progress']}")
    lines.append(f"✅ Завершено: {stats['completed']}")
    lines.append(f"👥 Менеджеров: {stats['managers_count']}\n")

    lines.append(f"⚠️ <b>Просрочено:</b> {stats['overdue']}")
    if stats['overdue'] > 0:
        lines.append(f"   🔴 Высокий приоритет: {stats['high']} задач")

    if stats['completed'] > 0:
        pct_on_time = round(stats['completed_on_time'] / stats['completed'] * 100)
        lines.append(f"\n✅ <b>Качество выполнения:</b>")
        lines.append(f"   🟢 В срок: {stats['completed_on_time']} ({pct_on_time}%)")
        lines.append(f"   🔴 С опозданием: {stats['completed_overdue']}")

    if stats['top_overdue']:
        priority_emoji = {
            Task.Priority.LOW: "🟢",
            Task.Priority.MEDIUM: "🟡",
            Task.Priority.HIGH: "🔴",
        }
        lines.append(f"\n⏰ <b>Самые просроченные:</b>")
        for t in stats['top_overdue']:
            pr = priority_emoji.get(t.priority, "🟡")
            manager_name = (
                f"{t.assigned_to.first_name} {t.assigned_to.last_name}".strip()
                or t.assigned_to.username
                if t.assigned_to
                else "—"
            )
            deadline = t.due_date.strftime("%d.%m.%Y")
            lines.append(f"   {pr} <b>{t.title[:30]}</b>")
            lines.append(f"      👤 {manager_name} — ⏰ {deadline}")

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 В меню", callback_data="menu_back")
    ]])

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ═══════════════════════════════════════════════════════════════════════
#  RESUBMIT GROUP
# ═══════════════════════════════════════════════════════════════════════

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

