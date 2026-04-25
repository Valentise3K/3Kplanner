"""Cleanup job: removes old fired/cancelled reminders and syncs stats."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import logger


def register_cleanup_job(scheduler: AsyncIOScheduler) -> None:
    scheduler.add_job(
        _run_cleanup,
        trigger=CronTrigger(hour=3, minute=0),  # 03:00 UTC daily
        id="daily_cleanup",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("Cleanup job registered")


async def _run_cleanup() -> None:
    from database.reminders import delete_old_reminders
    deleted = await delete_old_reminders(days=7)
    logger.info("Cleanup: deleted %d old reminders", deleted)
