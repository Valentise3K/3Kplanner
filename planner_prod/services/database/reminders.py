from datetime import datetime

from database.pool import get_pool


async def create_reminder(task_id: int, chat_id: int, remind_at: datetime) -> int:
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO reminders (task_id, chat_id, remind_at)
        VALUES ($1, $2, $3)
        RETURNING id
        """,
        task_id, chat_id, remind_at,
    )
    return row["id"]


async def cancel_reminders_for_task(task_id: int) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE reminders SET status = 'cancelled' WHERE task_id = $1 AND status = 'pending'",
        task_id,
    )


async def mark_reminder_fired(reminder_id: int) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE reminders SET status = 'fired', fired_at = NOW() WHERE id = $1",
        reminder_id,
    )


async def get_pending_reminders() -> list[dict]:
    """Fetch reminders due within the next minute."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT r.id, r.task_id, r.chat_id, r.remind_at,
               t.title AS task_title, t.scheduled_time
        FROM reminders r
        JOIN tasks t ON t.id = r.task_id
        WHERE r.status = 'pending'
          AND r.remind_at <= NOW() + INTERVAL '30 seconds'
          AND t.status = 'pending'
        ORDER BY r.remind_at ASC
        """
    )
    return [dict(r) for r in rows]


async def delete_old_reminders(days: int = 7) -> int:
    pool = await get_pool()
    result = await pool.execute(
        """
        DELETE FROM reminders
        WHERE status IN ('fired', 'cancelled')
          AND created_at < NOW() - INTERVAL '1 day' * $1
        """,
        days,
    )
    return int(result.split()[-1])
