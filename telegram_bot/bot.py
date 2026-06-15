"""
Telegram Bot for EduOsh CRM — entry point.

Imports all handler modules (which triggers Django setup via config.py)
and registers command / callback handlers before starting polling.
"""

import logging
import sys
import traceback

from .config import (
    Update,
    CommandHandler,
    CallbackQueryHandler,
    BOT_TOKEN,
    _get_application,
)

# Import all handler modules to trigger registration
from .handlers_common import (
    start,
    help_command,
    menu_back,
    menu_help,
    verify_code,
    get_message_handler,
)
from .handlers_teacher import (
    schedule,
    menu_schedule,
    students,
    menu_students,
    confirm_group,
    reject_group,
    show_group_students,
    handle_students_back,
    handle_rejection_comment,
    confirm_group_yes,
    reject_group_yes,
    cancel_action,
)
from .handlers_manager import (
    tasks,
    menu_tasks,
    task_set_status,
    task_filter,
    claim_lead,
)
from .handlers_admin import (
    tasks_stats,
    menu_tasks_stats,
    resubmit_group,
    resubmit_group_callback,
)

logger = logging.getLogger(__name__)


def _log(msg: str, level: str = "info"):
    """Log with immediate flush so Render logs see it in real-time."""
    getattr(logger, level)(msg)
    sys.stdout.flush()
    sys.stderr.flush()


def run_bot():
    """Run the Telegram bot in polling mode."""
    _log("=" * 60)
    _log("BOT: Starting Telegram bot...")
    _log(f"BOT: BOT_TOKEN length = {len(BOT_TOKEN) if BOT_TOKEN else 0}")
    
    if not BOT_TOKEN:
        _log("BOT: TELEGRAM_BOT_TOKEN is not configured!", "error")
        return

    try:
        application = _get_application()
        _log("BOT: Application instance created successfully")
    except Exception as e:
        _log(f"BOT: FAILED to create Application: {e}", "error")
        _log(f"BOT: Traceback: {traceback.format_exc()}", "error")
        return

    # Delete any existing webhook before starting polling
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.bot.delete_webhook(drop_pending_updates=True))
        loop.close()
        _log("BOT: Existing webhook deleted (if any)")
    except Exception as e:
        _log(f"BOT: Webhook cleanup warning (non-fatal): {e}")

    # ── Command handlers ──────────────────────────────────────────────
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("verify", verify_code))
    application.add_handler(CommandHandler("schedule", schedule))
    application.add_handler(CommandHandler("students", students))
    application.add_handler(CommandHandler("tasks", tasks))
    application.add_handler(CommandHandler("tasks_stats", tasks_stats))
    application.add_handler(CommandHandler("resubmit_group", resubmit_group))

    # ── Message handler for rejection comment ─────────────────────────
    # Registered BEFORE the generic code handler to catch rejection comments
    from telegram.ext import MessageHandler, filters
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_rejection_comment
    ))
    
    # ── Message handler for plain text 6-digit code entry ─────────────
    # Must be registered after rejection comment handler
    application.add_handler(get_message_handler())

    # ── Callback handlers ─────────────────────────────────────────────
    application.add_handler(CallbackQueryHandler(menu_schedule, pattern=r"^menu_schedule$"))
    application.add_handler(CallbackQueryHandler(menu_students, pattern=r"^menu_students$"))
    application.add_handler(CallbackQueryHandler(menu_tasks, pattern=r"^menu_tasks$"))
    application.add_handler(CallbackQueryHandler(menu_help, pattern=r"^menu_help$"))
    application.add_handler(CallbackQueryHandler(menu_back, pattern=r"^menu_back$"))
    application.add_handler(CallbackQueryHandler(claim_lead, pattern=r"^claim:"))
    application.add_handler(CallbackQueryHandler(confirm_group, pattern=r"^confirm_group:"))
    application.add_handler(CallbackQueryHandler(confirm_group_yes, pattern=r"^confirm_group_yes:"))
    application.add_handler(CallbackQueryHandler(reject_group_yes, pattern=r"^reject_group_yes:"))
    application.add_handler(CallbackQueryHandler(cancel_action, pattern=r"^cancel_action:"))
    application.add_handler(CallbackQueryHandler(reject_group, pattern=r"^reject_group:"))
    application.add_handler(CallbackQueryHandler(show_group_students, pattern=r"^st_group:"))
    application.add_handler(CallbackQueryHandler(handle_students_back, pattern=r"^st_back$"))
    application.add_handler(CallbackQueryHandler(task_set_status, pattern=r"^task_set:"))
    application.add_handler(CallbackQueryHandler(task_filter, pattern=r"^task_filter:"))
    application.add_handler(CallbackQueryHandler(menu_tasks_stats, pattern=r"^menu_tasks_stats$"))
    application.add_handler(CallbackQueryHandler(resubmit_group_callback, pattern=r"^resubmit_group:"))

    _log("BOT: Starting polling...")
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
    except Exception as e:
        _log(f"BOT: Polling error: {e}", "error")
        _log(f"BOT: Traceback: {traceback.format_exc()}", "error")
        raise
