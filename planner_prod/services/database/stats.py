from datetime import date, timedelta

from database.pool import get_pool


async def get_stats_summary(chat_id: int, days: int = 7) -> dict:
    """Return aggregated stats for the last N days."""
    pool = await get_pool()
    since = date.today() - timedelta(days=days)

    row = await pool.fetchrow(
        """
        SELECT
            COALESCE(SUM(tasks_total), 0)   AS total,
            COALESCE(SUM(tasks_done), 0)    AS done,
            COALESCE(SUM(tasks_skipped), 0) AS skipped
        FROM daily_stats
        WHERE chat_id = $1 AND stat_date >= $2
        """,
        chat_id, since,
    )

    total = row["total"] or 0
    done  = row["done"]  or 0
    pct   = round(done / total * 100) if total > 0 else 0

    return {"total": total, "done": done, "skipped": row["skipped"], "pct": pct}


async def get_streak(chat_id: int) -> int:
    """Return the current streak of productive days (>0 tasks done)."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT stat_date, tasks_done FROM daily_stats
        WHERE chat_id = $1
        ORDER BY stat_date DESC
        LIMIT 90
        """,
        chat_id,
    )
    if not rows:
        return 0

    streak = 0
    check_date = date.today()

    for row in rows:
        if row["stat_date"] == check_date and row["tasks_done"] > 0:
            streak += 1
            check_date -= timedelta(days=1)
        elif row["stat_date"] == check_date and row["tasks_done"] == 0:
            break
        else:
            # gap in dates
            break

    return streak


async def get_stats_by_category(chat_id: int, days: int = 7) -> list[dict]:
    pool = await get_pool()
    since = date.today() - timedelta(days=days)
    rows = await pool.fetch(
        """
        SELECT
            c.name, c.emoji,
            COUNT(t.id) FILTER (WHERE t.status != 'cancelled') AS total,
            COUNT(t.id) FILTER (WHERE t.status = 'done')       AS done
        FROM tasks t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE t.chat_id = $1 AND t.scheduled_date >= $2
        GROUP BY c.name, c.emoji
        ORDER BY total DESC
        """,
        chat_id, since,
    )
    result = []
    for r in rows:
        total = r["total"] or 0
        done  = r["done"]  or 0
        pct   = round(done / total * 100) if total > 0 else 0
        result.append({
            "name":  r["name"] or "—",
            "emoji": r["emoji"] or "📌",
            "total": total,
            "done":  done,
            "pct":   pct,
        })
    return result


async def get_stats_by_weekday(chat_id: int, days: int = 30) -> list[dict]:
    """Returns completion % per weekday (0=Mon … 6=Sun)."""
    pool = await get_pool()
    since = date.today() - timedelta(days=days)
    rows = await pool.fetch(
        """
        SELECT
            EXTRACT(DOW FROM stat_date)::INT  AS dow,
            SUM(tasks_total) AS total,
            SUM(tasks_done)  AS done
        FROM daily_stats
        WHERE chat_id = $1 AND stat_date >= $2
        GROUP BY dow
        ORDER BY dow
        """,
        chat_id, since,
    )
    # DOW: 0=Sun in Postgres, remap to 0=Mon
    result = {i: {"total": 0, "done": 0, "pct": 0} for i in range(7)}
    for r in rows:
        # Postgres DOW: 0=Sun → remap to Mon=0
        mon_based = (r["dow"] - 1) % 7
        total = r["total"] or 0
        done  = r["done"]  or 0
        result[mon_based] = {
            "total": total,
            "done":  done,
            "pct":   round(done / total * 100) if total > 0 else 0,
        }
    return [{"dow": k, **v} for k, v in sorted(result.items())]


async def get_best_weekday(chat_id: int, days: int = 30) -> int | None:
    """Return day-of-week index (0=Mon) with highest completion rate."""
    weekdays = await get_stats_by_weekday(chat_id, days)
    active = [w for w in weekdays if w["total"] > 0]
    if not active:
        return None
    return max(active, key=lambda x: x["pct"])["dow"]
