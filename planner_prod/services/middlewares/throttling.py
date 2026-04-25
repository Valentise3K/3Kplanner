"""Simple per-user rate limiter using Redis."""

import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from redis.asyncio import Redis

from config import settings

_redis: Redis | None = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


class ThrottlingMiddleware(BaseMiddleware):
    """
    Limits each user to `rate_limit` messages per `period` seconds.
    Silently drops excess messages.
    """

    def __init__(self, rate_limit: int = 3, period: int = 2):
        self.rate_limit = rate_limit
        self.period = period

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        message: Message | None = None
        if hasattr(event, "message") and event.message:
            message = event.message

        if message and message.from_user:
            uid = message.from_user.id
            redis = get_redis()
            key = f"throttle:{uid}"
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, self.period)
            if count > self.rate_limit:
                return  # drop silently

        return await handler(event, data)
