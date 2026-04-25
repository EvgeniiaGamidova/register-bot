from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

SKIP_BUTTON_TEXT = "Пропустить"

urgency_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Срочно"), KeyboardButton(text="Не срочно")],
        [KeyboardButton(text="ТО")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите срочность",
)

status_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Новая"), KeyboardButton(text="В работе")],
        [KeyboardButton(text="Есть проблема"), KeyboardButton(text="Выполнено")],
        [KeyboardButton(text="Отменена")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите статус",
)

skip_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=SKIP_BUTTON_TEXT)],
    ],
    resize_keyboard=True,
    input_field_placeholder="Можно пропустить",
)

main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Новая заявка")],
        [KeyboardButton(text="Редактировать последнюю заявку")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие",
)
