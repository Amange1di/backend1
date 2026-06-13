"""
Management command to send lesson reminders via Telegram bot.

Runs periodically (e.g. every 5 minutes via cron/systemd timer).
Checks for lessons starting in ~30 minutes and sends reminders
to teachers and students.

Usage:
    python manage.py send_reminders
    python manage.py send_reminders --minutes 30

Recommended cron: */5 * * * * cd /path/to/backend1 && python3 manage.py send_reminders
"""

import logging
from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send Telegram reminders for upcoming lessons"

    def add_arguments(self, parser):
        parser.add_argument(
            "--minutes",
            type=int,
            default=30,
            help="Minutes ahead to check for lessons (default: 30)",
        )
        parser.add_argument(
            "--summary",
            action="store_true",
            help="Also send daily lead summary to course admins",
        )

    def handle(self, *args, **options):
        minutes_ahead = options["minutes"]
        send_summary = options["summary"]

        self.stdout.write(
            self.style.NOTICE(
                f"Checking for lessons starting in ~{minutes_ahead} minutes..."
            )
        )

        try:
            import asyncio
            from telegram_bot.helpers import get_upcoming_groups
            from telegram_bot.notifications import send_lesson_reminder, send_daily_lead_summary

            async def run():
                groups = await asyncio.to_thread(get_upcoming_groups, minutes_ahead)
                if not groups:
                    self.stdout.write(self.style.SUCCESS("No upcoming lessons found."))
                else:
                    for group in groups:
                        await send_lesson_reminder(group)
                        self.stdout.write(
                            self.style.SUCCESS(f"  ✓ Reminder sent for group: {group.name} ({group.schedule_time})")
                        )

                if send_summary:
                    from django.db.models import Count
                    from core.models import TrialLead

                    today = date.today()
                    companies = (
                        TrialLead.objects
                        .filter(created_at__date=today)
                        .values_list("company_name", flat=True)
                        .distinct()
                    )
                    for company_name in companies:
                        if company_name:
                            await send_daily_lead_summary(company_name)
                            self.stdout.write(
                                self.style.SUCCESS(f"  ✓ Summary sent for company: {company_name}")
                            )

            asyncio.run(run())

        except ImportError as e:
            self.stderr.write(self.style.ERROR(f"Failed to import bot module: {e}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error sending reminders: {e}"))
            logger.exception("Error in send_reminders")
