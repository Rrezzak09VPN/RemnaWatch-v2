from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from src.config import settings


class AdminOnlyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
        if user and user.id in settings.admin_ids:
            return await handler(event, data)
        if isinstance(event, Message):
            await event.answer("⛔ Access denied")
        elif isinstance(event, CallbackQuery):
            await event.answer("Access denied", show_alert=True)
        return None
