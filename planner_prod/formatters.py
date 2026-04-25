"""
Message formatting helpers.
All functions return HTML-ready strings for aiogram ParseMode.HTML.
"""

from datetime import date, time as dtime
from typing import Optional

from locales import t

PRIORITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}
STATUS_ICON    = {"pending": "○", "done": "✅", "skipped": "⏭", "cancelled": "🗑"}

# ── Date / time ──────────────────────────────────────────────────────────────

def fmt_date(d: date, lang: str) -> str:
    """Format a date as '24 апр' / '24 Apr'."""
    month = t(f"month_{d.month}", lang)
    return f"{d.day} {month}"


def fmt_weekday(d: date, lang: str) -> str:
    """Return localised weekday name."""
    return t(f"weekday_{d.weekday()}", lang)


def fmt_time(t_obj) -> str:
    """Format a time object or 'HH:MM' string nicely."""
    if t_obj is None:
        return ""
    if hasattr(t_obj, "strftime"):
        return t_obj.strftime("%H:%M")
    return str(t_obj)[:5]


# ── Task card ────────────────────────────────────────────────────────────────

def format_task_card(task: dict, lang: str) -> str:
    """Format a single task as a detailed card message."""
    priority_emoji = PRIORITY_EMOJI.get(task.get("priority", "medium"), "🟡")
    time_part = f"  🕐 {fmt_time(task.get('scheduled_time'))}" if task.get("scheduled_time") else ""
    d = task["scheduled_date"]
    date_str = fmt_date(d, lang) if isinstance(d, date) else str(d)

    cat_line = ""
    if task.get("category_name"):
        emoji = task.get("category_emoji", "📌")
        cat_line = f"📌 {emoji} {task['category_name']}\n"

    remind_line = ""
    rb = task.get("remind_before") or []
    if rb:
        parts = []
        for mins in sorted(rb):
            if mins < 60:
                parts.append(f"{mins}" + (" мин" if lang == "ru" else " min"))
            else:
                h = mins // 60
                parts.append(f"{h}" + (" ч" if lang == "ru" else " hr"))
        remind_line = "🔔 " + (", ".join(parts)) + "\n"

    rec_line = ""
    if task.get("recurrence"):
        rec_map = {
            "ru": {"daily": "каждый день", "weekly": "каждую неделю",
                   "monthly": "каждый месяц", "weekdays": "по будням"},
            "en": {"daily": "every day", "weekly": "every week",
                   "monthly": "every month", "weekdays": "weekdays"},
        }
        label = rec_map.get(lang, rec_map["en"]).get(task["recurrence"], task["recurrence"])
        rec_line = f"🔁 {label}\n"

    return t(
        "task_card", lang,
        priority_emoji=priority_emoji,
        title=task["title"],
        date=date_str,
        time_part=time_part,
        category_line=cat_line,
        remind_line=remind_line,
        recurrence_line=rec_line,
    )


# ── Schedule day ─────────────────────────────────────────────────────────────

def format_schedule_day(tasks: list[dict], target_date: date, lang: str) -> str:
    """
    Build the full schedule message for a given day.
    Tasks are grouped into Morning / Afternoon / Evening / All-day.
    """
    header = t(
        "schedule_header", lang,
        weekday=fmt_weekday(target_date, lang),
        date=fmt_date(target_date, lang),
    )

    if not tasks:
        return f"{header}\n\n{t('schedule_empty', lang)}"

    # Partition by time of day
    morning, afternoon, evening, all_day = [], [], [], []
    for task in tasks:
        st = task.get("scheduled_time")
        if st is None:
            all_day.append(task)
        else:
            h = st.hour if hasattr(st, "hour") else int(str(st)[:2])
            if h < 12:
                morning.append(task)
            elif h < 17:
                afternoon.append(task)
            else:
                evening.append(task)

    def render_group(header_key: str, group: list[dict]) -> str:
        if not group:
            return ""
        lines = [t(header_key, lang)]
        for task in group:
            icon  = STATUS_ICON.get(task["status"], "○")
            time  = f"<b>{fmt_time(task.get('scheduled_time'))}</b>  " if task.get("scheduled_time") else ""
            emoji = task.get("category_emoji") or "📌"
            pri   = " 🔴" if task.get("priority") == "high" else ""
            lines.append(f"  {icon} {time}{emoji} {task['title']}{pri}")
        return "\n".join(lines)

    parts = [header, ""]
    for key, group in [
        ("schedule_morning", morning),
        ("schedule_day",     afternoon),
        ("schedule_evening", evening),
        ("schedule_no_time", all_day),
    ]:
        chunk = render_group(key, group)
        if chunk:
            parts.append(chunk)
            parts.append("")

    done  = sum(1 for t_ in tasks if t_["status"] == "done")
    total = len(tasks)
    parts.append(t("schedule_footer", lang, done=done, total=total))

    return "\n".join(parts)


