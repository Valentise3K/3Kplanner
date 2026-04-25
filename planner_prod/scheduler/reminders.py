"""
Reminder scheduler: schedules APScheduler jobs for task reminders
and fires them at the right time.
"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from config import logger
from database.reminders import get_pending_reminders, mark_reminder_fired

scheduler: AsyncIOScheduler | None = None   # set in bot.py


def set_scheduler(s: AsyncIOScheduler) -> None:
    global scheduler
    scheduler = s


async def schedule_task_reminders(
    task_id: int,
    chat_id: int,
    scheduled_date: date,
    scheduled_time: str,       # "HH:MM"
    remind_before: list[int],  # minutes before
    user_tz: str,
) -> None:
    """Create reminder rows and schedule APScheduler jobs."""
    from database.reminders import create_reminder

    tz    = ZoneInfo(user_tz)
    h, m  = map(int, scheduled_time.split(":"))
    task_dt = datetime(
        scheduled_date.year, scheduled_date.month, scheduled_date.day,
        h, m, tzinfo=tz,
    )

    for mins in remind_before:
        remind_at = task_dt - timedelta(minutes=mins)
        if remind_at <= datetime.now(tz):
            continue  # in the past

        reminder_id = await create_reminder(task_id, chat_id, remind_at)
        job_id      = f"reminder_{reminder_id}"

        if scheduler:
            scheduler.add_job(
                _fire_reminder,
                trigger=DateTrigger(run_date=remind_at),
                id=job_id,
                args=[reminder_id, chat_id],
                replace_existing=True,
                misfire_grace_time=120,
            )
            logger.info("Scheduled reminder %s at %s", job_id, remind_at)


async def _fire_reminder(reminder_id: int, chat_id: int) -> None:
    """Called by APScheduler when a reminder is due."""
    from instance import bot
    from database.reminders import get_pending_reminders
    from database.users import get_user_lang, get_user

    # Find this specific reminder
    from database.pool import get_pool
    pool  = await get_pool()
    row   = await pool.fetchrow(
        """
        SELECT r.id, r.task_id, t.title, t.scheduled_time, t.status
        FROM reminders r
        JOIN tasks t ON t.id = r.task_id
        WHERE r.id = $1 AND r.status = 'pending'
        """,
        reminder_id,
    )
    if not row:
        return
    if row["status"] != "pending":
        await mark_reminder_fired(reminder_id)
        return

    lang = await get_user_lang(chat_id)
    time_str = row["scheduled_time"].strftime("%H:%M") if row.get("scheduled_time") else ""

    text = (
        f"🔔 <b>Напоминание:</b> {row['title']}" + (f"\n🕐 {time_str}" if time_str else "")
        if lang == "ru" else
        f"🔔 <b>Reminder:</b> {row['title']}" + (f"\n🕐 {time_str}" if time_str else "")
    )

    from keyboards.tasks import task_card_keyboard
    try:
        await bot.send_message(
            chat_id,
            text,
            reply_markup=task_card_keyboard(row["task_id"], lang),
        )
    except Exception as e:
        logger.warning("Failed to send reminder %s: %s", reminder_id, e)

    await mark_reminder_fired(reminder_id)


async def restore_reminder_jobs() -> None:
    """On bot restart: re-schedule all pending reminders from the DB."""
    if not scheduler:
        return
    from database.pool import get_pool
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT r.id, r.chat_id, r.remind_at
        FROM reminders r
        WHERE r.status = 'pending' AND r.remind_at > NOW()
        ORDER BY r.remind_at ASC
        """
    )
    for row in rows:
        job_id = f"reminder_{row['id']}"
        scheduler.add_job(
            _fire_reminder,
            trigger=DateTrigger(run_date=row["remind_at"]),
            id=job_id,
            args=[row["id"], row["chat_id"]],
            replace_existing=True,
            misfire_grace_time=120,
        )
    logger.info("Restored %d reminder jobs", len(rows))
