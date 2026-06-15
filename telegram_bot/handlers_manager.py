"""
Manager handlers.

Commands:
  /tasks  — list tasks (all / active / completed)

Callbacks:
  menu_tasks           — tasks from menu button
  task_set:<id>:<st>   — change task status
  task_filter:<name>   — filter task list
  claim:<lead_id>      — claim a lead
"""

import re

from core.models import Task, User, TrialLead

from .config import (
    Update,
    ContextTypes,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    logger,
)
from .helpers import (
    _get_user_by_chat_id,
    _get_manager_tasks_by_status,
    _get_task_by_id,
    _update_task_status,
    _get_lead_by_id,
    _get_lead_assignment,
    _create_lead_assignment,
    _update_lead_assignment,
    _update_lead_status_contacted,
)
from .notifications import send_task_status_changed_notification


# ═══════════════════════════════════════════════════════════════════════
#  TASKS COMMAND
# ═══════════════════════════════════════════════════════════════════════

async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the manager's tasks.

    Usage:
      /tasks — show all tasks grouped by status
      /tasks active — show only active tasks (pending, in_progress)
      /tasks completed — show only completed tasks
    """
    chat_id = update.effective_chat.id
    user = await _get_user_by_chat_id(chat_id)

    if not user:
        await update.message.reply_text("❌ Вы не зарегистрированы. Используйте /start ваш_username")
        return

    if user.role != User.Role.MANAGER:
        await update.message.reply_text("❌ Команда /tasks доступна только для менеджеров.")
        return

    query = " ".join(context.args).lower() if context.args else ""

    if query == "completed":
        all_tasks = await _get_manager_tasks_by_status(user, Task.Status.COMPLETED)
        sections = [("✅ Завершённые", all_tasks)]
    elif query == "active":
        pending = await _get_manager_tasks_by_status(user, Task.Status.PENDING)
        in_progress = await _get_manager_tasks_by_status(user, Task.Status.IN_PROGRESS)
        sections = [("🕐 Ожидают", pending), ("🔄 В работе", in_progress)]
    else:
        pending = await _get_manager_tasks_by_status(user, Task.Status.PENDING)
        in_progress = await _get_manager_tasks_by_status(user, Task.Status.IN_PROGRESS)
        completed = await _get_manager_tasks_by_status(user, Task.Status.COMPLETED)
        sections = [("🕐 Ожидают", pending), ("🔄 В работе", in_progress), ("✅ Завершённые", completed)]

    total = sum(len(tasks) for _, tasks in sections)
    if total == 0:
        await update.message.reply_text(
            "📋 <b>Мои задачи</b>\n\n🎉 У вас нет задач.",
            parse_mode="HTML",
        )
        return

    priority_emoji = {
        Task.Priority.LOW: "🟢",
        Task.Priority.MEDIUM: "🟡",
        Task.Priority.HIGH: "🔴",
    }

    lines = [f"📋 <b>Мои задачи</b> ({total})\n"]
    for section_title, section_tasks in sections:
        if not section_tasks:
            continue
        lines.append(f"\n{section_title} ({len(section_tasks)}):")
        for t in section_tasks[:10]:
            priority = priority_emoji.get(t.priority, "🟡")
            deadline = t.due_date.strftime("%d.%m.%Y")
            if t.due_time:
                deadline += f" {t.due_time.strftime('%H:%M')}"
            lines.append(
                f"\n{priority} <b>{t.title}</b>\n"
                f"   ⏰ {deadline}"
            )
            if t.description:
                lines.append(f"   📄 {t.description[:150]}")
        if len(section_tasks) > 10:
            lines.append(f"\n   ... и ещё {len(section_tasks) - 10} задач")

    # Build keyboard
    keyboard = [
        [
            InlineKeyboardButton("📋 Все", callback_data="task_filter:all"),
            InlineKeyboardButton("🔄 Активные", callback_data="task_filter:active"),
            InlineKeyboardButton("✅ Завершённые", callback_data="task_filter:completed"),
        ],
    ]
    for section_title, section_tasks in sections:
        for t in section_tasks[:10]:
            if t.status == Task.Status.PENDING:
                title_short = t.title[:25] + "…" if len(t.title) > 25 else t.title
                keyboard.append([
                    InlineKeyboardButton(f"▶️ {title_short}", callback_data=f"task_set:{t.id}:in_progress")
                ])
            elif t.status == Task.Status.IN_PROGRESS:
                title_short = t.title[:25] + "…" if len(t.title) > 25 else t.title
                keyboard.append([
                    InlineKeyboardButton(f"✅ {title_short}", callback_data=f"task_set:{t.id}:completed")
                ])

    keyboard.append([InlineKeyboardButton("🔙 В меню", callback_data="menu_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=reply_markup,
    )


async def menu_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle menu 'Мои задачи' button — shows manager's tasks."""
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    user = await _get_user_by_chat_id(chat_id)
    if not user or user.role != User.Role.MANAGER:
        await query.answer("❌ Доступно только для менеджеров.", show_alert=True)
        return

    pending = await _get_manager_tasks_by_status(user, Task.Status.PENDING)
    in_progress = await _get_manager_tasks_by_status(user, Task.Status.IN_PROGRESS)
    completed = await _get_manager_tasks_by_status(user, Task.Status.COMPLETED)

    total = len(pending) + len(in_progress) + len(completed)

    priority_emoji = {
        Task.Priority.LOW: "🟢",
        Task.Priority.MEDIUM: "🟡",
        Task.Priority.HIGH: "🔴",
    }

    lines = [f"📋 <b>Мои задачи</b> ({total})"]
    if total == 0:
        lines.append("\n🎉 У вас нет задач.")
    else:
        sections = [
            ("🕐 Ожидают", pending),
            ("🔄 В работе", in_progress),
            ("✅ Завершённые", completed),
        ]
        for section_title, section_tasks in sections:
            if not section_tasks:
                continue
            lines.append(f"\n{section_title} ({len(section_tasks)}):")
            for t in section_tasks[:10]:
                priority = priority_emoji.get(t.priority, "🟡")
                deadline = t.due_date.strftime("%d.%m.%Y")
                if t.due_time:
                    deadline += f" {t.due_time.strftime('%H:%M')}"
                lines.append(
                    f"\n{priority} <b>{t.title}</b>\n"
                    f"   ⏰ {deadline}"
                )
                if t.description:
                    lines.append(f"   📄 {t.description[:150]}")
            if len(section_tasks) > 10:
                lines.append(f"\n   ... и ещё {len(section_tasks) - 10} задач")

    # Build keyboard with filters and status buttons
    keyboard = [
        [
            InlineKeyboardButton("📋 Все", callback_data="task_filter:all"),
            InlineKeyboardButton("🔄 Активные", callback_data="task_filter:active"),
            InlineKeyboardButton("✅ Завершённые", callback_data="task_filter:completed"),
        ],
    ]
    for t in pending[:10]:
        title_short = t.title[:25] + "…" if len(t.title) > 25 else t.title
        keyboard.append([
            InlineKeyboardButton(f"▶️ {title_short}", callback_data=f"task_set:{t.id}:in_progress")
        ])
    for t in in_progress[:10]:
        title_short = t.title[:25] + "…" if len(t.title) > 25 else t.title
        keyboard.append([
            InlineKeyboardButton(f"✅ {title_short}", callback_data=f"task_set:{t.id}:completed")
        ])

    keyboard.append([InlineKeyboardButton("🔙 В меню", callback_data="menu_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "\n".join(lines)
    if len(text) > 4000:
        plain = re.sub(r"<[^>]+>", "", text)[:3997] + "..."
        await query.edit_message_text(plain, reply_markup=reply_markup)
    else:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)


# ═══════════════════════════════════════════════════════════════════════
#  CHANGE TASK STATUS (callback)
# ═══════════════════════════════════════════════════════════════════════

async def task_set_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle status change button on a task.

    Callback data: task_set:<task_id>:<new_status>
    """
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("task_set:"):
        return

    parts = data.split(":")
    if len(parts) != 3:
        return

    task_id = int(parts[1])
    new_status = parts[2]

    if new_status not in [Task.Status.IN_PROGRESS, Task.Status.COMPLETED]:
        await query.answer("❌ Неверный статус.", show_alert=True)
        return

    chat_id = update.effective_chat.id
    user = await _get_user_by_chat_id(chat_id)
    if not user or user.role != User.Role.MANAGER:
        await query.answer("❌ Доступно только для менеджеров.", show_alert=True)
        return

    try:
        task = await _get_task_by_id(task_id)
    except Task.DoesNotExist:
        await query.answer("❌ Задача не найдена.", show_alert=True)
        return

    if task.assigned_to_id != user.id:
        await query.answer("❌ Это не ваша задача.", show_alert=True)
        return

    if task.status == new_status:
        await query.answer(f"✅ Задача уже в статусе «{task.get_status_display()}».", show_alert=True)
        return

    await _update_task_status(task_id, new_status)

    status_text = {
        Task.Status.IN_PROGRESS: "🔄 В работе",
        Task.Status.COMPLETED: "✅ Завершена",
    }

    try:
        task_refreshed = await _get_task_by_id(task_id)
        await send_task_status_changed_notification(task_refreshed)
    except Exception as e:
        logger.error(f"Failed to send status change notification: {e}")

    await query.answer(f"✅ Статус изменён на «{status_text.get(new_status, new_status)}»", show_alert=True)

    # Rebuild the message with current data
    pending = await _get_manager_tasks_by_status(user, Task.Status.PENDING)
    in_progress = await _get_manager_tasks_by_status(user, Task.Status.IN_PROGRESS)
    completed = await _get_manager_tasks_by_status(user, Task.Status.COMPLETED)

    total = len(pending) + len(in_progress) + len(completed)

    priority_emoji = {
        Task.Priority.LOW: "🟢",
        Task.Priority.MEDIUM: "🟡",
        Task.Priority.HIGH: "🔴",
    }

    lines = [f"📋 <b>Мои задачи</b> ({total})"]
    if total == 0:
        lines.append("\n🎉 У вас нет задач.")
    else:
        sections = [
            ("🕐 Ожидают", pending),
            ("🔄 В работе", in_progress),
            ("✅ Завершённые", completed),
        ]
        for section_title, section_tasks in sections:
            if not section_tasks:
                continue
            lines.append(f"\n{section_title} ({len(section_tasks)}):")
            for t in section_tasks[:10]:
                priority = priority_emoji.get(t.priority, "🟡")
                deadline = t.due_date.strftime("%d.%m.%Y")
                if t.due_time:
                    deadline += f" {t.due_time.strftime('%H:%M')}"
                lines.append(
                    f"\n{priority} <b>{t.title}</b>\n"
                    f"   ⏰ {deadline}"
                )
                if t.description:
                    lines.append(f"   📄 {t.description[:150]}")
            if len(section_tasks) > 10:
                lines.append(f"\n   ... и ещё {len(section_tasks) - 10} задач")

    keyboard = [
        [
            InlineKeyboardButton("📋 Все", callback_data="task_filter:all"),
            InlineKeyboardButton("🔄 Активные", callback_data="task_filter:active"),
            InlineKeyboardButton("✅ Завершённые", callback_data="task_filter:completed"),
        ],
    ]
    for t in pending[:10]:
        title_short = t.title[:25] + "…" if len(t.title) > 25 else t.title
        keyboard.append([
            InlineKeyboardButton(f"▶️ {title_short}", callback_data=f"task_set:{t.id}:in_progress")
        ])
    for t in in_progress[:10]:
        title_short = t.title[:25] + "…" if len(t.title) > 25 else t.title
        keyboard.append([
            InlineKeyboardButton(f"✅ {title_short}", callback_data=f"task_set:{t.id}:completed")
        ])

    keyboard.append([InlineKeyboardButton("🔙 В меню", callback_data="menu_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "\n".join(lines)
    if len(text) > 4000:
        plain = re.sub(r"<[^>]+>", "", text)[:3997] + "..."
        await query.edit_message_text(plain, reply_markup=reply_markup)
    else:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)


# ═══════════════════════════════════════════════════════════════════════
#  TASK FILTER (callback)
# ═══════════════════════════════════════════════════════════════════════

async def task_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle filter button on the tasks view.

    Callback data: task_filter:<filter_name>
    filter_name: all | active | completed
    """
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("task_filter:"):
        return

    filter_name = data.split(":")[1]
    if filter_name not in ("all", "active", "completed"):
        return

    chat_id = update.effective_chat.id
    user = await _get_user_by_chat_id(chat_id)
    if not user or user.role != User.Role.MANAGER:
        await query.answer("❌ Доступно только для менеджеров.", show_alert=True)
        return

    if filter_name == "completed":
        all_tasks = await _get_manager_tasks_by_status(user, Task.Status.COMPLETED)
        sections = [("✅ Завершённые", all_tasks)]
    elif filter_name == "active":
        pending = await _get_manager_tasks_by_status(user, Task.Status.PENDING)
        in_progress = await _get_manager_tasks_by_status(user, Task.Status.IN_PROGRESS)
        sections = [("🕐 Ожидают", pending), ("🔄 В работе", in_progress)]
    else:
        pending = await _get_manager_tasks_by_status(user, Task.Status.PENDING)
        in_progress = await _get_manager_tasks_by_status(user, Task.Status.IN_PROGRESS)
        completed = await _get_manager_tasks_by_status(user, Task.Status.COMPLETED)
        sections = [("🕐 Ожидают", pending), ("🔄 В работе", in_progress), ("✅ Завершённые", completed)]

    total = sum(len(tasks) for _, tasks in sections)

    priority_emoji = {
        Task.Priority.LOW: "🟢",
        Task.Priority.MEDIUM: "🟡",
        Task.Priority.HIGH: "🔴",
    }

    lines = [f"📋 <b>Мои задачи</b> ({total})"]
    if total == 0:
        lines.append("\n🎉 У вас нет задач.")
    else:
        for section_title, section_tasks in sections:
            if not section_tasks:
                continue
            lines.append(f"\n{section_title} ({len(section_tasks)}):")
            for t in section_tasks[:10]:
                priority = priority_emoji.get(t.priority, "🟡")
                deadline = t.due_date.strftime("%d.%m.%Y")
                if t.due_time:
                    deadline += f" {t.due_time.strftime('%H:%M')}"
                lines.append(
                    f"\n{priority} <b>{t.title}</b>\n"
                    f"   ⏰ {deadline}"
                )
                if t.description:
                    lines.append(f"   📄 {t.description[:150]}")
            if len(section_tasks) > 10:
                lines.append(f"\n   ... и ещё {len(section_tasks) - 10} задач")

    keyboard = [
        [
            InlineKeyboardButton("📋 Все", callback_data="task_filter:all"),
            InlineKeyboardButton("🔄 Активные", callback_data="task_filter:active"),
            InlineKeyboardButton("✅ Завершённые", callback_data="task_filter:completed"),
        ],
    ]
    for section_title, section_tasks in sections:
        for t in section_tasks[:10]:
            if t.status == Task.Status.PENDING:
                title_short = t.title[:25] + "…" if len(t.title) > 25 else t.title
                keyboard.append([
                    InlineKeyboardButton(f"▶️ {title_short}", callback_data=f"task_set:{t.id}:in_progress")
                ])
            elif t.status == Task.Status.IN_PROGRESS:
                title_short = t.title[:25] + "…" if len(t.title) > 25 else t.title
                keyboard.append([
                    InlineKeyboardButton(f"✅ {title_short}", callback_data=f"task_set:{t.id}:completed")
                ])

    keyboard.append([InlineKeyboardButton("🔙 В меню", callback_data="menu_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "\n".join(lines)
    if len(text) > 4000:
        plain = re.sub(r"<[^>]+>", "", text)[:3997] + "..."
        await query.edit_message_text(plain, reply_markup=reply_markup)
    else:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)


# ═══════════════════════════════════════════════════════════════════════
#  CLAIM LEAD (callback)
# ═══════════════════════════════════════════════════════════════════════

async def claim_lead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 'Взять в работу' button callback."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("claim:"):
        return

    lead_id = int(data.split(":")[1])
    chat_id = update.effective_chat.id

    try:
        lead = await _get_lead_by_id(lead_id)
    except TrialLead.DoesNotExist:
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(text=query.message.text + "\n\n❌ Лид не найден (возможно, удалён).")
        return

    existing = await _get_lead_assignment(lead)
    if existing and existing.manager:
        manager_name = (
            f"{existing.manager.first_name} {existing.manager.last_name}".strip()
            or existing.manager.username
        )
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(text=query.message.text + f"\n\n⚠️ Лид уже взят менеджером: {manager_name}")
        return

    try:
        manager = await _get_user_by_chat_id(chat_id)
    except User.DoesNotExist:
        await query.answer("❌ Вы не зарегистрированы. Используйте /start ваш_username", show_alert=True)
        return

    if existing:
        await _update_lead_assignment(existing, manager)
    else:
        await _create_lead_assignment(lead, manager)

    await _update_lead_status_contacted(lead)

    manager_name = f"{manager.first_name} {manager.last_name}".strip() or manager.username

    await query.edit_message_reply_markup(reply_markup=None)
    await query.edit_message_text(text=query.message.text + f"\n\n✅ Лид взят менеджером: {manager_name}")
    await query.answer(f"✅ Лид назначен на вас!", show_alert=True)
