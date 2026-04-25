from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from flow_utils import MENU_EDIT_LAST, MENU_NEW_REQUEST, start_edit_last_request, start_flow
from telegram_utils import answer_private, private_reply_markup

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    if message.chat.type != "private":
        await message.answer(
            "Бот принимает и сопровождает заявки.\n"
            "Что умеет:\n"
            "- создавать заявки\n"
            "- отправлять их в рабочий чат\n"
            "- помогать менять статус и редактировать данные\n\n"
            "Создавать заявки можно только в личных сообщениях. Откройте личный чат с ботом и отправьте /new.",
            reply_markup=private_reply_markup(message),
        )
        return

    await message.answer(
        "Бот помогает работать с заявками.\n"
        "Что можно делать:\n"
        "- /new — создать новую заявку\n"
        "- /cancel — отменить создание заявки\n"
        "- редактировать последнюю заявку\n"
        "- изменять данные и статусы заявок\n"
        "- отправлять заявки в рабочий чат для сотрудников\n"
        "- отслеживать исполнение заявок\n\n"
        "Для начала отправьте /new или выберите действие в меню.",
        reply_markup=private_reply_markup(message),
    )


@router.message(Command("chat_info"))
async def show_chat_info(message: Message) -> None:
    await message.answer(
        f"group_id: {message.chat.id}\n"
        f"topic_id: {message.message_thread_id}",
        reply_markup=private_reply_markup(message),
    )


@router.message(Command("cancel"))
async def cancel_request(message: Message, state: FSMContext) -> None:
    await state.clear()
    await answer_private(message, "Текущее действие отменено.")


@router.message(Command("new"))
async def start_new(message: Message, state: FSMContext) -> None:
    await start_flow(message, state)


@router.message(F.text == MENU_NEW_REQUEST)
async def start_new_from_menu(message: Message, state: FSMContext) -> None:
    if message.chat.type != "private":
        return
    await start_flow(message, state)


@router.message(F.text == MENU_EDIT_LAST)
async def edit_last_from_menu(message: Message, state: FSMContext) -> None:
    if message.chat.type != "private":
        return
    await start_edit_last_request(message, state)
