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

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the teacher's schedule for today and the current week.

    Usage: /schedule
    """
    chat_id = update.effective_chat.id
    user = await _get_user_by_chat_id(chat_id)

    if not user:
        await update.message.reply_text("❌ Вы не зарегистрированы. Используйте /start ваш_username")
        return

    if user.role != User.Role.TEACHER:
        await update.message.reply_text("❌ Команда /schedule доступна только для учителей.")
        return

    groups_by_day, weekday_names_ru, today, monday = await _get_week_groups_for_teacher(user)
    today_idx = today.weekday()

    # ── TODAY ──
    today_groups = groups_by_day.get(today_idx, [])
    today_lines = []
    if today_groups:
        for g in today_groups:
            course_name = await _get_group_course_name(g)
            auditorium = g.auditorium.name if g.auditorium else "—"
            today_lines.append(
                f"🕐 {g.schedule_time}  📚 {g.name}  ({course_name})\n"
                f"   📍 {auditorium}"
            )

    today_text = (
        f"📅 <b>Расписание на сегодня</b> ({today.strftime('%d.%m.%Y')})\n\n"
        + ("\n\n".join(today_lines) if today_lines else "   🎉 Сегодня уроков нет")
    )

    # ── THIS WEEK ──
    week_lines = []
    for day_idx in range(7):
        day_date = monday + timedelta(days=day_idx)
        day_groups = groups_by_day.get(day_idx, [])
        if not day_groups:
            continue
        day_header_emoji = "📌" if day_idx == today_idx else "▫️"
        day_label = weekday_names_ru[day_idx]
        date_str = day_date.strftime("%d.%m")
        today_tag = " <b>← сегодня</b>" if day_idx == today_idx else ""

        day_block = f"{day_header_emoji} <b>{day_label}</b> ({date_str}){today_tag}"
        for g in day_groups:
            course_name = await _get_group_course_name(g)
            auditorium = g.auditorium.name if g.auditorium else "—"
            day_block += f"\n   🕐 {g.schedule_time}  📚 {g.name}  ({course_name})  📍 {auditorium}"
        week_lines.append(day_block)

    week_text = (
        f"📋 <b>Расписание на неделю</b>\n\n"
        + ("\n\n".join(week_lines) if week_lines else "   🎉 На этой неделе уроков нет")
    )

    await update.message.reply_text(
        f"{today_text}\n\n━━━━━━━━━━━━━━\n\n{week_text}",
        parse_mode="HTML",
    )

async def menu_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle menu 'Расписание' button — calls schedule logic."""
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    user = await _get_user_by_chat_id(chat_id)
    if not user or user.role != User.Role.TEACHER:
        await query.answer("❌ Доступно только для учителей.", show_alert=True)
        return

    groups_by_day, weekday_names_ru, today, monday = await _get_week_groups_for_teacher(user)
    today_idx = today.weekday()

    today_groups = groups_by_day.get(today_idx, [])
    today_lines = []
    if today_groups:
        for g in today_groups:
            course_name = await _get_group_course_name(g)
            auditorium = g.auditorium.name if g.auditorium else "—"
            today_lines.append(
                f"🕐 {g.schedule_time}  📚 {g.name}  ({course_name})\n"
                f"   📍 {auditorium}"
            )

    today_text = (
        f"📅 <b>Расписание на сегодня</b> ({today.strftime('%d.%m.%Y')})\n\n"
        + ("\n\n".join(today_lines) if today_lines else "   🎉 Сегодня уроков нет")
    )

    week_lines = []
    for day_idx in range(7):
        day_date = monday + timedelta(days=day_idx)
        day_groups = groups_by_day.get(day_idx, [])
        if not day_groups:
            continue
        day_header_emoji = "📌" if day_idx == today_idx else "▫️"
        day_label = weekday_names_ru[day_idx]
        date_str = day_date.strftime("%d.%m")
        today_tag = " <b>← сегодня</b>" if day_idx == today_idx else ""
        day_block = f"{day_header_emoji} <b>{day_label}</b> ({date_str}){today_tag}"
        for g in day_groups:
            course_name = await _get_group_course_name(g)
            auditorium = g.auditorium.name if g.auditorium else "—"
            day_block += f"\n   🕐 {g.schedule_time}  📚 {g.name}  ({course_name})  📍 {auditorium}"
        week_lines.append(day_block)

    week_text = (
        f"📋 <b>Расписание на неделю</b>\n\n"
        + ("\n\n".join(week_lines) if week_lines else "   🎉 На этой неделе уроков нет")
    )

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 В меню", callback_data="menu_back")
    ]])

    await query.edit_message_text(
        f"{today_text}\n\n━━━━━━━━━━━━━━\n\n{week_text}",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ═══════════════════════════════════════════════════════════════════════
#  STUDENTS
# ═══════════════════════════════════════════════════════════════════════

