from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from command import assigned_keyboard, terminal_keyboard, take_keyboard
from config import GROUP_CHAT_ID, GROUP_TOPIC_ID
from history_utils import append_history_entries
from presenters import RequestRow, build_request_message
from request_store import get_request_meta
from sheets_queries import get_request_row
from sheets_schema import STATUS_CANCELED, STATUS_COMPLETED
from sheets_writes import apply_status_color
from telegram_utils import run_blocking, run_telegram


def get_request_row_safe(request_id: str) -> RequestRow | None:
    try:
        return get_request_row(request_id)
    except Exception:
        return None


def safe_apply_status_color(request_id: str, status: str) -> None:
    try:
        apply_status_color(request_id, status)
    except Exception:
        pass


def build_request_reply_markup(row: RequestRow, request_id: str):
    if row["status"] in {STATUS_COMPLETED, STATUS_CANCELED}:
        return terminal_keyboard(request_id)
    if row["assigned_employee"]:
        return assigned_keyboard(request_id)
    return take_keyboard(request_id)


def _private_chat_redirect_markup(bot_username: str | None) -> InlineKeyboardMarkup | None:
    if not bot_username:
        return None

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Перейти в личные сообщения",
                    url=f"https://t.me/{bot_username}?start=new_request",
                )
            ]
        ]
    )


async def redirect_to_private_for_request_creation(message: Message, state: FSMContext | None = None) -> bool:
    if message.chat.type == "private":
        return False

    if state is not None:
        await state.clear()

    bot_user = await message.bot.get_me()
    await message.answer(
        "Создавать заявки можно только в личных сообщениях с ботом. Перейдите в личный чат и продолжите там.",
        reply_markup=_private_chat_redirect_markup(bot_user.username),
    )
    return True


async def _load_group_request_context(request_id: str) -> tuple[RequestRow | None, dict | None]:
    row = await run_blocking(get_request_row, request_id)
    if not row:
        return None, None

    meta = await run_blocking(get_request_meta, request_id)
    return row, meta


async def _edit_group_request_message(bot, request_id: str, row: RequestRow, meta: dict) -> bool:
    if not meta.get("group_message_id") or not GROUP_CHAT_ID:
        return False

    await run_telegram(
        bot.edit_message_text,
        chat_id=GROUP_CHAT_ID,
        message_id=meta["group_message_id"],
        text=build_request_message(row),
        reply_markup=build_request_reply_markup(row, request_id),
    )
    return True


async def refresh_group_request_message(bot, request_id: str) -> bool:
    row, meta = await _load_group_request_context(request_id)
    if not row or not meta:
        return False

    return await _edit_group_request_message(bot, request_id, row, meta)


async def send_request_to_group(bot, text: str, reply_markup):
    if not GROUP_CHAT_ID:
        return None

    send_kwargs = {
        "chat_id": GROUP_CHAT_ID,
        "text": text,
        "reply_markup": reply_markup,
    }
    if GROUP_TOPIC_ID:
        send_kwargs["message_thread_id"] = GROUP_TOPIC_ID

    return await run_telegram(bot.send_message, **send_kwargs)


async def safe_refresh_group_request_message(bot, request_id: str) -> None:
    try:
        await refresh_group_request_message(bot, request_id)
    except Exception:
        row, meta = await _load_group_request_context(request_id)
        if not row or not meta:
            return

        await _edit_group_request_message(bot, request_id, row, meta)


async def finalize_request_action(
    callback,
    *,
    request_id: str,
    status: str,
    history_entries: list[dict[str, str]],
    log_event: str,
    success_message: str,
    logger,
) -> None:
    await run_blocking(append_history_entries, history_entries)
    await run_blocking(safe_apply_status_color, request_id, status)
    await safe_refresh_group_request_message(callback.bot, request_id)
    logger.info("%s request_id=%s user_id=%s", log_event, request_id, callback.from_user.id)
    await callback.answer(success_message)
