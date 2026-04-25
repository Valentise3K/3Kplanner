from datetime import date

from database.pool import get_pool


async def create_habit(
    chat_id: int,
    title: str,
    emoji: str = "⭐",
    frequency: str = "daily",
    remind_time: str | None = None,
    category_id: int | None = None,
) -> int:
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO habits (chat_id, title, emoji, frequency, remind_time, category_id)
        VALUES ($1,$2,$3,$4,$5::TEXT::TIME,$6)
        RETURNING id
        """,
        chat_id, title, emoji, frequency, remind_time, category_id,
    )
    return row["id"]


async def get_user_habits(chat_id: int) -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT * FROM habits WHERE chat_id = $1 AND is_active = TRUE ORDER BY id ASC",
        chat_id,
    )
    return [dict(r) for r in rows]


async def log_habit(habit_id: int, chat_id: int, log_date: date, status: str = "done") -> None:
    pool = await get_pool()
    await pool.execute(
        """
        INSERT INTO habit_logs (habit_id, chat_id, log_date, status)
        VALUES ($1,$2,$3,$4)
        ON CONFLICT (habit_id, log_date)
        DO UPDATE SET status = EXCLUDED.status
        """,
        habit_id, chat_id, log_date, status,
    )


async def get_habit_streak(habit_id: int) -> int:
    """Return consecutive completed days ending today."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT log_date FROM habit_logs
        WHERE habit_id = $1 AND status = 'done'
        ORDER BY log_date DESC
        LIMIT 365
        """,
        habit_id,
    )
    if not rows:
        return 0

    from datetime import timedelta
    streak = 0
    check = date.today()
    for row in rows:
        if row["log_date"] == check:
            streak += 1
            check -= timedelta(days=1)
        else:
            break
    return streak


async def get_today_habit_log(habit_id: int, today: date) -> dict | None:
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM habit_logs WHERE habit_id = $1 AND log_date = $2",
        habit_id, today,
    )
    return dict(row) if row else None


async def archive_habit(habit_id: int, chat_id: int) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE habits SET is_active = FALSE WHERE id = $1 AND chat_id = $2",
        habit_id, chat_id,
    )
