from datetime import date, datetime
from typing import Optional

from database.pool import get_pool


async def create_task(
    chat_id: int,
    title: str,
    scheduled_date: date,
    scheduled_time: Optional[str] = None,      # "HH:MM" or None
    priority: str = "medium",
    category_id: Optional[int] = None,
    remind_before: list[int] | None = None,
    recurrence: Optional[str] = None,
    description: Optional[str] = None,
    source: str = "manual",
    workspace_id: Optional[int] = None,
) -> int:
    """Insert a task and return its id."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO tasks (
            chat_id, title, description, category_id, priority,
            scheduled_date, scheduled_time,
            remind_before, recurrence, source, workspace_id
        )
        VALUES ($1,$2,$3,$4,$5,$6,$7::TEXT::TIME,$8,$9,$10,$11)
        RETURNING id
        """,
        chat_id, title, description, category_id, priority,
        scheduled_date, scheduled_time,
        remind_before or [], recurrence, source, workspace_id,
    )
    return row["id"]


async def get_tasks_for_date(chat_id: int, target_date: date) -> list[dict]:
    """Return all non-cancelled tasks for a given date, ordered by time."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT t.*, c.name as category_name, c.emoji as category_emoji
        FROM tasks t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE t.chat_id = $1
          AND t.scheduled_date = $2
          AND t.status != 'cancelled'
        ORDER BY t.scheduled_time ASC NULLS LAST, t.created_at ASC
        """,
        chat_id, target_date,
    )
    return [dict(r) for r in rows]


async def get_task(task_id: int) -> dict | None:
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        SELECT t.*, c.name as category_name, c.emoji as category_emoji
        FROM tasks t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE t.id = $1
        """,
        task_id,
    )
    return dict(row) if row else None


async def complete_task(task_id: int) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        UPDATE tasks
        SET status = 'done', completed_at = NOW(), updated_at = NOW()
        WHERE id = $1
        """,
        task_id,
    )
    await _update_daily_stats(task_id, "done")


async def skip_task(task_id: int) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE tasks SET status = 'skipped', updated_at = NOW() WHERE id = $1",
        task_id,
    )
    await _update_daily_stats(task_id, "skipped")


async def restore_task(task_id: int) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        UPDATE tasks
        SET status = 'pending', completed_at = NULL, updated_at = NOW()
        WHERE id = $1
        """,
        task_id,
    )


async def delete_task(task_id: int) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE tasks SET status = 'cancelled', updated_at = NOW() WHERE id = $1",
        task_id,
    )


async def update_task_title(task_id: int, title: str) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE tasks SET title = $2, updated_at = NOW() WHERE id = $1",
        task_id, title,
    )


async def update_task_time(task_id: int, scheduled_date: date, scheduled_time: Optional[str]) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        UPDATE tasks
        SET scheduled_date = $2, scheduled_time = $3::TEXT::TIME, updated_at = NOW()
        WHERE id = $1
        """,
        task_id, scheduled_date, scheduled_time,
    )


async def count_tasks_today(chat_id: int, target_date: date) -> int:
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        SELECT COUNT(*) as cnt FROM tasks
        WHERE chat_id = $1 AND scheduled_date = $2 AND status != 'cancelled'
        """,
        chat_id, target_date,
    )
    return row["cnt"]


async def get_pending_reminders() -> list[dict]:
    """Return reminders that should fire now (±1 minute)."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT r.*, t.title as task_title, t.chat_id
        FROM reminders r
        JOIN tasks t ON t.id = r.task_id
        WHERE r.status = 'pending'
          AND r.remind_at <= NOW() + INTERVAL '1 minute'
          AND r.remind_at >= NOW() - INTERVAL '1 minute'
          AND t.status = 'pending'
        """
    )
    return [dict(r) for r in rows]


async def _update_daily_stats(task_id: int, action: str) -> None:
    """Upsert daily_stats row when a task is completed or skipped."""
    pool = await get_pool()
    row = await pool.fetchrow("SELECT chat_id, scheduled_date FROM tasks WHERE id = $1", task_id)
    if not row:
        return
    chat_id, stat_date = row["chat_id"], row["scheduled_date"]

    # Ensure the row exists
    await pool.execute(
        """
        INSERT INTO daily_stats (chat_id, stat_date, tasks_total)
        SELECT $1, $2, COUNT(*)
        FROM tasks
        WHERE chat_id = $1 AND scheduled_date = $2 AND status != 'cancelled'
        ON CONFLICT (chat_id, stat_date) DO UPDATE
            SET tasks_total = EXCLUDED.tasks_total
        """,
        chat_id, stat_date,
    )

    if action == "done":
        await pool.execute(
            """
            UPDATE daily_stats
            SET tasks_done = tasks_done + 1
            WHERE chat_id = $1 AND stat_date = $2
            """,
            chat_id, stat_date,
        )
    elif action == "skipped":
        await pool.execute(
            """
            UPDATE daily_stats
            SET tasks_skipped = tasks_skipped + 1
            WHERE chat_id = $1 AND stat_date = $2
            """,
            chat_id, stat_date,
        )


async def sync_daily_stats(chat_id: int, stat_date: date) -> None:
    """Recalculate and upsert daily stats for a user/date."""
    pool = await get_pool()
    await pool.execute(
        """
        INSERT INTO daily_stats (chat_id, stat_date, tasks_total, tasks_done, tasks_skipped)
        SELECT
            $1,
            $2,
            COUNT(*) FILTER (WHERE status != 'cancelled'),
            COUNT(*) FILTER (WHERE status = 'done'),
            COUNT(*) FILTER (WHERE status = 'skipped')
        FROM tasks
        WHERE chat_id = $1 AND scheduled_date = $2
        ON CONFLICT (chat_id, stat_date) DO UPDATE SET
            tasks_total   = EXCLUDED.tasks_total,
            tasks_done    = EXCLUDED.tasks_done,
            tasks_skipped = EXCLUDED.tasks_skipped
        """,
        chat_id, stat_date,
    )
