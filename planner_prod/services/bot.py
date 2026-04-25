"""
PlannerBot — entry point.

Startup sequence:
  1. Init PostgreSQL pool + create all tables
  2. Register middlewares
  3. Start APScheduler (digest + cleanup + reminder jobs)
  4. Restore pending reminder jobs from DB
  5. Start polling
"""

import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import logger
from database import init_pool
from instance import bot, dp
from middlewares import ThrottlingMiddleware, UserMiddleware
from scheduler import (
    register_cleanup_job,
    register_digest_jobs,
    restore_reminder_jobs,
    set_scheduler,
)

import handlers  # noqa: F401 — registers all handlers via side-effects


async def main() -> None:
    logger.info("Starting PlannerBot...")

    # 1. Database
    await init_pool()

    # 2. Middlewares — order matters (throttling first, then user data)
    dp.update.outer_middleware(ThrottlingMiddleware(rate_limit=5, period=2))
    dp.update.outer_middleware(UserMiddleware())

    # 3. Scheduler
    scheduler = AsyncIOScheduler(timezone="UTC")
    set_scheduler(scheduler)
    register_digest_jobs(scheduler)
    register_cleanup_job(scheduler)
    scheduler.start()
    logger.info("Scheduler started")

    # 4. Restore reminder jobs that survived a restart
    await restore_reminder_jobs()

    # 5. Webhook server for YooKassa / Stripe (runs in background)
    from http_server import start_webhook_server
    await start_webhook_server()

    # 6. Start polling
    logger.info("Bot is running — listening for updates...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
