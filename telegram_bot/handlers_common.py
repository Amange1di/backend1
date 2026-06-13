"""
Common handlers — shared by all roles.

- /start command: universal registration with optional verification code
- /verify command: enter verification code to confirm re-binding
- menu_back: returns to the main role-based menu
"""

import random
import time

from .config import (
    Update,
    ContextTypes,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MessageHandler,
    filters,
    User,
    logger,
    FRONTEND_URL,
)
from .helpers import _get_user_by_username, _save_telegram_chat_id, _get_user_by_chat_id, _get_valid_bind_code, _mark_bind_code_used, _get_user_by_bind_code


# ═══════════════════════════════════════════════════════════════════════
#  VERIFICATION CODE STORE
# ═══════════════════════════════════════════════════════════════════════

# Pending verification codes for re-binding.
# Structure: {username: {"code": str, "expires_at": float, "new_chat_id": int}}
_pending_verifications: dict = {}


def _generate_code() -> str:
    """Generate a 6-digit verification code."""
    return f"{random.randint(0, 999999):06d}"


def _clean_expired_codes():
    """Remove expired verification codes (older than 5 minutes)."""
    now = time.time()
    expired = [k for k, v in _pending_verifications.items() if v["expires_at"] <= now]
    for k in expired:
        del _pending_verifications[k]


# ═══════════════════════════════════════════════════════════════════════
#  SHARED HELP TEXT (used by /help command and menu_help callback)
# ═══════════════════════════════════════════════════════════════════════

