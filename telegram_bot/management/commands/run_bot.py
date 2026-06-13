"""
Management command to run the Telegram bot.

Usage:
    python manage.py run_bot

This starts polling for Telegram updates (commands, button callbacks).
Run this alongside the Django server (e.g. in a separate terminal or
via a process manager like supervisor/systemd).
"""

import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run the Telegram bot for lead notifications"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Telegram bot..."))
        try:
            from telegram_bot.bot import run_bot

            run_bot()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nBot stopped by user."))
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"Failed to start bot: {e}")
            )
            logger.exception("Bot failed to start")
