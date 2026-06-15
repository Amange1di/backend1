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

from .config import (
    Update,
    ContextTypes,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    sync_to_async,
    timedelta,
    User,
    Group,
    Student,
    logger,
    _get_application,
)
from .helpers import (
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
from .config import _get_application
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


async def handle_rejection_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle teacher's rejection comment."""
    chat_id = update.effective_chat.id
    
    # Проверяем, ждём ли мы комментарий
    if not context.user_data.get('waiting_for_rejection_comment'):
        return
    
    text = update.message.text.strip()
    group_id = context.user_data.get('rejecting_group_id')
    
    if not group_id:
        await update.message.reply_text("❌ Ошибка: группа не найдена.")
        context.user_data['waiting_for_rejection_comment'] = False
        return
    
    try:
        group = await _get_group_by_id(group_id)
    except Group.DoesNotExist:
        await update.message.reply_text("❌ Группа не найдена.")
        context.user_data['waiting_for_rejection_comment'] = False
        return
    
    # Сохраняем комментарий
    comment = text if text.lower() not in ['без причины', 'без причины.', 'нет', ''] else '—'
    group.rejection_comment = comment
    group.rejection_count = group.rejection_count + 1
    group.status = Group.Status.REJECTED
    await sync_to_async(group.save)()
    
    course_name = await _get_group_course_name(group)
    teacher = await _get_user_by_chat_id(chat_id)
    teacher_name = f"{teacher.first_name} {teacher.last_name}".strip() or teacher.username
    company_name = await _get_group_company_name(group)
    
    # Удаление ожидания
    context.user_data['waiting_for_rejection_comment'] = False
    context.user_data.pop('rejecting_group_id', None)
    
    # Отправляем подтверждение учителю
    await update.message.reply_text(
        f"❌ Ваш отказ зафиксирован.\n"
        f"Группа «{group.name}» отклонена.\n"
        f"Комментарий: {comment}"
    )
    
    # Уведомляем курс-админов
    if company_name:
        admins = await _get_course_admins_for_company(company_name)
        application = _get_application()
        if admins:
            for admin in admins:
                try:
                    admin_keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            "🔁 Повторить отправку",
                            callback_data=f"resubmit_group:{group.id}"
                        )
                    ]])
                    
                    # Формируем текст с учётом количества отказов
                    if group.rejection_count > 1:
                        rejection_text = f"⚠️ <b>Это {group.rejection_count}-й отказ учителя!</b>"
                    else:
                        rejection_text = "❌ <b>Учитель отказался от группы!</b>"
                    
                    await application.bot.send_message(
                        chat_id=admin.telegram_chat_id,
                        text=(
                            f"{rejection_text}\n\n"
                            f"👨‍🏫 Учитель: {teacher_name}\n"
                            f"📚 Группа: {group.name}\n"
                            f"📖 Курс: {course_name}\n"
                            f"💬 <b>Комментарий:</b> {comment}\n\n"
                            f"Нажмите кнопку ниже, чтобы повторить отправку запроса."
                        ),
                        parse_mode="HTML",
                        reply_markup=admin_keyboard
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin.username}: {e}")
        else:
            logger.warning(f"No course admins found for company {company_name}")
    else:
        logger.warning(f"Group {group.id} has no company, cannot notify admins")


# ═══════════════════════════════════════════════════════════════════════
#  GROUP CONFIRMATION / REJECTION
# ═══════════════════════════════════════════════════════════════════════

async def confirm_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle teacher confirming a group assignment."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("confirm_group:"):
        return

    group_id = int(data.split(":")[1])
    chat_id = update.effective_chat.id

    try:
        group = await _get_group_by_id(group_id)
    except Group.DoesNotExist:
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(text=query.message.text + "\n\n❌ Группа не найдена.")
        return

    try:
        teacher = await _get_user_by_chat_id(chat_id)
    except User.DoesNotExist:
        await query.answer("❌ Вы не зарегистрированы. Используйте /start ваш_username", show_alert=True)
        return

    if group.teacher_id != teacher.id:
        await query.answer("❌ Эта группа назначена не вам.", show_alert=True)
        return

    if group.status != Group.Status.PENDING:
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(
            text=query.message.text + f"\n\n⚠️ Статус группы уже изменён (текущий: {group.status})."
        )
        return

    # Показываем подтверждение
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Да, подтвердить", callback_data=f"confirm_group_yes:{group_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_action:{group_id}")
        ],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_back")]
    ])
    
    course_name = await _get_group_course_name(group)
    await query.edit_message_reply_markup(reply_markup=None)
    await query.edit_message_text(
        text=query.message.text + f"\n\n⚠️ <b>Подтвердите действие:</b>\n\n"
        f"Вы принимаете группу «{group.name}» ({course_name}).\n"
        f"Это изменит статус группы на <b>Активна</b>.",
        parse_mode="HTML",
        reply_markup=keyboard
    )



