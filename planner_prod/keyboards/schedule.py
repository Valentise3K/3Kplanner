from datetime import date, timedelta

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from locales import t

CB_DAY_NAV   = "day:"        # day:2024-04-24
CB_TASK_OPEN = "open_task:"  # open_task:42


def schedule_nav_keyboard(current_date: date, lang: str) -> InlineKeyboardMarkup:
    """Previous / Today / Next day navigation."""
    prev_date = current_date - timedelta(days=1)
    next_date = current_date + timedelta(days=1)
    today     = date.today()

    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("btn_prev_day", lang),
        callback_data=f"{CB_DAY_NAV}{prev_date.isoformat()}",
    )
    if current_date != today:
        builder.button(
            text=t("btn_back_today", lang),
            callback_data=f"{CB_DAY_NAV}{today.isoformat()}",
        )
    builder.button(
        text=t("btn_next_day", lang),
        callback_data=f"{CB_DAY_NAV}{next_date.isoformat()}",
    )

    cols = 3 if current_date != today else 2
    builder.adjust(cols)
    return builder.as_markup()


def tasks_list_keyboard(
    tasks: list[dict],
    current_date: date,
    lang: str,
) -> InlineKeyboardMarkup:
    """Full schedule keyboard: task buttons + day navigation."""
    builder = InlineKeyboardBuilder()

    STATUS_ICON = {"pending": "○", "done": "✅", "skipped": "⏭"}

    for task in tasks:
        icon  = STATUS_ICON.get(task["status"], "○")
        time  = task["scheduled_time"].strftime("%H:%M") if task.get("scheduled_time") else ""
        emoji = task.get("category_emoji") or "📌"
        label = f"{icon} {time + '  ' if time else ''}{emoji} {task['title']}"
        # Truncate long titles for button
        if len(label) > 60:
            label = label[:57] + "…"
        builder.button(
            text=label,
            callback_data=f"{CB_TASK_OPEN}{task['id']}",
        )

    builder.adjust(1)

    # Navigation row
    prev_date = current_date - timedelta(days=1)
    next_date = current_date + timedelta(days=1)
    today     = date.today()

    nav_row: list = [
        InlineKeyboardBuilder().button(
            text=t("btn_prev_day", lang),
            callback_data=f"{CB_DAY_NAV}{prev_date.isoformat()}",
        )
    ]

    # We rebuild with separate builder for nav to control layout
    nav_builder = InlineKeyboardBuilder()
    nav_builder.button(
        text=t("btn_prev_day", lang),
        callback_data=f"{CB_DAY_NAV}{prev_date.isoformat()}",
    )
    if current_date != today:
        nav_builder.button(
            text=t("btn_back_today", lang),
            callback_data=f"{CB_DAY_NAV}{today.isoformat()}",
        )
    nav_builder.button(
        text=t("btn_next_day", lang),
        callback_data=f"{CB_DAY_NAV}{next_date.isoformat()}",
    )

    nav_cols = 3 if current_date != today else 2
    nav_builder.adjust(nav_cols)

    builder.attach(nav_builder)
    return builder.as_markup()
