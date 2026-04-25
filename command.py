from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


EDIT_FIELD_LABELS = {
    "object_name": "Название объекта",
    "address": "Адрес объекта",
    "description": "Описание",
    "status": "Статус",
    "urgency": "Срочность",
    "equipment": "Вид оборудования",
    "contact": "Контактное лицо",
    "phone": "Телефон",
}


def _inline_button(text: str, callback_data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=callback_data)


def _single_button_row(text: str, callback_data: str) -> list[InlineKeyboardButton]:
    return [_inline_button(text=text, callback_data=callback_data)]


def _edit_button_row(request_id: str) -> list[InlineKeyboardButton]:
    return _single_button_row("Редактировать", f"editmenu_{request_id}")


def take_keyboard(request_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            _single_button_row("Взять в работу", f"take_{request_id}"),
            _single_button_row("Отменить заявку", f"cancel_{request_id}"),
            _edit_button_row(request_id),
        ]
    )


def assigned_keyboard(request_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            _single_button_row("Работа выполнена", f"done_{request_id}"),
            _single_button_row("Отменить заявку", f"cancel_{request_id}"),
            _single_button_row("Отменить исполнителя", f"unassign_{request_id}"),
            _edit_button_row(request_id),
        ]
    )


def terminal_keyboard(request_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[_edit_button_row(request_id)]
    )


def edit_request_keyboard(request_id: str, prefix: str = "edit") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            _single_button_row(label, f"{prefix}_{request_id}_{field_name}")
            for field_name, label in EDIT_FIELD_LABELS.items()
        ]
    )
