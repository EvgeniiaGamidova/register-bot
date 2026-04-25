import asyncio
import logging
from datetime import datetime
from uuid import uuid4

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from command import take_keyboard
from config import GROUP_CHAT_ID
from access_utils import format_user_display
from group_message_utils import redirect_to_private_for_request_creation, safe_apply_status_color, send_request_to_group
from history_utils import append_history_entry
from keyboards import SKIP_BUTTON_TEXT, skip_keyboard, urgency_keyboard
from presenters import build_request_text
from request_store import save_request_meta
from sheets_schema import STATUS_NEW
from sheets_writes import append_request_row
from states import NewRequest
from telegram_utils import answer_private, run_blocking
from validators import PHONE_FORMAT_HINT, URGENCY_VALUES, normalize_phone

router = Router()
logger = logging.getLogger(__name__)
_submission_locks: dict[tuple[int, int], asyncio.Lock] = {}


def _is_skip_value(message: Message) -> bool:
    return message.chat.type == "private" and (message.text or "").strip().lower() == SKIP_BUTTON_TEXT.lower()


def _optional_value(message: Message) -> str:
    return "" if _is_skip_value(message) else (message.text or "").strip()


def _optional_reply_markup(message: Message):
    return skip_keyboard if message.chat.type == "private" else None


async def _ensure_private_creation(message: Message, state: FSMContext) -> bool:
    return await redirect_to_private_for_request_creation(message, state)


def _build_contact_info(contact: str, phone: str) -> str:
    values = [value for value in (contact.strip(), phone.strip()) if value]
    return " | ".join(values)


def _get_submission_lock(message: Message) -> asyncio.Lock:
    key = (message.chat.id, message.from_user.id)
    if key not in _submission_locks:
        _submission_locks[key] = asyncio.Lock()
    return _submission_locks[key]


async def _save_and_advance(
    message: Message,
    state: FSMContext,
    *,
    key: str,
    value: str,
    prompt: str,
    next_state,
    reply_markup=None,
) -> None:
    await state.update_data(**{key: value})
    await message.answer(prompt, reply_markup=reply_markup)
    await state.set_state(next_state)


@router.message(NewRequest.object_name)
async def get_object(message: Message, state: FSMContext) -> None:
    if await _ensure_private_creation(message, state):
        return

    await _save_and_advance(
        message,
        state,
        key="object_name",
        value=_optional_value(message),
        prompt="Фактический адрес объекта:",
        next_state=NewRequest.address,
        reply_markup=_optional_reply_markup(message),
    )


@router.message(NewRequest.address)
async def get_address(message: Message, state: FSMContext) -> None:
    if await _ensure_private_creation(message, state):
        return

    await _save_and_advance(
        message,
        state,
        key="address",
        value=_optional_value(message),
        prompt="Описание заявки:",
        next_state=NewRequest.reason,
        reply_markup=_optional_reply_markup(message),
    )


@router.message(NewRequest.reason)
async def get_reason(message: Message, state: FSMContext) -> None:
    if await _ensure_private_creation(message, state):
        return

    await _save_and_advance(
        message,
        state,
        key="reason",
        value=_optional_value(message),
        prompt="Срочность выполнения:",
        next_state=NewRequest.urgency,
        reply_markup=urgency_keyboard,
    )


@router.message(NewRequest.urgency)
async def get_urgency(message: Message, state: FSMContext) -> None:
    if await _ensure_private_creation(message, state):
        return

    urgency = (message.text or "").strip().lower()
    if urgency not in URGENCY_VALUES:
        await message.answer("Выберите срочность кнопкой: Срочно, Не срочно или ТО.")
        return

    reply_markup = _optional_reply_markup(message) if message.chat.type == "private" else ReplyKeyboardRemove()
    await _save_and_advance(
        message,
        state,
        key="urgency",
        value=URGENCY_VALUES[urgency],
        prompt="Вид оборудования:",
        next_state=NewRequest.equipment,
        reply_markup=reply_markup,
    )


