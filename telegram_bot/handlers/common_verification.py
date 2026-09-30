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
from .common_state import _clean_expired_codes, _pending_verifications

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