async def reject_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle teacher rejecting a group assignment."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("reject_group:"):
        return

    group_id = int(data.split(":")[1])
    chat_id = update.effective_chat.id

    try:
        group = await _get_group_by_id(group_id)
    except Group.DoesNotExist:
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(text=query.message.text + "\n\n❌ Группа не найдена.")
        return

    try:
        teacher = await _get_user_by_chat_id(chat_id)
    except User.DoesNotExist:
        await query.answer("❌ Вы не зарегистрированы. Используйте /start ваш_username", show_alert=True)
        return

    if group.teacher_id != teacher.id:
        await query.answer("❌ Эта группа назначена не вам.", show_alert=True)
        return

    if group.status != Group.Status.PENDING:
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(text=query.message.text + "\n\n⚠️ Статус группы уже изменён.")
        return

    # Показываем подтверждение
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Да, отказаться", callback_data=f"reject_group_yes:{group_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_action:{group_id}")
        ],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_back")]
    ])
    
    course_name = await _get_group_course_name(group)
    await query.edit_message_reply_markup(reply_markup=None)
    await query.edit_message_text(
        text=query.message.text + f"\n\n⚠️ <b>Подтвердите действие:</b>\n\n"
        f"Вы отказываетесь от группы «{group.name}» ({course_name}).\n"
        f"Это изменит статус группы на <b>Отклонена</b>.\n"
        f"После этого курс-админ сможет повторить отправку запроса.",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def confirm_group_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle teacher confirming group acceptance."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("confirm_group_yes:"):
        return

    group_id = int(data.split(":")[1])
    chat_id = update.effective_chat.id

    try:
        group = await _get_group_by_id(group_id)
    except Group.DoesNotExist:
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(text="❌ Группа не найдена.")
        return

    try:
        teacher = await _get_user_by_chat_id(chat_id)
    except User.DoesNotExist:
        await query.answer("❌ Вы не зарегистрированы.", show_alert=True)
        return

    if group.teacher_id != teacher.id:
        await query.answer("❌ Эта группа не вам.", show_alert=True)
        return

    if group.status != Group.Status.PENDING:
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(text=f"⚠️ Статус группы уже изменён ({group.status}).")
        return

    # Подтверждаем
    await _update_group_status(group_id, Group.Status.ACTIVE)

    course_name = await _get_group_course_name(group)
    company_name = await _get_group_company_name(group)

    # Build keyboard for course admins
    keyboard = []
    if company_name:
        keyboard.append([
            InlineKeyboardButton(
                "🔁 Повторить отправку",
                callback_data=f"resubmit_group:{group.id}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton("🔙 Назад в меню", callback_data="menu_back")
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_reply_markup(reply_markup=reply_markup)
    await query.edit_message_text(
        text=query.message.text + f"\n\n✅ Вы приняли группу «{group.name}» ({course_name})!",
        reply_markup=reply_markup
    )
    await query.answer("✅ Группа подтверждена!", show_alert=True)

    # Notify course admins
    if company_name:
        teacher_name = f"{teacher.first_name} {teacher.last_name}".strip() or teacher.username
        admins = await _get_course_admins_for_company(company_name)
        application = _get_application()
        for admin in admins:
            try:
                admin_keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        "🔁 Повторить отправку",
                        callback_data=f"resubmit_group:{group.id}"
                    )
                ]])
                await application.bot.send_message(
                    chat_id=admin.telegram_chat_id,
                    text=(
                        f"✅ <b>Учитель подтвердил группу!</b>\n\n"
                        f"👨‍🏫 Учитель: {teacher_name}\n"
                        f"📚 Группа: {group.name}\n"
                        f"📖 Курс: {course_name}\n\n"
                        f"Нажмите кнопку ниже, если нужно повторить отправку."
                    ),
                    parse_mode="HTML",
                    reply_markup=admin_keyboard
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin.username}: {e}")


async def reject_group_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle teacher confirming group rejection - then asks for comment."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("reject_group_yes:"):
        return

    group_id = int(data.split(":")[1])
    chat_id = update.effective_chat.id

    try:
        group = await _get_group_by_id(group_id)
    except Group.DoesNotExist:
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(text="❌ Группа не найдена.")
        return

    try:
        teacher = await _get_user_by_chat_id(chat_id)
    except User.DoesNotExist:
        await query.answer("❌ Вы не зарегистрированы.", show_alert=True)
        return

    if group.teacher_id != teacher.id:
        await query.answer("❌ Эта группа не вам.", show_alert=True)
        return

    if group.status != Group.Status.PENDING:
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(text=f"⚠️ Статус группы уже изменён ({group.status}).")
        return

    # Запрашиваем комментарий
    context.user_data['rejecting_group_id'] = group_id
    context.user_data['rejecting_chat_id'] = chat_id
    context.user_data['waiting_for_rejection_comment'] = True
    
    await query.edit_message_reply_markup(reply_markup=None)
    await query.edit_message_text(
        text=query.message.text + f"\n\n❌ Вы подтвердили отказ от группы «{group.name}».\n"
        f"Теперь напишите причину (комментарий):",
        parse_mode="HTML"
    )
    
    await context.bot.send_message(
        chat_id=chat_id,
        text="✏️ Напишите комментарий или «без причины»:"
    )


async def cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle teacher cancelling an action."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_reply_markup(reply_markup=None)
    await query.edit_message_text(
        text=query.message.text + "\n\n✅ Действие отменено."
    )
    await query.answer("Отменено.")