@router.message(NewRequest.equipment)
async def get_equipment(message: Message, state: FSMContext) -> None:
    if await _ensure_private_creation(message, state):
        return

    await _save_and_advance(
        message,
        state,
        key="equipment",
        value=_optional_value(message),
        prompt="Контактное лицо:",
        next_state=NewRequest.contact,
        reply_markup=_optional_reply_markup(message),
    )


@router.message(NewRequest.contact)
async def get_contact(message: Message, state: FSMContext) -> None:
    if await _ensure_private_creation(message, state):
        return

    await _save_and_advance(
        message,
        state,
        key="contact",
        value=_optional_value(message),
        prompt="Номер телефона:",
        next_state=NewRequest.phone,
        reply_markup=_optional_reply_markup(message),
    )


@router.message(NewRequest.phone)
async def finish_request(message: Message, state: FSMContext) -> None:
    if await _ensure_private_creation(message, state):
        return

    phone = ""
    if not _is_skip_value(message):
        normalized_phone = normalize_phone(message.text or "")
        if not normalized_phone:
            await message.answer(f"Не удалось распознать номер. {PHONE_FORMAT_HINT}")
            return
        phone = normalized_phone

    await _save_and_advance(
        message,
        state,
        key="phone",
        value=phone,
        prompt="Примечание:",
        next_state=NewRequest.note,
        reply_markup=_optional_reply_markup(message),
    )


@router.message(NewRequest.note)
async def finish_request_with_note(message: Message, state: FSMContext) -> None:
    if await _ensure_private_creation(message, state):
        return

    async with _get_submission_lock(message):
        if await state.get_state() != NewRequest.note.state:
            return

        await state.update_data(note=_optional_value(message))
        data = await state.get_data()

        request_id = f"REQ-{uuid4().hex[:8].upper()}"
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        creator_display = format_user_display(message)
        note = data.get("note", "")
        contact_info = _build_contact_info(data.get("contact", ""), data.get("phone", ""))

        try:
            await run_blocking(
                append_request_row,
                [
                    request_id,
                    now,
                    data["object_name"],
                    data["address"],
                    data["reason"],
                    data["urgency"],
                    data["equipment"],
                    contact_info,
                    "",
                    STATUS_NEW,
                    note,
                    creator_display,
                ],
            )
        except Exception:
            await answer_private(
                message,
                "Не удалось сохранить заявку в Google Sheets. Проверьте интернет, доступ сервисного аккаунта к таблице и настройки .env.",
            )
            return

        await run_blocking(
            append_history_entry,
            request_id=request_id,
            changed_by=creator_display,
            action="Создание заявки",
            field_name="Статус",
            old_value="",
            new_value=STATUS_NEW,
        )
        await run_blocking(safe_apply_status_color, request_id, STATUS_NEW)
        await answer_private(message, f"Заявка создана.\nID заявки: {request_id}")

        sent_message = None
        request_text = build_request_text(
            {
                "object_name": data["object_name"],
                "address": data["address"],
                "description": data["reason"],
                "status": STATUS_NEW,
                "urgency": data["urgency"],
                "equipment": data["equipment"],
                "contact": data.get("contact", ""),
                "phone": data.get("phone", ""),
                "note": note,
            },
            request_id,
            now,
            creator_display,
        )

        if GROUP_CHAT_ID:
            sent_message = await send_request_to_group(
                message.bot,
                request_text,
                take_keyboard(request_id),
            )
        else:
            await answer_private(message, "GROUP_CHAT_ID не настроен, поэтому уведомление в рабочий чат пока не отправлено.")

        await run_blocking(
            save_request_meta,
            request_id=request_id,
            creator_user_id=message.from_user.id,
            group_message_id=sent_message.message_id if sent_message else None,
        )

        logger.info("request_created request_id=%s creator_id=%s", request_id, message.from_user.id)
        await state.clear()
