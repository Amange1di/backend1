"""
Course-admin handlers.

Commands:
  /tasks_stats  — task statistics for the company

Callbacks:
  menu_tasks_stats  — statistics from menu button
"""

from .config import (
    Update,
    ContextTypes,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    User,
    Task,
)
from .helpers import (
    _get_user_by_chat_id,
    _get_task_stats_for_company,
)


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