# ── Statistics ───────────────────────────────────────────────────────────────

PROGRESS_FILLED = "█"
PROGRESS_EMPTY  = "░"

def _bar(pct: int, width: int = 10) -> str:
    filled = round(pct / 100 * width)
    return PROGRESS_FILLED * filled + PROGRESS_EMPTY * (width - filled)


def format_stats(
    summary: dict,
    streak: int,
    by_category: list[dict],
    by_weekday: list[dict],
    period_days: int,
    best_dow: int | None,
    lang: str,
) -> str:
    period_label = {7: "7 " + ("дней" if lang == "ru" else "days"),
                    30: "30 " + ("дней" if lang == "ru" else "days"),
                    90: "90 " + ("дней" if lang == "ru" else "days")}.get(period_days, f"{period_days}d")

    lines = [
        t("stats_header", lang),
        t("stats_period", lang, period=period_label),
        "",
    ]

    if streak > 0:
        lines.append(t("stats_streak", lang, days=streak))
    else:
        lines.append(t("stats_streak_none", lang))

    lines.append(t("stats_completion", lang,
                   pct=summary["pct"], done=summary["done"], total=summary["total"]))

    if best_dow is not None:
        from locales import t as _t
        day_name = _t(f"weekday_{best_dow}", lang)
        best_pct = next((w["pct"] for w in by_weekday if w["dow"] == best_dow), 0)
        lines.append(t("stats_best_day", lang, day=day_name, pct=best_pct))

    if summary["total"] == 0:
        lines.append("")
        lines.append(t("stats_empty", lang))
        return "\n".join(lines)

    # By category
    if by_category:
        lines += ["", t("stats_by_category", lang)]
        for cat in by_category[:5]:
            bar = _bar(cat["pct"])
            lines.append(f"  {cat['emoji']} {cat['name']:<12} {bar}  {cat['pct']}%")

    # By weekday
    if by_weekday:
        lines += ["", t("stats_by_weekday", lang)]
        short_days_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        short_days_en = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        short_days = short_days_ru if lang == "ru" else short_days_en
        for wd in by_weekday:
            day_label = short_days[wd["dow"]]
            bar = _bar(wd["pct"], width=8)
            lines.append(f"  {day_label}  {bar}  {wd['pct']}%")

    return "\n".join(lines)


# ── Digest ───────────────────────────────────────────────────────────────────

def format_morning_digest(
    tasks: list[dict],
    streak: int,
    target_date: date,
    lang: str,
    is_premium: bool = False,
    ai_summary: str | None = None,
) -> str:
    weekday = fmt_weekday(target_date, lang)
    date_str = fmt_date(target_date, lang)

    if ai_summary and is_premium:
        return (
            f"🌅 <b>{'Доброе утро!' if lang == 'ru' else 'Good morning!'}</b>\n\n"
            f"📅 <b>{weekday}, {date_str}</b>\n\n"
            f"{ai_summary}\n\n"
            + (t("digest_streak", lang, days=streak) if streak > 0
               else t("digest_no_streak", lang))
        )

    if not tasks:
        return (
            f"🌅 <b>{'Доброе утро!' if lang == 'ru' else 'Good morning!'}</b>\n\n"
            f"📅 <b>{weekday}, {date_str}</b>\n\n"
            + t("digest_empty", lang)
        )

    # Top-3 tasks preview
    task_lines = []
    for task in tasks[:5]:
        time_str = fmt_time(task.get("scheduled_time"))
        prefix   = f"🕐 {time_str}  " if time_str else "  •  "
        pri      = " 🔴" if task.get("priority") == "high" else ""
        task_lines.append(f"{prefix}{task['title']}{pri}")

    if len(tasks) > 5:
        more = len(tasks) - 5
        task_lines.append(f"  + ещё {more}" if lang == "ru" else f"  + {more} more")

    streak_line = (t("digest_streak", lang, days=streak) if streak > 0
                   else t("digest_no_streak", lang))

    return t(
        "digest_morning", lang,
        weekday=weekday,
        date=date_str,
        total=len(tasks),
        task_lines="\n".join(task_lines),
        streak_line=streak_line,
    )


def format_evening_digest(
    done: int,
    total: int,
    streak: int,
    lang: str,
) -> str:
    pct = round(done / total * 100) if total > 0 else 0
    streak_line = (t("digest_streak", lang, days=streak) if streak > 0
                   else t("digest_no_streak", lang))
    return t(
        "digest_evening", lang,
        done=done,
        total=total,
        pct=pct,
        streak_line=streak_line,
    )
