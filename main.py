import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN, LOG_LEVEL
from handlers import router

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

BOT_COMMANDS = [
    BotCommand(command="start", description="Запустить бота"),
    BotCommand(command="new", description="Создать новую заявку"),
    BotCommand(command="cancel", description="Отменить текущую заявку"),
    BotCommand(command="chat_info", description="Показать ID чата и темы"),
]


async def setup_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(BOT_COMMANDS)


async def main() -> None:
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    async with Bot(token=BOT_TOKEN) as bot:
        await setup_bot_commands(bot)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
