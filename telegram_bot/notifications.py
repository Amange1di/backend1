"""
Notification sender functions.

Each function sends a Telegram message via the shared Application instance.
Called from Django signals or management commands.
"""

from datetime import date

from .config import (
    BOT_TOKEN,
    _get_application,
    logger,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    User,
    TrialLead,
    Group,
    HomeworkSubmission,
    HomeworkTask,
    Task,
    Student,
)
from .helpers import (
    _get_lead_company_name,
    _get_managers_for_company,
    _get_course_admins_for_company,
    _get_group_course_name,
    _get_group_company_name,
    _get_students_for_group,
    _get_submission_student_name,
    _get_submission_task_title,
    _get_submission_task_group_name,
    _get_task_created_by_name,
    _get_task_assigned_to_name,
    _get_task_company_name,
    _get_superadmins,
    sync_to_async,
)


async def send_lead_notification(lead: TrialLead):
    """Send a new lead notification to all managers of the company."""
    if not BOT_TOKEN:
        return

    company_name = await _get_lead_company_name(lead)
    if not company_name:
        logger.warning(f"Lead {lead.id} has no company")
        return

    managers = await _get_managers_for_company(company_name)
    if not managers:
        return

    text = (
        f"🔔 <b>Новый лид!</b>\n\n"
        f"👤 <b>Имя:</b> {lead.full_name}\n"
        f"📞 <b>Телефон:</b> {lead.phone}\n"
        f"📚 <b>Курс:</b> {lead.course_interest or '—'}\n"
        f"📝 <b>Комментарий:</b> {lead.comment or '—'}\n"
        f"📅 <b>Дата:</b> {lead.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"🌐 <b>Источник:</b> {lead.source or '—'}"
    )

    keyboard = [[InlineKeyboardButton("✅ Взять в работу", callback_data=f"claim:{lead.id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    application = _get_application()
    for manager in managers:
        try:
            await application.bot.send_message(
                chat_id=manager.telegram_chat_id,
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
        except Exception as e:
            logger.error(f"Failed to send lead notification to {manager.username}: {e}")


async def send_group_confirmation(group: Group, teacher: User):
    """Send a group confirmation request to the assigned teacher."""
    if not BOT_TOKEN or not teacher.telegram_chat_id:
        return

    course_name = await _get_group_course_name(group)

    text = (
        f"👨‍🏫 <b>Вас назначили на группу!</b>\n\n"
        f"📚 <b>Группа:</b> {group.name}\n"
        f"📖 <b>Курс:</b> {course_name}\n"
        f"📅 <b>Расписание:</b> {group.schedule_days or '—'} в {group.schedule_time or '—'}\n"
        f"📆 <b>Старт:</b> {group.start_date or '—'}\n\n"
        f"Подтвердите, чтобы открыть группу для студентов:"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Принять", callback_data=f"confirm_group:{group.id}"),
            InlineKeyboardButton("❌ Отказаться", callback_data=f"reject_group:{group.id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    application = _get_application()
    try:
        await application.bot.send_message(
            chat_id=teacher.telegram_chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
    except Exception as e:
        logger.error(f"Failed to send group confirmation to {teacher.username}: {e}")


async def send_homework_submission_notification(submission: HomeworkSubmission):
    """Send a notification to the teacher when a student submits homework."""
    if not BOT_TOKEN:
        return

    teacher = submission.task.teacher
    if not teacher or not teacher.telegram_chat_id:
        return

    student_name = await _get_submission_student_name(submission)
    task_title = await _get_submission_task_title(submission)
    group_name = await _get_submission_task_group_name(submission)

    text = (
        f"📚 <b>Студент сдал домашнее задание!</b>\n\n"
        f"👤 <b>Студент:</b> {student_name}\n"
        f"📝 <b>Задание:</b> {task_title}\n"
        f"👥 <b>Группа:</b> {group_name}\n"
        f"📅 <b>Сдано:</b> {submission.submitted_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"📊 <b>Статус:</b> Ожидает проверки"
    )

    application = _get_application()
    try:
        await application.bot.send_message(
            chat_id=teacher.telegram_chat_id,
            text=text,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Failed to send homework notification to {teacher.username}: {e}")


async def send_lesson_reminder(group: Group):
    """Send a reminder about an upcoming lesson to teacher and students."""
    if not BOT_TOKEN:
        return

    course_name = await _get_group_course_name(group)

    # Notify teacher
    if group.teacher and group.teacher.telegram_chat_id:
        text_teacher = (
            f"🔔 <b>Урок через 30 минут!</b>\n\n"
            f"📚 <b>Группа:</b> {group.name}\n"
            f"📖 <b>Курс:</b> {course_name}\n"
            f"⏰ <b>Время:</b> {group.schedule_time or '—'}\n"
            f"📍 <b>Аудитория:</b> {group.auditorium.name if group.auditorium else '—'}"
        )
        application = _get_application()
        try:
            await application.bot.send_message(
                chat_id=group.teacher.telegram_chat_id,
                text=text_teacher,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Failed to send lesson reminder to teacher {group.teacher.username}: {e}")

    # Notify students
    students = await _get_students_for_group(group.id)
    if students:
        text_student = (
            f"🔔 <b>Урок через 30 минут!</b>\n\n"
            f"📚 <b>Группа:</b> {group.name}\n"
            f"⏰ <b>Время:</b> {group.schedule_time or '—'}\n"
            f"👨‍🏫 <b>Учитель:</b> {group.teacher.first_name if group.teacher else '—'}"
        )
        application = _get_application()
        for student in students:
            try:
                await application.bot.send_message(
                    chat_id=student.user.telegram_chat_id,
                    text=text_student,
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.error(f"Failed to send lesson reminder to student {student.id}: {e}")


async def send_homework_assigned_notification(group: Group, task: HomeworkTask):
    """Send notification to students about a new homework assignment."""
    if not BOT_TOKEN:
        return

    students = await _get_students_for_group(group.id)
    if not students:
        return

    deadline_str = task.deadline.strftime("%d.%m.%Y %H:%M") if task.deadline else "—"
    text = (
        f"📝 <b>Новое домашнее задание!</b>\n\n"
        f"📚 <b>Группа:</b> {group.name}\n"
        f"📖 <b>Задание:</b> {task.title}\n"
        f"{'📄 ' + task.description[:200] if task.description else ''}\n"
        f"⏰ <b>Дедлайн:</b> {deadline_str}"
    )

    application = _get_application()
    for student in students:
        try:
            await application.bot.send_message(
                chat_id=student.user.telegram_chat_id,
                text=text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Failed to send homework notification to student {student.id}: {e}")


async def send_submission_reviewed_notification(submission: HomeworkSubmission):
    """Send notification to student when their homework is reviewed."""
    if not BOT_TOKEN:
        return

    student = submission.student
    if not student.user or not student.user.telegram_chat_id:
        return

    task_title = await _get_submission_task_title(submission)
    grade_text = f"\n📊 <b>Оценка:</b> {submission.grade}/100" if submission.grade is not None else ""
    comment_text = f"\n💬 <b>Комментарий:</b> {submission.teacher_comment}" if submission.teacher_comment else ""

    text = (
        f"✅ <b>Домашнее задание проверено!</b>\n\n"
        f"📝 <b>Задание:</b> {task_title}"
        f"{grade_text}"
        f"{comment_text}"
    )

    application = _get_application()
    try:
        await application.bot.send_message(
            chat_id=student.user.telegram_chat_id,
            text=text,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Failed to send review notification to student {student.id}: {e}")


async def send_task_assigned_notification(task: Task):
    """Send a notification to the manager when a task is assigned."""
    if not BOT_TOKEN:
        return

    manager = task.assigned_to
    if not manager or not manager.telegram_chat_id:
        return

    created_by_name = await _get_task_created_by_name(task)
    priority_emoji = {
        Task.Priority.LOW: "🟢",
        Task.Priority.MEDIUM: "🟡",
        Task.Priority.HIGH: "🔴",
    }
    priority = priority_emoji.get(task.priority, "🟡")
    deadline_str = f"{task.due_date.strftime('%d.%m.%Y')}"
    if task.due_time:
        deadline_str += f" {task.due_time.strftime('%H:%M')}"

    text = (
        f"📋 <b>Новая задача!</b>\n\n"
        f"📝 <b>Задача:</b> {task.title}\n"
        f"{'📄 ' + task.description[:300] if task.description else ''}\n"
        f"{priority} <b>Приоритет:</b> {task.get_priority_display()}\n"
        f"⏰ <b>Срок:</b> {deadline_str}\n"
        f"👤 <b>Поставил:</b> {created_by_name}\n"
        f"🔄 <b>Статус:</b> {task.get_status_display()}"
    )

    keyboard = [[InlineKeyboardButton("▶️ Взять в работу", callback_data=f"task_set:{task.id}:in_progress")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    application = _get_application()
    try:
        await application.bot.send_message(
            chat_id=manager.telegram_chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
    except Exception as e:
        logger.error(f"Failed to send task notification to {manager.username}: {e}")


async def send_task_status_changed_notification(task: Task):
    """Send a notification to course admins when a manager changes task status."""
    if not BOT_TOKEN:
        return

    company_name = await _get_task_company_name(task)
    if not company_name:
        return

    admins = await _get_course_admins_for_company(company_name)
    if not admins:
        return

    manager_name = await _get_task_assigned_to_name(task)
    status_emoji = {
        Task.Status.PENDING: "🕐",
        Task.Status.IN_PROGRESS: "🔄",
        Task.Status.COMPLETED: "✅",
    }
    status_icon = status_emoji.get(task.status, "📋")

    text = (
        f"{status_icon} <b>Статус задачи изменён!</b>\n\n"
        f"📝 <b>Задача:</b> {task.title}\n"
        f"👤 <b>Исполнитель:</b> {manager_name}\n"
        f"📊 <b>Новый статус:</b> {task.get_status_display()}\n"
    )

    if task.status == Task.Status.COMPLETED and task.completed_at:
        text += f"✅ <b>Завершена:</b> {task.completed_at.strftime('%d.%m.%Y %H:%M')}"

    application = _get_application()
    for admin in admins:
        try:
            await application.bot.send_message(
                chat_id=admin.telegram_chat_id,
                text=text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Failed to send task status notification to {admin.username}: {e}")


async def send_daily_lead_summary(company_name: str):
    """Send a daily summary of new leads to course admins."""
    if not BOT_TOKEN:
        return

    admins = await _get_course_admins_for_company(company_name)
    if not admins:
        return

    today = date.today()

    @sync_to_async
    def _get_today_leads_stats(cname: str):
        leads_today = TrialLead.objects.filter(
            company_name=cname,
            created_at__date=today,
        )
        total = leads_today.count()
        contacted = leads_today.filter(status=TrialLead.Status.CONTACTED).count()
        return total, contacted

    total, contacted = await _get_today_leads_stats(company_name)
    if total == 0:
        return

    text = (
        f"📊 <b>Сводка за сегодня</b>\n\n"
        f"🏢 <b>{company_name}</b>\n"
        f"🆕 Новых лидов: {total}\n"
        f"📞 В работе: {contacted}"
    )

    application = _get_application()
    for admin in admins:
        try:
            await application.bot.send_message(
                chat_id=admin.telegram_chat_id,
                text=text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Failed to send summary to admin {admin.username}: {e}")


async def send_new_student_notification(student: Student):
    """Send a notification about a new student to all managers of the company."""
    if not BOT_TOKEN:
        return

    company_name = getattr(student, "company_name", None)
    if not company_name and student.company:
        company_name = student.company.name
    if not company_name:
        logger.warning(f"Student {student.id} has no company")
        return

    managers = await _get_managers_for_company(company_name)
    if not managers:
        return

    full_name = f"{student.first_name} {student.last_name}".strip()
    text = (
        f"🆕 <b>Новый клиент!</b>\n\n"
        f"👤 <b>Имя:</b> {full_name}\n"
        f"📞 <b>Телефон:</b> {student.phone}\n"
        f"📱 <b>Telegram:</b> {student.telegram or '—'}\n"
        f"📅 <b>Создан:</b> {student.created_at.strftime('%d.%m.%Y %H:%M') if student.created_at else '—'}"
    )

    application = _get_application()
    for manager in managers:
        try:
            await application.bot.send_message(
                chat_id=manager.telegram_chat_id,
                text=text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Failed to send new student notification to {manager.username}: {e}")


async def send_crm_contact_notification(
    full_name: str,
    phone: str,
    comment: str,
    telegram: str = "",
):
    """Send a notification about a new CRM website contact to all superadmins.

    This is for the CRM's own landing page (not company-specific).
    """
    if not BOT_TOKEN:
        return

    superadmins = await _get_superadmins()
    if not superadmins:
        logger.warning("No superadmins with Telegram found")
        return

    text = (
        f"🌐 <b>Новая заявка с CRM-сайта!</b>\n\n"
        f"👤 <b>Имя:</b> {full_name}\n"
        f"📞 <b>Телефон:</b> {phone}\n"
        f"{'💬 <b>Telegram:</b> ' + telegram + '\n' if telegram else ''}"
        f"📝 <b>Сообщение:</b> {comment or '—'}"
    )

    application = _get_application()
    for admin in superadmins:
        try:
            await application.bot.send_message(
                chat_id=admin.telegram_chat_id,
                text=text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Failed to send CRM contact notification to {admin.username}: {e}")
