from datetime import datetime, timedelta
from typing import Optional

from database.pool import get_pool
from crypto import encrypt, decrypt
from config import logger


async def get_or_create_user(chat_id: int, username: str | None = None) -> dict:
    """Return user row, creating it with defaults if absent."""
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM users WHERE chat_id = $1", chat_id)
    if row:
        return dict(row)
    await pool.execute(
        """
        INSERT INTO users (chat_id, username)
        VALUES ($1, $2)
        ON CONFLICT (chat_id) DO NOTHING
        """,
        chat_id, username,
    )
    row = await pool.fetchrow("SELECT * FROM users WHERE chat_id = $1", chat_id)
    return dict(row)


async def get_user(chat_id: int) -> dict | None:
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM users WHERE chat_id = $1", chat_id)
    return dict(row) if row else None


async def get_user_lang(chat_id: int) -> str:
    pool = await get_pool()
    row = await pool.fetchrow("SELECT language FROM users WHERE chat_id = $1", chat_id)
    return row["language"] if row else "ru"


async def get_user_timezone(chat_id: int) -> str:
    pool = await get_pool()
    row = await pool.fetchrow("SELECT timezone FROM users WHERE chat_id = $1", chat_id)
    if row and row["timezone"]:
        try:
            return decrypt(row["timezone"])
        except Exception:
            return row["timezone"]
    return "UTC"


async def is_premium(chat_id: int) -> bool:
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT plan, plan_until FROM users WHERE chat_id = $1", chat_id
    )
    if not row or row["plan"] != "premium":
        return False
    if row["plan_until"] and row["plan_until"] < datetime.utcnow().replace(tzinfo=row["plan_until"].tzinfo):
        return False
    return True


async def save_user_location(chat_id: int, city: str, timezone: str) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        UPDATE users
        SET city = $2, timezone = $3, updated_at = NOW()
        WHERE chat_id = $1
        """,
        chat_id, encrypt(city), encrypt(timezone),
    )


async def save_user_language(chat_id: int, language: str) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE users SET language = $2, updated_at = NOW() WHERE chat_id = $1",
        chat_id, language,
    )


async def save_digest_time(chat_id: int, digest_time: str) -> None:
    """digest_time: 'HH:MM' string"""
    pool = await get_pool()
    await pool.execute(
        "UPDATE users SET digest_time = $2::TEXT::TIME, updated_at = NOW() WHERE chat_id = $1",
        chat_id, digest_time,
    )


async def toggle_evening_digest(chat_id: int) -> bool:
    """Flip evening_digest flag. Returns the new state."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT evening_digest FROM users WHERE chat_id = $1", chat_id
    )
    new_state = not row["evening_digest"]
    await pool.execute(
        "UPDATE users SET evening_digest = $2, updated_at = NOW() WHERE chat_id = $1",
        chat_id, new_state,
    )
    return new_state


async def mark_onboarding_done(chat_id: int) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE users SET onboarding_done = TRUE, updated_at = NOW() WHERE chat_id = $1",
        chat_id,
    )


async def activate_premium(chat_id: int, months: int) -> datetime:
    """Activate premium for N months. Returns the expiry datetime."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT plan_until FROM users WHERE chat_id = $1", chat_id
    )
    # Extend from current expiry or from now
    base = row["plan_until"] if (row and row["plan_until"]) else datetime.utcnow()
    if base < datetime.utcnow():
        base = datetime.utcnow()
    new_until = base + timedelta(days=30 * months)
    await pool.execute(
        """
        UPDATE users
        SET plan = 'premium', plan_until = $2, updated_at = NOW()
        WHERE chat_id = $1
        """,
        chat_id, new_until,
    )
    return new_until


async def get_all_users_for_digest(digest_hour: int, digest_minute: int) -> list[dict]:
    """Return users whose digest_time matches the given UTC hour:minute."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT chat_id, language, timezone, plan, plan_until
        FROM users
        WHERE onboarding_done = TRUE
          AND EXTRACT(HOUR   FROM digest_time) = $1
          AND EXTRACT(MINUTE FROM digest_time) = $2
        """,
        digest_hour, digest_minute,
    )
    return [dict(r) for r in rows]


async def get_all_users_for_evening(evening_hour: int, evening_minute: int) -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT chat_id, language, timezone, plan, plan_until
        FROM users
        WHERE onboarding_done = TRUE
          AND evening_digest = TRUE
          AND EXTRACT(HOUR   FROM evening_time) = $1
          AND EXTRACT(MINUTE FROM evening_time) = $2
        """,
        evening_hour, evening_minute,
    )
    return [dict(r) for r in rows]


async def create_default_categories(chat_id: int, lang: str) -> None:
    """Insert the 3 default categories for a new user."""
    defaults = {
        "ru": [("💼", "Работа"), ("🏠", "Личное"), ("🏃", "Здоровье")],
        "en": [("💼", "Work"),   ("🏠", "Personal"), ("🏃", "Health")],
    }
    cats = defaults.get(lang, defaults["ru"])
    pool = await get_pool()
    for emoji, name in cats:
        await pool.execute(
            """
            INSERT INTO categories (chat_id, name, emoji, is_default)
            VALUES ($1, $2, $3, TRUE)
            ON CONFLICT DO NOTHING
            """,
            chat_id, name, emoji,
        )
