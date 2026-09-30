"""
Teacher handlers.

Commands:
  /schedule  — today's / week schedule
  /students  — list groups, show students per group

Callbacks:
  menu_schedule          — schedule from menu button
  menu_students          — students from menu button
  confirm_group:         — accept group assignment
  reject_group:          — decline group assignment
  st_group:<id>          — show students for a group
  st_back                — back to group list
"""

import bleach
from core.models import User, Group, Student

from ..config import (
    Update,
    ContextTypes,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    sync_to_async,
    timedelta,
    logger,
    _get_application,
)
from ..helpers import (
    _get_user_by_chat_id,
    _get_group_by_id,
    _get_teacher_groups,
    _get_all_students_for_group,
    _get_week_groups_for_teacher,
    _get_group_course_name,
    _get_group_company_name,
    _get_course_admins_for_company,
    _update_group_status,
)
from ..config import _get_application
from asgiref.sync import sync_to_async


# ═══════════════════════════════════════════════════════════════════════
#  SCHEDULE
# ═══════════════════════════════════════════════════════════════════════

async def students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the teacher's groups with inline buttons.

    Usage: /students
    Shows a list of groups. Click a group to see its students.
    """
    chat_id = update.effective_chat.id
    user = await _get_user_by_chat_id(chat_id)

    if not user:
        await update.message.reply_text("❌ Вы не зарегистрированы. Используйте /start ваш_username")
        return

    if user.role != User.Role.TEACHER:
        await update.message.reply_text("❌ Команда /students доступна только для учителей.")
        return

    groups = await _get_teacher_groups(user)
    if not groups:
        await update.message.reply_text("📚 У вас нет активных групп.")
        return

    lines = [f"📚 <b>Ваши группы</b> ({len(groups)}):"]
    keyboard = []
    row = []
    for g in groups:
        course_name = await _get_group_course_name(g)
        student_count = await sync_to_async(lambda g=g: g.students.count())()
        lines.append(f"\n<b>{g.name}</b> — 👥 {student_count} — 📖 {course_name}")
        btn = InlineKeyboardButton(f"{g.name}", callback_data=f"st_group:{g.id}")
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=reply_markup,
    )

async def menu_students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle menu 'Студенты' button — calls students logic."""
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    user = await _get_user_by_chat_id(chat_id)
    if not user or user.role != User.Role.TEACHER:
        await query.answer("❌ Доступно только для учителей.", show_alert=True)
        return

    groups = await _get_teacher_groups(user)
    if not groups:
        await query.edit_message_text("📚 У вас нет активных групп.")
        return

    lines = [f"📚 <b>Ваши группы</b> ({len(groups)}):"]
    keyboard = []
    row = []
    for g in groups:
        course_name = await _get_group_course_name(g)
        student_count = await sync_to_async(lambda g=g: g.students.count())()
        lines.append(f"\n<b>{g.name}</b> — 👥 {student_count} — 📖 {course_name}")
        btn = InlineKeyboardButton(f"{g.name}", callback_data=f"st_group:{g.id}")
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔙 В меню", callback_data="menu_back")])

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ═══════════════════════════════════════════════════════════════════════
#  SHOW GROUP STUDENTS (callback)
# ═══════════════════════════════════════════════════════════════════════

async def show_group_students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback when teacher clicks a group button."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("st_group:"):
        return

    group_id = int(data.split(":")[1])
    chat_id = update.effective_chat.id

    user = await _get_user_by_chat_id(chat_id)
    if not user or user.role != User.Role.TEACHER:
        await query.answer("❌ Доступно только для учителей.", show_alert=True)
        return

    try:
        group = await _get_group_by_id(group_id)
    except Group.DoesNotExist:
        await query.edit_message_text("❌ Группа не найдена.")
        return

    if group.teacher_id != user.id:
        await query.answer("❌ Эта группа не ваша.", show_alert=True)
        return

    students_list = await _get_all_students_for_group(group.id)
    course_name = await _get_group_course_name(group)

    if not students_list:
        header = f"📚 <b>{group.name}</b> ({course_name})\n👥 В группе пока нет студентов."
    else:
        student_lines = []
        for i, s in enumerate(students_list, 1):
            name = f"{s.first_name} {s.last_name}".strip() or "—"
            phone = s.phone or "—"
            tg = f" (@{s.telegram.replace('@', '')})" if s.telegram else ""
            student_lines.append(f"{i}. {name} — 📞 {phone}{tg}")

        header = f"📚 <b>{group.name}</b> ({course_name})\n👥 {len(students_list)} студентов:\n\n" + "\n".join(student_lines)

        # Split long messages
        if len(header) > 4000:
            header = f"📚 <b>{group.name}</b> ({course_name})\n👥 {len(students_list)} студентов:"
            await query.edit_message_text(header, parse_mode="HTML")
            chunk = []
            chunk_len = 0
            for line in student_lines:
                if chunk_len + len(line) + 1 > 4000:
                    await context.bot.send_message(chat_id, "\n".join(chunk))
                    chunk = [line]
                    chunk_len = len(line)
                else:
                    chunk.append(line)
                    chunk_len += len(line) + 1
            if chunk:
                await context.bot.send_message(chat_id, "\n".join(chunk))
            back_keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад к группам", callback_data="st_back")
            ]])
            await context.bot.send_message(
                chat_id,
                "💡 Нажмите «Назад», чтобы вернуться к списку групп",
                reply_markup=back_keyboard,
            )
            return

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Назад к группам", callback_data="st_back")
    ]])

    await query.edit_message_text(
        text=header,
        parse_mode="HTML",
        reply_markup=keyboard,
    )

async def handle_students_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 'Назад к группам' button callback."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="🔙 Вы вернулись в главное меню.")