ROLE_HELPS = {
    User.Role.MANAGER: (
        "<b>📋 Меню менеджера</b>\n\n"
        "<b>🌐 Войти на сайт</b> — открыть CRM в браузере\n"
        "<b>📋 Мои задачи</b> — список активных задач\n"
        "<b>❓ Помощь</b> — описание кнопок меню\n\n"
        "<b>🔔 Уведомления:</b>\n"
        "• Новые лиды — нажмите «Взять в работу»\n"
        "• Новые задачи — нажмите «▶️ Взять в работу»"
    ),
    User.Role.TEACHER: (
        "<b>👨‍🏫 Меню учителя</b>\n\n"
        "<b>🌐 Войти на сайт</b> — открыть CRM в браузере\n"
        "<b>📅 Расписание</b> — расписание на сегодня и неделю\n"
        "<b>📚 Студенты</b> — список студентов по группам\n"
        "<b>❓ Помощь</b> — описание кнопок меню\n\n"
        "<b>🔔 Уведомления:</b>\n"
        "• Назначение на группу — принять / отказаться\n"
        "• Напоминание об уроке за 30 минут\n"
        "• Сдача домашнего задания студентом"
    ),
    User.Role.COURSE_ADMIN: (
        "<b>🏢 Меню Course Admin</b>\n\n"
        "<b>🌐 Войти на сайт</b> — открыть CRM в браузере\n"
        "<b>📊 Статистика задач</b> — статистика задач компании\n"
        "<b>❓ Помощь</b> — описание кнопок меню\n\n"
        "<b>🔔 Уведомления:</b>\n"
        "• Учитель подтвердил / отказался от группы\n"
        "• Изменение статуса задачи менеджером\n"
        "• Ежедневная сводка по лидам"
    ),
    User.Role.STUDENT: (
        "<b>🎓 Меню студента</b>\n\n"
        "<b>🌐 Войти на сайт</b> — открыть CRM в браузере\n"
        "<b>❓ Помощь</b> — описание кнопок меню\n\n"
        "<b>🔔 Уведомления:</b>\n"
        "• Напоминание об уроке за 30 минут\n"
        "• Новое домашнее задание\n"
        "• Результат проверки ДЗ"
    ),
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register a user's Telegram chat ID.

    Usage: /start <username>
    Where <username> is the user's username in the CRM.
    Works for any role: manager, teacher, student, course_admin.
    """
    if not context.args:
        await update.message.reply_text(
            "❌ Использование: /start ваш_username [код]\n\n"
            "Например: /start teacher_aziz\n"
            "Или если у вас есть код из CRM: /start teacher_aziz 123456\n"
            "Username — это логин, под которым вы заходите в CRM."
        )
        return

    raw_arg = context.args[0].strip()
    username = raw_arg
    provided_code = None
    chat_id = update.effective_chat.id

    # First, try to find user by the full raw_arg (before attempting deep-link splitting)
    # This prevents false positives when a username happens to end with _XXXXXX
    try:
        user = await _get_user_by_username(raw_arg)
    except User.DoesNotExist:
        user = None

    if user is None and len(context.args) == 1:
        # User not found — maybe this is a deep link ?start=username_123456
        # Try splitting on the last underscore to extract username + 6-digit code
        last_underscore = raw_arg.rfind("_")
        if last_underscore != -1:
            potential_code = raw_arg[last_underscore + 1:]
            if len(potential_code) == 6 and potential_code.isdigit():
                username = raw_arg[:last_underscore]
                provided_code = potential_code
                try:
                    user = await _get_user_by_username(username)
                except User.DoesNotExist:
                    pass  # will be caught below
    elif len(context.args) > 1:
        provided_code = context.args[1].strip() if len(context.args) > 1 else None

    if user is None:
        await update.message.reply_text(
            f"❌ Пользователь с username «{username}» не найден.\n"
            "Проверьте username в CRM."
        )
        return

    # If user already has a telegram_chat_id and it's different from current chat,
    # require a verification code before switching the binding.
    if user.telegram_chat_id and user.telegram_chat_id != chat_id:
        code = _generate_code()
        _pending_verifications[username] = {
            "code": code,
            "expires_at": time.time() + 300,  # 5 minutes
            "new_chat_id": chat_id,
        }

        # Send verification code to the OLD Telegram chat
        try:
            await context.bot.send_message(
                chat_id=user.telegram_chat_id,
                text=(
                    f"⚠️ <b>Запрос на смену привязки Telegram</b>\n\n"
                    f"Кто-то пытается привязать ваш аккаунт <b>{username}</b> "
                    f"к другому Telegram.\n\n"
                    f"Если это вы, подтвердите кодом:\n"
                    f"<code>{code}</code>\n\n"
                    f"<b>Код действителен 5 минут.</b>\n"
                    f"Если это не вы — просто проигнорируйте сообщение."
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning(f"Failed to send verification code to old chat: {e}")

        await update.message.reply_text(
            f"📱 <b>Код подтверждения отправлен!</b>\n\n"
            f"На ваш старый Telegram чат отправлен код подтверждения.\n"
            f"Проверьте старый чат и отправьте полученный код сюда.\n\n"
            f"<b>Код действителен 5 минут.</b>",
            parse_mode="HTML",
        )
        return

    # NEW: First-time binding — require a code generated from the CRM website
    if not user.telegram_chat_id:
        # If user already has a telegram_chat_id matching this chat, they're already bound
        # This branch handles the no-telegram_chat_id case
        if provided_code:
            # Validate the provided code from DB
            is_valid = await _get_valid_bind_code(user, provided_code)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ Неверный или просроченный код.\n\n"
                    f"Сгенерируйте новый код в своём профиле на сайте "
                    f"и попробуйте снова: /start {username} новый_код",
                    parse_mode="HTML",
                )
                return

            # Code is valid — bind and mark code as used
            await _mark_bind_code_used(user, provided_code)
            await _save_telegram_chat_id(user, chat_id)
            await _send_welcome_message(update, user)
            return
        else:
            # No code provided — tell user to get one from the website
            await update.message.reply_text(
                f"🔐 <b>Требуется код подтверждения</b>\n\n"
                f"Для привязки Telegram к аккаунту <b>{username}</b> "
                f"необходимо сгенерировать одноразовый код в CRM.\n\n"
                f"<b>Инструкция:</b>\n"
                f"1️⃣ Зайдите на сайт CRM под своим логином\n"
                f"2️⃣ В профиле нажмите «Сгенерировать код»\n"
                f"3️⃣ Отправьте код сюда:\n"
                f"   <code>/start {username} ваш_код</code>\n\n"
                f"<b>Код действителен 10 минут.</b>",
                parse_mode="HTML",
            )
            return

    # If user already has a telegram_chat_id matching this chat, they're already bound
    # This falls through only if user.telegram_chat_id == chat_id
    await _send_welcome_message(update, user)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available commands based on the user's role.

    Usage: /help
    """
    chat_id = update.effective_chat.id
    user = await _get_user_by_chat_id(chat_id)

    if not user:
        text = (
            "<b>🤖 Telegram Bot — EduOsh CRM</b>\n\n"
            "Для начала работы зарегистрируйтесь:\n"
            "<code>/start ваш_username</code>\n\n"
            "Username — это логин, под которым вы заходите в CRM.\n"
            "После регистрации вы будете получать уведомления "
            "в зависимости от вашей роли."
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    text = ROLE_HELPS.get(
        user.role,
        "<b>🤖 Telegram Bot — EduOsh CRM</b>\n\n"
        "Ваша роль не имеет специальных команд. "
        "Вы будете получать уведомления по мере необходимости."
    )

    await update.message.reply_text(text, parse_mode="HTML")


async def menu_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle '❓ Помощь' button — shows role-specific help."""
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    user = await _get_user_by_chat_id(chat_id)

    if not user:
        await query.edit_message_text(
            "❌ Вы не зарегистрированы. Используйте /start ваш_username",
        )
        return

    text = ROLE_HELPS.get(
        user.role,
        "<b>🤖 Telegram Bot — EduOsh CRM</b>\n\n"
        "Ваша роль не имеет специальных команд."
    )

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 В меню", callback_data="menu_back")
    ]])

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)


async def menu_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'В меню' button — returns to welcome menu."""
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    user = await _get_user_by_chat_id(chat_id)
    if not user:
        await query.edit_message_text("❌ Пользователь не найден.")
        return

    role_messages = {
        User.Role.MANAGER: "✅ Вы в главном меню.\nНажимайте «Взять в работу» на уведомлениях о лидах.",
        User.Role.TEACHER: "✅ Вы в главном меню. Выберите действие:",
        User.Role.STUDENT: "✅ Вы в главном меню.\nВы будете получать напоминания об уроках и ДЗ.",
        User.Role.COURSE_ADMIN: "✅ Вы в главном меню.\nВы будете получать сводку по лидам и статистику.",
    }

    msg = role_messages.get(user.role, "✅ Вы в главном меню.")

    login_button = [InlineKeyboardButton("🌐 Войти на сайт", url=FRONTEND_URL)]

    role_keyboards = {
        User.Role.TEACHER: [
            login_button,
            [InlineKeyboardButton("📅 Расписание", callback_data="menu_schedule")],
            [InlineKeyboardButton("📚 Студенты", callback_data="menu_students")],
            [InlineKeyboardButton("❓ Помощь", callback_data="menu_help")],
        ],
        User.Role.MANAGER: [
            login_button,
            [InlineKeyboardButton("📋 Мои задачи", callback_data="menu_tasks")],
            [InlineKeyboardButton("❓ Помощь", callback_data="menu_help")],
        ],
        User.Role.COURSE_ADMIN: [
            login_button,
            [InlineKeyboardButton("📊 Статистика задач", callback_data="menu_tasks_stats")],
            [InlineKeyboardButton("❓ Помощь", callback_data="menu_help")],
        ],
        User.Role.STUDENT: [
            login_button,
            [InlineKeyboardButton("❓ Помощь", callback_data="menu_help")],
        ],
    }

    keyboard = role_keyboards.get(user.role)
    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        reply_markup = InlineKeyboardMarkup([login_button]) if user.role else None

    await query.edit_message_text(msg, parse_mode="HTML", reply_markup=reply_markup)


# ═══════════════════════════════════════════════════════════════════════
#  SHARED WELCOME / HELPERS
# ═══════════════════════════════════════════════════════════════════════


async def _send_welcome_message(update: Update, user: User):
    """Send a role-specific welcome message with inline keyboard.

    Used by /start (first-time registration) and _process_verification (re-binding).
    """
    role_messages = {
        User.Role.MANAGER: (
            "✅ Привет, {name}! Теперь вы будете получать уведомления о новых лидах.\n"
            "Нажимайте «Взять в работу», чтобы назначить лида на себя."
        ),
        User.Role.TEACHER: (
            "✅ Привет, {name}! Теперь вы будете получать:\n"
            "• Уведомления о новых группах — нужно подтвердить\n"
            "• Напоминания об уроках за 30 минут\n"
            "• Уведомления о сданных домашних заданиях"
        ),
        User.Role.STUDENT: (
            "✅ Привет, {name}! Теперь вы будете получать:\n"
            "• Напоминания об уроках за 30 минут\n"
            "• Уведомления о новых домашних заданиях\n"
            "• Результаты проверки ДЗ"
        ),
        User.Role.COURSE_ADMIN: (
            "✅ Привет, {name}! Теперь вы будете получать:\n"
            "• Сводку по новым лидам\n"
            "• Статистику по компании"
        ),
    }

    name = f"{user.first_name} {user.last_name}".strip() or user.username
    msg = role_messages.get(user.role, "✅ Привет, {name}! Регистрация прошла успешно.")

    # Common "Войти на сайт" button for all roles
    login_button = [InlineKeyboardButton("🌐 Войти на сайт", url=FRONTEND_URL)]

    # Role-specific inline menu buttons
    role_keyboards = {
        User.Role.TEACHER: [
            login_button,
            [InlineKeyboardButton("📅 Расписание", callback_data="menu_schedule")],
            [InlineKeyboardButton("📚 Студенты", callback_data="menu_students")],
            [InlineKeyboardButton("❓ Помощь", callback_data="menu_help")],
        ],
        User.Role.MANAGER: [
            login_button,
            [InlineKeyboardButton("📋 Мои задачи", callback_data="menu_tasks")],
            [InlineKeyboardButton("❓ Помощь", callback_data="menu_help")],
        ],
        User.Role.COURSE_ADMIN: [
            login_button,
            [InlineKeyboardButton("📊 Статистика задач", callback_data="menu_tasks_stats")],
            [InlineKeyboardButton("❓ Помощь", callback_data="menu_help")],
        ],
        User.Role.STUDENT: [
            login_button,
            [InlineKeyboardButton("❓ Помощь", callback_data="menu_help")],
        ],
    }

    keyboard = role_keyboards.get(user.role)
    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        reply_markup = InlineKeyboardMarkup([login_button]) if user.role else None

    await update.message.reply_text(
        msg.format(name=name),
        parse_mode="HTML",
        reply_markup=reply_markup,
    )


# ═══════════════════════════════════════════════════════════════════════
#  VERIFICATION CODE HANDLERS
# ═══════════════════════════════════════════════════════════════════════


async def verify_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /verify <code> command — enter verification code."""
    if not context.args:
        await update.message.reply_text(
            "❌ Использование: /verify <код>\n"
            "Код должен прийти вам в старый Telegram чат после /start."
        )
        return

    code = context.args[0].strip()
    await _process_verification(update, context, code)


async def handle_code_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain text 6-digit code entry (non-command message).

    Silently ignores the message if no pending verification exists for this chat,
    to avoid replying to random 6-digit numbers the user might type.
    """
    text = update.message.text.strip()
    if len(text) == 6 and text.isdigit():
        _clean_expired_codes()
        chat_id = update.effective_chat.id
        # Only process if there's actually a pending verification for this chat
        has_pending = any(
            data["new_chat_id"] == chat_id
            for data in _pending_verifications.values()
        )
        if has_pending:
            await _process_verification(update, context, text)


async def _process_verification(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    """Process a verification code — bind the user if the code is correct."""
    chat_id = update.effective_chat.id

    # First, check if this is a first-time binding code from the CRM website
    user = await _get_user_by_bind_code(code)
    if user:
        await _mark_bind_code_used(user, code)
        await _save_telegram_chat_id(user, chat_id)
        await _send_welcome_message(update, user)
        return

    # Look for a matching pending verification (re-binding flow)
    for username, data in list(_pending_verifications.items()):
        if data["new_chat_id"] != chat_id:
            continue

        if data["code"] != code:
            await update.message.reply_text("❌ Неверный код. Попробуйте ещё раз.")
            return

        # Code matches — bind the user to this chat
        try:
            user = await _get_user_by_username(username)
        except User.DoesNotExist:
            await update.message.reply_text("❌ Ошибка: пользователь не найден.")
            del _pending_verifications[username]
            return

        # Save old chat_id before overwriting it, so we can notify it
        old_chat_id = user.telegram_chat_id

        await _save_telegram_chat_id(user, chat_id)
        del _pending_verifications[username]

        # Notify the old chat that the binding has been transferred
        if old_chat_id and old_chat_id != chat_id:
            try:
                await context.bot.send_message(
                    chat_id=old_chat_id,
                    text=(
                        f"✅ <b>Привязка аккаунта изменена</b>\n\n"
                        f"Ваш аккаунт <b>{username}</b> был привязан к новому Telegram устройству.\n"
                        f"Уведомления больше не будут приходить сюда."
                    ),
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.warning(f"Failed to notify old chat about transfer: {e}")

        # Send role-specific welcome to the new chat
        await _send_welcome_message(update, user)
        return

    # No pending verification found for this chat
    existing_user = await _get_user_by_chat_id(chat_id)
    if existing_user:
        await update.message.reply_text(
            f"✅ Ваш аккаунт уже привязан. Используйте /help для списка команд."
        )
        return

    await update.message.reply_text(
        "❌ Нет ожидающего запроса на привязку.\n"
        "Сначала используйте /start ваш_username"
    )


def get_message_handler():
    """Return the MessageHandler for 6-digit code entry.
    Used by bot.py to register the handler."""
    return MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code_message)
