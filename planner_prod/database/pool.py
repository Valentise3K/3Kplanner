import asyncpg

from config import logger, settings

pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    global pool
    pool = await asyncpg.create_pool(
        dsn=settings.DATABASE_URL,
        min_size=2,
        max_size=10,
    )
    await _create_tables()
    logger.info("PostgreSQL pool ready")


async def get_pool() -> asyncpg.Pool:
    if pool is None:
        raise RuntimeError("Database pool not initialised. Call init_pool() first.")
    return pool


async def _create_tables() -> None:
    async with pool.acquire() as conn:
        # ── Users ────────────────────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id           BIGINT PRIMARY KEY,
                username          TEXT,
                timezone          TEXT    NOT NULL DEFAULT 'UTC',
                city              TEXT,
                language          TEXT    NOT NULL DEFAULT 'ru',
                plan              TEXT    NOT NULL DEFAULT 'free',
                plan_until        TIMESTAMPTZ,
                digest_time       TIME    NOT NULL DEFAULT '08:00',
                evening_digest    BOOLEAN NOT NULL DEFAULT TRUE,
                evening_time      TIME    NOT NULL DEFAULT '21:00',
                onboarding_done   BOOLEAN NOT NULL DEFAULT FALSE,
                created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # ── Categories ───────────────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id          BIGSERIAL   PRIMARY KEY,
                chat_id     BIGINT      REFERENCES users ON DELETE CASCADE,
                name        TEXT        NOT NULL,
                emoji       TEXT        NOT NULL DEFAULT '📌',
                is_default  BOOLEAN     NOT NULL DEFAULT FALSE,
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # ── Tasks ────────────────────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id                  BIGSERIAL   PRIMARY KEY,
                chat_id             BIGINT      REFERENCES users ON DELETE CASCADE,
                workspace_id        INTEGER,
                title               TEXT        NOT NULL,
                description         TEXT,
                category_id         INTEGER     REFERENCES categories,
                priority            TEXT        NOT NULL DEFAULT 'medium',
                status              TEXT        NOT NULL DEFAULT 'pending',
                scheduled_date      DATE        NOT NULL,
                scheduled_time      TIME,
                duration_minutes    INTEGER,
                recurrence          TEXT,
                recurrence_end_date DATE,
                remind_before       INTEGER[]   NOT NULL DEFAULT '{}',
                completed_at        TIMESTAMPTZ,
                source              TEXT        NOT NULL DEFAULT 'manual',
                created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_chat_date "
            "ON tasks(chat_id, scheduled_date)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)"
        )

        # ── Reminders ────────────────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id          BIGSERIAL   PRIMARY KEY,
                task_id     INTEGER     REFERENCES tasks ON DELETE CASCADE,
                chat_id     BIGINT      REFERENCES users ON DELETE CASCADE,
                remind_at   TIMESTAMPTZ NOT NULL,
                status      TEXT        NOT NULL DEFAULT 'pending',
                fired_at    TIMESTAMPTZ,
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_reminders_status   ON reminders(status)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_reminders_chat_id  ON reminders(chat_id)"
        )

        # ── Workspaces ───────────────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                id          BIGSERIAL   PRIMARY KEY,
                name        TEXT        NOT NULL,
                emoji       TEXT        DEFAULT '👥',
                owner_id    BIGINT      REFERENCES users ON DELETE CASCADE,
                invite_code TEXT        UNIQUE,
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS workspace_members (
                workspace_id  INTEGER     REFERENCES workspaces ON DELETE CASCADE,
                chat_id       BIGINT      REFERENCES users ON DELETE CASCADE,
                role          TEXT        NOT NULL DEFAULT 'member',
                joined_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (workspace_id, chat_id)
            )
        """)

        # ── Daily stats ──────────────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                chat_id         BIGINT  REFERENCES users ON DELETE CASCADE,
                stat_date       DATE    NOT NULL,
                tasks_total     INTEGER NOT NULL DEFAULT 0,
                tasks_done      INTEGER NOT NULL DEFAULT 0,
                tasks_skipped   INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (chat_id, stat_date)
            )
        """)

        # ── Habits (Premium) ─────────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id          BIGSERIAL   PRIMARY KEY,
                chat_id     BIGINT      REFERENCES users ON DELETE CASCADE,
                title       TEXT        NOT NULL,
                emoji       TEXT        NOT NULL DEFAULT '⭐',
                category_id INTEGER     REFERENCES categories,
                frequency   TEXT        NOT NULL DEFAULT 'daily',
                remind_time TIME,
                is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS habit_logs (
                id          BIGSERIAL   PRIMARY KEY,
                habit_id    INTEGER     REFERENCES habits ON DELETE CASCADE,
                chat_id     BIGINT      REFERENCES users ON DELETE CASCADE,
                log_date    DATE        NOT NULL,
                status      TEXT        NOT NULL DEFAULT 'done',
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (habit_id, log_date)
            )
        """)

        # ── Payments ─────────────────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id              BIGSERIAL   PRIMARY KEY,
                chat_id         BIGINT      REFERENCES users,
                provider        TEXT        NOT NULL,
                provider_id     TEXT,
                plan            TEXT        NOT NULL,
                amount          NUMERIC(10,2),
                currency        TEXT,
                status          TEXT        NOT NULL DEFAULT 'pending',
                period_months   INTEGER     NOT NULL DEFAULT 1,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

    logger.info("All tables created / verified")
