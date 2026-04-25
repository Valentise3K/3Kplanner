"""
Subscription middleware.

Injects `is_premium` and `lang` into handler data on every update.
Premium-gated handlers can read data["is_premium"] directly.
"""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from database.users import get_user, is_premium as _check_premium, get_user_lang


class UserMiddleware(BaseMiddleware):
    """
    Runs before every handler.
    Adds to data:
        data["lang"]       – user language ("ru" / "en")
        data["is_premium"] – bool
        data["user"]       – full user row dict (or None if unknown)
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Extract chat_id from the event
        chat_id: int | None = None

        if hasattr(event, "message") and event.message:
            chat_id = event.message.chat.id
        elif hasattr(event, "callback_query") and event.callback_query:
            chat_id = event.callback_query.message.chat.id
        elif hasattr(event, "chat") and event.chat:
            chat_id = event.chat.id

        if chat_id:
            user = await get_user(chat_id)
            data["user"]       = user
            data["lang"]       = user["language"] if user else "ru"
            data["is_premium"] = await _check_premium(chat_id)
        else:
            data["user"]       = None
            data["lang"]       = "ru"
            data["is_premium"] = False

        return await handler(event, data)
