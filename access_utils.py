from aiogram.types import CallbackQuery, Message

from presenters import RequestRow
from request_store import get_request_meta
from sheets_queries import get_request_lookup_debug, get_request_row
from telegram_utils import answer_callback, run_blocking


def _format_user_display(full_name: str, username: str | None) -> str:
    if username:
        return f"{full_name} (@{username})"
    return full_name


def format_user_display(message: Message) -> str:
    return _format_user_display(message.from_user.full_name, message.from_user.username)


def format_callback_user_display(callback: CallbackQuery) -> str:
    return _format_user_display(callback.from_user.full_name, callback.from_user.username)


def callback_request_id(callback: CallbackQuery) -> str:
    return callback.data.split("_", maxsplit=1)[1].strip()


async def can_manage_request(callback: CallbackQuery, assigned_employee: str) -> bool:
    return assigned_employee == format_callback_user_display(callback)


async def can_edit_request(callback: CallbackQuery, row: RequestRow, request_id: str) -> bool:
    if row["assigned_employee"] == format_callback_user_display(callback):
        return True

    meta = await run_blocking(get_request_meta, request_id)
    return bool(meta and meta.get("creator_user_id") == callback.from_user.id)


async def get_request_row_or_alert(callback: CallbackQuery, request_id: str) -> RequestRow | None:
    try:
        row = await run_blocking(get_request_row, request_id)
    except Exception:
        await answer_callback(callback, "Не удалось подключиться к Google Sheets.")
        return None

    if row is None:
        debug_text = await run_blocking(get_request_lookup_debug, request_id)
        await answer_callback(callback, f"Заявка не найдена в таблице.\n{debug_text}")
        return None

    return row
