from aiogram.fsm.context import FSMContext
from aiogram.types import ForceReply, Message, ReplyKeyboardRemove

from command import EDIT_FIELD_LABELS, edit_request_keyboard
from group_message_utils import redirect_to_private_for_request_creation
from keyboards import skip_keyboard, status_keyboard, urgency_keyboard
from presenters import RequestRow, build_request_text_from_sheet_row
from request_store import get_last_request_id_for_user
from sheets_queries import get_request_row
from states import EditRequest, NewRequest
from telegram_utils import answer_private, private_reply_markup, run_blocking

MENU_NEW_REQUEST = "Новая заявка"
MENU_EDIT_LAST = "Редактировать последнюю заявку"


def get_field_value_from_row(row: RequestRow, field_name: str) -> str:
    field_map = {
        "object_name": row["object_name"],
        "address": row["address"],
        "description": row["description"],
        "status": row["status"],
        "urgency": row["urgency"],
        "equipment": row["equipment"],
        "contact": row["contact"],
        "phone": row["phone"],
        "note": row["note"],
    }
    return field_map.get(field_name, "")


async def start_flow(message: Message, state: FSMContext) -> None:
    if await redirect_to_private_for_request_creation(message, state):
        return

    await state.clear()
    await message.answer("Наименование объекта:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(NewRequest.object_name)


async def start_edit_last_request(message: Message, state: FSMContext) -> None:
    last_request_id = await run_blocking(get_last_request_id_for_user, message.from_user.id)
    if not last_request_id:
        await answer_private(message, "Не удалось найти вашу последнюю заявку для редактирования.")
        return

    row = await run_blocking(get_request_row, last_request_id)
    if not row:
        await answer_private(message, "Последняя заявка не найдена в таблице.")
        return

    await state.clear()
    await message.answer(
        f"Редактируем заявку {last_request_id}. Выберите поле:",
        reply_markup=private_reply_markup(message),
    )
    await message.answer(
        build_request_text_from_sheet_row(row),
        reply_markup=edit_request_keyboard(last_request_id),
    )


async def prompt_request_edit_menu(target_message: Message, request_id: str, *, prefix: str = "edit") -> None:
    await target_message.answer(
        f"Редактирование заявки {request_id}. Выберите поле:",
        reply_markup=edit_request_keyboard(request_id, prefix=prefix),
    )


async def prompt_edit_input(target_message: Message, field_name: str) -> None:
    if field_name == "urgency":
        await target_message.answer("Выберите новую срочность:", reply_markup=urgency_keyboard)
        return
    if field_name == "status":
        await target_message.answer("Выберите новый статус:", reply_markup=status_keyboard)
        return

    reply_markup = (
        ForceReply(input_field_placeholder="Введите новое значение")
        if target_message.chat.type != "private"
        else skip_keyboard
    )
    await target_message.answer(
        f"Введите новое значение для поля «{EDIT_FIELD_LABELS[field_name]}» ответом на это сообщение:",
        reply_markup=reply_markup,
    )


async def begin_edit_session(state: FSMContext, request_id: str, field_name: str) -> None:
    await state.clear()
    await state.update_data(request_id=request_id, edit_field=field_name)
    await state.set_state(EditRequest.waiting_for_value)
