import asyncio
import time

from aiogram.types import CallbackQuery, Message

from keyboards import main_menu_keyboard


def private_reply_markup(message: Message):
    return main_menu_keyboard if message.chat.type == "private" else None


async def answer_private(message: Message, text: str) -> None:
    await message.answer(text, reply_markup=private_reply_markup(message))


async def answer_callback(callback: CallbackQuery, text: str, *, show_alert: bool = True) -> None:
    await callback.answer(text, show_alert=show_alert)


def retry(fn, *, attempts=3, base_delay=0.5, exceptions=(Exception,)):
    for attempt in range(attempts):
        try:
            return fn()
        except exceptions:
            if attempt == attempts - 1:
                raise
            time.sleep(base_delay * (2 ** attempt))


async def run_blocking(func, *args, **kwargs):
    return await asyncio.to_thread(lambda: retry(lambda: func(*args, **kwargs)))


async def run_telegram(func, *args, attempts=3, base_delay=0.5, exceptions=(Exception,), **kwargs):
    for attempt in range(attempts):
        try:
            return await func(*args, **kwargs)
        except exceptions:
            if attempt == attempts - 1:
                raise
            await asyncio.sleep(base_delay * (2 ** attempt))
