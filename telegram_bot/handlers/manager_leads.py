from asgiref.sync import sync_to_async
"""
Manager handlers.

Commands:
  /tasks  — list tasks (all / active / completed)

Callbacks:
  menu_tasks           — tasks from menu button
  task_set:<id>:<st>   — change task status
  task_filter:<name>   — filter task list
  claim:<lead_id>      — claim a lead
"""

import re

import bleach
from core.models import Task, User, TrialLead

from ..config import (
    Update,
    ContextTypes,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    logger,
)
from ..helpers import (
    _get_user_by_chat_id,
    _get_manager_tasks_by_status,
    _get_task_by_id,
    _update_task_status,
    _get_lead_by_id,
    _get_lead_assignment,
    _claim_lead_once,
)
from ..notifications import send_task_status_changed_notification


# ═══════════════════════════════════════════════════════════════════════
#  TASKS COMMAND
# ═══════════════════════════════════════════════════════════════════════

async def claim_lead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 'Взять в работу' button callback."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("claim:"):
        return

    lead_id = int(data.split(":")[1])
    chat_id = update.effective_chat.id

    try:
        lead = await _get_lead_by_id(lead_id)
    except TrialLead.DoesNotExist:
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(text=query.message.text + "\n\n❌ Лид не найден (возможно, удалён).")
        return

    try:
        manager = await _get_user_by_chat_id(chat_id)
    except User.DoesNotExist:
        await query.answer("Вы не зарегистрированы.", show_alert=True)
        return
    if manager.role != User.Role.MANAGER or manager.company_id != lead.company_id:
        await query.answer("Нет доступа к заявке.", show_alert=True)
        return
    if lead.branch_id and not await sync_to_async(manager.branches.filter(id=lead.branch_id, is_active=True).exists)():
        await query.answer("Заявка другого филиала.", show_alert=True)
        return
    success, owner = await _claim_lead_once(lead, manager)
    if not success:
        owner_name = f"{owner.first_name} {owner.last_name}".strip() or owner.username
        await query.answer(f"Заявка уже у менеджера: {owner_name}", show_alert=True)
        return

    manager_name = f"{manager.first_name} {manager.last_name}".strip() or manager.username

    await query.edit_message_reply_markup(reply_markup=None)
    await query.edit_message_text(text=query.message.text + f"\n\n✅ Лид взят менеджером: {manager_name}")
    await query.answer(f"✅ Лид назначен на вас!", show_alert=True)

