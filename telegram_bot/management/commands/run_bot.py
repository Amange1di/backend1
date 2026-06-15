"""
Management command to run the Telegram bot.

Usage:
    python manage.py run_bot

This starts polling for Telegram updates (commands, button callbacks).
Run this alongside the Django server (e.g. in a separate terminal or
via a process manager like supervisor/systemd).
"""

import logging
import sys
import traceback

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run the Telegram bot for lead notifications"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("COMMAND: Starting Telegram bot..."))
        self.stdout.flush()
        try:
            from telegram_bot.bot import run_bot

            run_bot()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nCOMMAND: Bot stopped by user."))
            self.stdout.flush()
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"COMMAND: Failed to start bot: {e}")
            )
            self.stderr.flush()
            logger.exception("COMMAND: Bot failed to start")
            # Print full traceback to stderr
            traceback.print_exc()
            sys.stderr.flush()
