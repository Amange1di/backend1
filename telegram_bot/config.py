"""
Telegram Bot — configuration and shared utilities.

Handles Django setup, model imports, BOT_TOKEN, logger, and the
cached Application instance used by all modules.
"""

import logging
import os
from datetime import date, datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ── Django setup (idempotent) ──────────────────────────────────────────
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()

# ── Django / ASGI imports ─────────────────────────────────────────────
from asgiref.sync import sync_to_async
from django.conf import settings
from django.db.models import Q, Count
from django.utils import timezone

# NOTE: core.models are NOT imported here to avoid "Apps aren't loaded yet"
# during Django startup. Each module imports models directly from core.models.

# ── Shared globals ────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN

# Frontend CRM site URL (used for login buttons in bot messages)
FRONTEND_URL = getattr(settings, "FRONTEND_URL", "http://localhost:3000")

_application = None


def _get_application():
    """Return the singleton Application instance."""
    global _application
    if _application is None:
        _application = Application.builder().token(BOT_TOKEN).build()
    return _application
