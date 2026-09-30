"""
Common handlers — shared by all roles.

- /start command: universal registration with optional verification code
- /verify command: enter verification code to confirm re-binding
- menu_back: returns to the main role-based menu
"""

import random
import time

from core.models import User

from ..config import (
    Update,
    ContextTypes,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MessageHandler,
    filters,
    logger,
    FRONTEND_URL,
)
from ..helpers import _get_user_by_username, _save_telegram_chat_id, _get_user_by_chat_id, _get_valid_bind_code, _mark_bind_code_used, _get_user_by_bind_code

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

