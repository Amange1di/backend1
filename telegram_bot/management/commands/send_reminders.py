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
    help = "Send Telegram reminders for upcoming lessons, payment debts, and daily summaries"

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
        parser.add_argument(
            "--payment-reminders",
            action="store_true",
            help="Also send payment debt reminders to students",
        )

    def handle(self, *args, **options):
        minutes_ahead = options["minutes"]
        send_summary = options["summary"]
        send_payment_reminders = options.get("payment_reminders", False)

        try:
            import asyncio
            from telegram_bot.helpers import get_upcoming_groups, _get_students_with_debt
            from telegram_bot.notifications import (
                send_lesson_reminder,
                send_daily_lead_summary,
                send_payment_reminder,
            )

            async def run():
                # ── Lesson reminders ──
                self.stdout.write(
                    self.style.NOTICE(
                        f"Checking for lessons starting in ~{minutes_ahead} minutes..."
                    )
                )
                groups = await asyncio.to_thread(get_upcoming_groups, minutes_ahead)
                if not groups:
                    self.stdout.write(self.style.SUCCESS("  No upcoming lessons found."))
                else:
                    for group in groups:
                        await send_lesson_reminder(group)
                        self.stdout.write(
                            self.style.SUCCESS(f"  ✓ Lesson reminder sent: {group.name} ({group.schedule_time})")
                        )

                # ── Daily lead summary ──
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
                                self.style.SUCCESS(f"  ✓ Lead summary sent: {company_name}")
                            )

                # ── Payment debt reminders ──
                if send_payment_reminders:
                    self.stdout.write(
                        self.style.NOTICE("Checking for overdue payments...")
                    )
                    from core.models import Company

                    companies_qs = Company.objects.filter(is_active=True)
                    for company in companies_qs:
                        debtors = await _get_students_with_debt(company.name)
                        if not debtors:
                            continue
                        for student, payment, days_overdue in debtors:
                            await send_payment_reminder(student, payment, days_overdue)
                            await asyncio.to_thread(
                                _mark_payment_reminder_sent_sync,
                                payment.id,
                            )
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  ✓ Payment reminder sent: {student.first_name} - {payment.amount} сом ({days_overdue} дн.)"
                                )
                            )
                        self.stdout.write(
                            self.style.WARNING(
                                f"    Company '{company.name}': {len(debtors)} debtors notified"
                            )
                        )
                    self.stdout.write(
                        self.style.SUCCESS("Payment reminders completed.")
                    )

            asyncio.run(run())

        except ImportError as e:
            self.stderr.write(self.style.ERROR(f"Failed to import bot module: {e}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error sending reminders: {e}"))
            logger.exception("Error in send_reminders")


def _mark_payment_reminder_sent_sync(payment_id: int):
    """Sync helper to mark payment reminder as sent (called via asyncio.to_thread)."""
    from core.models import Payment
    from django.utils import timezone
    Payment.objects.filter(id=payment_id).update(reminder_sent_at=timezone.now())
