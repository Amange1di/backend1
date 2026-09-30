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

from .common_menu import _send_welcome_message
from .common_state import _generate_code, _pending_verifications

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

