import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from access_utils import (
    callback_request_id,
    can_edit_request,
    can_manage_request,
    format_callback_user_display,
    get_request_row_or_alert,
)
from group_message_utils import finalize_request_action
from history_utils import history_timestamp
from sheets_queries import get_assigned_employee
from sheets_schema import STATUS_CANCELED, STATUS_COMPLETED, STATUS_IN_PROGRESS, STATUS_NEW
from sheets_writes import append_employee_activity, assign_request, cancel_request, mark_request_completed, unassign_request
from telegram_utils import answer_callback, run_blocking

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("take_"))
async def take_request(callback: CallbackQuery) -> None:
    request_id = callback_request_id(callback)
    employee_display = format_callback_user_display(callback)

    row = await get_request_row_or_alert(callback, request_id)
    if row is None:
        return

    if row["assigned_employee"]:
        await answer_callback(callback, f"Эта заявка уже закреплена за {row['assigned_employee']}.")
        return

    try:
        was_assigned = await run_blocking(assign_request, request_id, employee_display)
    except Exception:
        await answer_callback(callback, "Не удалось подключиться к Google Sheets.")
        return

    if not was_assigned:
        assigned_employee = await run_blocking(get_assigned_employee, request_id) or "другим сотрудником"
        await answer_callback(callback, f"Эта заявка уже закреплена за {assigned_employee}.")
        return

    await finalize_request_action(
        callback,
        request_id=request_id,
        status=STATUS_IN_PROGRESS,
        history_entries=[
            {
                "request_id": request_id,
                "changed_by": employee_display,
                "action": "Назначение исполнителя",
                "field_name": "Назначеный сотрудник",
                "old_value": "",
                "new_value": employee_display,
            },
            {
                "request_id": request_id,
                "changed_by": employee_display,
                "action": "Изменение статуса",
                "field_name": "Статус",
                "old_value": row["status"],
                "new_value": STATUS_IN_PROGRESS,
            },
        ],
        log_event="request_taken",
        success_message="Заявка закреплена за вами.",
        logger=logger,
    )


async def _close_request(
    callback: CallbackQuery,
    *,
    request_id: str,
    row,
    status: str,
    updater,
    history_action: str,
    log_event: str,
    success_message: str,
) -> None:
    try:
        was_updated = await run_blocking(updater, request_id)
    except Exception:
        await answer_callback(callback, "Не удалось подключиться к Google Sheets.")
        return

    if not was_updated:
        await answer_callback(callback, "Не удалось обновить статус заявки.")
        return

    actor = format_callback_user_display(callback)
    await finalize_request_action(
        callback,
        request_id=request_id,
        status=status,
        history_entries=[
            {
                "request_id": request_id,
                "changed_by": actor,
                "action": history_action,
                "field_name": "Статус",
                "old_value": row["status"],
                "new_value": status,
            },
        ],
        log_event=log_event,
        success_message=success_message,
        logger=logger,
    )


@router.callback_query(F.data.startswith("done_"))
async def complete_request(callback: CallbackQuery) -> None:
    request_id = callback_request_id(callback)
    row = await get_request_row_or_alert(callback, request_id)
    if row is None:
        return

    if not row["assigned_employee"]:
        await answer_callback(callback, "У заявки нет назначенного исполнителя.")
        return

    if not await can_manage_request(callback, row["assigned_employee"]):
        await answer_callback(callback, "Недостаточно прав для завершения этой заявки.")
        return

    await _close_request(
        callback,
        request_id=request_id,
        row=row,
        status=STATUS_COMPLETED,
        updater=mark_request_completed,
        history_action="Завершение работы",
        log_event="request_completed",
        success_message="Заявка отмечена как выполненная.",
    )
    await run_blocking(
        append_employee_activity,
        row["assigned_employee"],
        request_id=request_id,
        logged_at=history_timestamp(),
        action="Завершил заявку",
        status=STATUS_COMPLETED,
        object_name=row["object_name"],
        address=row["address"],
    )


@router.callback_query(F.data.startswith("cancel_"))
async def cancel_request_action(callback: CallbackQuery) -> None:
    request_id = callback_request_id(callback)
    row = await get_request_row_or_alert(callback, request_id)
    if row is None:
        return

    if not await can_edit_request(callback, row, request_id):
        await answer_callback(callback, "Недостаточно прав для отмены этой заявки.")
        return

    await _close_request(
        callback,
        request_id=request_id,
        row=row,
        status=STATUS_CANCELED,
        updater=cancel_request,
        history_action="Отмена заявки",
        log_event="request_canceled",
        success_message="Заявка отменена.",
    )


@router.callback_query(F.data.startswith("unassign_"))
async def remove_employee(callback: CallbackQuery) -> None:
    request_id = callback_request_id(callback)
    row = await get_request_row_or_alert(callback, request_id)
    if row is None:
        return

    if not row["assigned_employee"]:
        await answer_callback(callback, "У заявки уже нет назначенного исполнителя.")
        return

    if not await can_manage_request(callback, row["assigned_employee"]):
        await answer_callback(callback, "Недостаточно прав для снятия исполнителя.")
        return

    try:
        await run_blocking(unassign_request, request_id)
    except Exception:
        await answer_callback(callback, "Не удалось подключиться к Google Sheets.")
        return

    actor = format_callback_user_display(callback)
    await finalize_request_action(
        callback,
        request_id=request_id,
        status=STATUS_NEW,
        history_entries=[
            {
                "request_id": request_id,
                "changed_by": actor,
                "action": "Снятие исполнителя",
                "field_name": "Назначеный сотрудник",
                "old_value": row["assigned_employee"],
                "new_value": "",
            },
            {
                "request_id": request_id,
                "changed_by": actor,
                "action": "Изменение статуса",
                "field_name": "Статус",
                "old_value": row["status"],
                "new_value": STATUS_NEW,
            },
        ],
        log_event="request_unassigned",
        success_message="Исполнитель снят с заявки.",
        logger=logger,
    )
