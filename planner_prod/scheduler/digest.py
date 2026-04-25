"""
Digest scheduler: runs every minute, checks which users need
a morning or evening digest right now.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import logger


def register_digest_jobs(scheduler: AsyncIOScheduler) -> None:
    """Register a single per-minute job that fans out digests."""
    scheduler.add_job(
        _send_due_morning_digests,
        trigger=CronTrigger(minute="*"),   # every minute
        id="morning_digest_fan",
        replace_existing=True,
        misfire_grace_time=60,
    )
    scheduler.add_job(
        _send_due_evening_digests,
        trigger=CronTrigger(minute="*"),
        id="evening_digest_fan",
        replace_existing=True,
        misfire_grace_time=60,
    )
    logger.info("Digest jobs registered")


async def _send_due_morning_digests() -> None:
    now = datetime.utcnow()
    await _dispatch_digests(now.hour, now.minute, kind="morning")


async def _send_due_evening_digests() -> None:
    now = datetime.utcnow()
    await _dispatch_digests(now.hour, now.minute, kind="evening")


async def _dispatch_digests(utc_hour: int, utc_minute: int, kind: str) -> None:
    from database.users import get_all_users_for_digest, get_all_users_for_evening
    from database.tasks import get_tasks_for_date
    from database.stats import get_streak
    from instance import bot
    from keyboards.schedule import CB_DAY_NAV
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from locales import t
    from formatters import format_morning_digest, format_evening_digest
    from services.ai_parser import generate_ai_digest
    from crypto import decrypt

    if kind == "morning":
        users = await get_all_users_for_digest(utc_hour, utc_minute)
    else:
        users = await get_all_users_for_evening(utc_hour, utc_minute)

    for user in users:
        chat_id    = user["chat_id"]
        lang       = user.get("language", "ru")
        user_tz    = user.get("timezone") or "UTC"
        is_premium = (user.get("plan") == "premium")

        # Decrypt timezone if needed
        try:
            user_tz = decrypt(user_tz)
        except Exception:
            pass

        try:
            tz         = ZoneInfo(user_tz)
            local_now  = datetime.now(tz)
            today      = local_now.date()

            tasks  = await get_tasks_for_date(chat_id, today)
            streak = await get_streak(chat_id)

            if kind == "morning":
                pending_tasks = [t_ for t_ in tasks if t_["status"] == "pending"]

                ai_summary = None
                if is_premium and pending_tasks:
                    ai_summary = await generate_ai_digest(
                        pending_tasks, "", lang, user_tz
                    )

                text = format_morning_digest(
                    pending_tasks, streak, today, lang, is_premium, ai_summary
                )
            else:
                done    = sum(1 for t_ in tasks if t_["status"] == "done")
                total   = len([t_ for t_ in tasks if t_["status"] != "cancelled"])
                text    = format_evening_digest(done, total, streak, lang)

            # Build "Open today" button
            builder = InlineKeyboardBuilder()
            builder.button(
                text=t("btn_open_today", lang),
                callback_data=f"{CB_DAY_NAV}{today.isoformat()}",
            )

            await bot.send_message(chat_id, text, reply_markup=builder.as_markup())
            logger.info("Sent %s digest to %s", kind, chat_id)

        except Exception as e:
            logger.error("Digest error for %s: %s", chat_id, e)
