import logging

from aiogram import Router
from aiogram.types.error_event import ErrorEvent

from handlers_actions import router as actions_router
from handlers_create import router as create_router
from handlers_edit import router as edit_router
from handlers_misc import router as misc_router

router = Router()
logger = logging.getLogger(__name__)

router.include_router(misc_router)
router.include_router(create_router)
router.include_router(actions_router)
router.include_router(edit_router)


@router.errors()
async def on_router_error(event: ErrorEvent) -> bool:
    logger.exception("unhandled_router_error", exc_info=event.exception)

    if event.update.message:
        await event.update.message.answer("⚠️ Произошла ошибка, попробуйте позже.")
        return True

    if event.update.callback_query:
        await event.update.callback_query.answer("⚠️ Произошла ошибка, попробуйте позже.", show_alert=True)
        return True

    return True
