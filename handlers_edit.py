from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from command import EDIT_FIELD_LABELS
from access_utils import callback_request_id, can_edit_request, format_user_display, get_request_row_or_alert
from flow_utils import begin_edit_session, get_field_value_from_row, prompt_edit_input, prompt_request_edit_menu
from group_message_utils import get_request_row_safe, safe_apply_status_color, safe_refresh_group_request_message
from history_utils import append_history_entry
from keyboards import SKIP_BUTTON_TEXT
from request_store import get_request_meta
from sheets_schema import STATUS_CANCELED, STATUS_COMPLETED, STATUS_IN_PROGRESS, STATUS_ISSUE, STATUS_NEW
from sheets_writes import update_request_field
from states import EditRequest
from telegram_utils import answer_callback, answer_private, private_reply_markup, run_blocking
from validators import PHONE_FORMAT_HINT, URGENCY_VALUES, normalize_phone

router = Router()
STATUS_VALUES = {STATUS_NEW, STATUS_IN_PROGRESS, STATUS_ISSUE, STATUS_COMPLETED, STATUS_CANCELED}


async def _start_edit_selection(
    callback: CallbackQuery,
    state: FSMContext,
    *,
    request_id: str,
    field_name: str,
) -> None:
    if field_name not in EDIT_FIELD_LABELS:
        await answer_callback(callback, "Поле для редактирования не найдено.")
        return

    await begin_edit_session(state, request_id, field_name)
    await prompt_edit_input(callback.message, field_name)
    await callback.answer()


@router.callback_query(F.data.startswith("edit_"))
async def choose_edit_field(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message.chat.type != "private":
        await answer_callback(callback, "Редактирование доступно только в личном чате с ботом.")
        return

    _, request_id, field_name = callback.data.split("_", maxsplit=2)
    meta = await run_blocking(get_request_meta, request_id)
    if not meta or meta.get("creator_user_id") != callback.from_user.id:
        await answer_callback(callback, "Можно редактировать только свою последнюю заявку.")
        return

    await _start_edit_selection(callback, state, request_id=request_id, field_name=field_name)


@router.callback_query(F.data.startswith("editmenu_"))
async def open_group_edit_menu(callback: CallbackQuery) -> None:
    request_id = callback_request_id(callback)
    row = await get_request_row_or_alert(callback, request_id)
    if row is None:
        return

    if not await can_edit_request(callback, row, request_id):
        await answer_callback(callback, "Недостаточно прав для редактирования заявки.")
        return

    await prompt_request_edit_menu(callback.message, request_id, prefix="groupedit")
    await callback.answer()


@router.callback_query(F.data.startswith("groupedit_"))
async def choose_group_edit_field(callback: CallbackQuery, state: FSMContext) -> None:
    _, request_id, field_name = callback.data.split("_", maxsplit=2)
    row = await get_request_row_or_alert(callback, request_id)
    if row is None:
        return

    if not await can_edit_request(callback, row, request_id):
        await answer_callback(callback, "Недостаточно прав для редактирования заявки.")
        return

    await _start_edit_selection(callback, state, request_id=request_id, field_name=field_name)


@router.message(EditRequest.waiting_for_value)
async def save_edited_value(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    request_id = data.get("request_id")
    field_name = data.get("edit_field")

    if not request_id or not field_name:
        await state.clear()
        await message.answer(
            "Сессия редактирования потеряна. Попробуйте снова.",
            reply_markup=private_reply_markup(message),
        )
        return

    row_before = await run_blocking(get_request_row_safe, request_id)
    if not row_before:
        await state.clear()
        await answer_private(message, "Не удалось найти заявку для редактирования.")
        return

    new_value = (message.text or "").strip()
    if not new_value:
        await message.answer("Введите непустое значение.")
        return

    if field_name == "urgency":
        normalized_urgency = new_value.lower()
        if normalized_urgency not in URGENCY_VALUES:
            await message.answer("Выберите срочность кнопкой: Срочно, Не срочно или ТО.")
            return
        new_value = URGENCY_VALUES[normalized_urgency]
    elif field_name == "status":
        if new_value not in STATUS_VALUES:
            await message.answer("Выберите статус кнопкой: Новая, В работе, Есть проблема, Выполнено или Отменена.")
            return
    elif message.chat.type == "private" and new_value.lower() == SKIP_BUTTON_TEXT.lower():
        new_value = ""

    if field_name == "phone":
        if not new_value:
            pass
        else:
            normalized_phone = normalize_phone(new_value)
            if not normalized_phone:
                await message.answer(f"Не удалось распознать номер. {PHONE_FORMAT_HINT}")
                return
            new_value = normalized_phone

    old_value = get_field_value_from_row(row_before, field_name)

    try:
        was_updated = await run_blocking(update_request_field, request_id, field_name, new_value)
    except Exception:
        await answer_private(message, "Не удалось обновить заявку в Google Sheets.")
        await state.clear()
        return

    if not was_updated:
        await answer_private(message, "Не удалось найти заявку для редактирования.")
        await state.clear()
        return

    await run_blocking(
        append_history_entry,
        request_id=request_id,
        changed_by=format_user_display(message),
        action="Редактирование поля",
        field_name=EDIT_FIELD_LABELS[field_name],
        old_value=old_value,
        new_value=new_value,
    )

    if field_name == "status":
        await run_blocking(safe_apply_status_color, request_id, new_value)

    await state.clear()
    await safe_refresh_group_request_message(message.bot, request_id)
