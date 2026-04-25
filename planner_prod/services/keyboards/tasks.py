"""
Keyboards for task confirmation, editing and card actions.

New flow (v2):
  - NO mode selection keyboard (quick/step/voice buttons removed)
  - Confirm keyboard: Save | Remind before (only if time set) | Edit | Cancel
  - Edit keyboard: one message with a button per field
  - Remind-before keyboard: 10 min / 30 min / 1 hour / custom
"""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from locales import t

# ── Callback prefixes ────────────────────────────────────────────────────────

# Task confirmation
CB_TASK_CONFIRM   = "tc:save"          # save the parsed draft
CB_TASK_REMIND    = "tc:remind"        # open remind-before picker
CB_TASK_EDIT_OPEN = "tc:edit"          # open edit panel
CB_TASK_CANCEL    = "tc:cancel"        # discard draft

# Remind-before picker (on draft)
CB_REMIND_10      = "rb:10"
CB_REMIND_30      = "rb:30"
CB_REMIND_60      = "rb:60"
CB_REMIND_CUSTOM  = "rb:custom"
CB_REMIND_REMOVE  = "rb:remove"       # remove previously set reminder

# Edit field selection
CB_EDIT_DATE      = "edit:date"
CB_EDIT_TIME      = "edit:time"
CB_EDIT_TITLE     = "edit:title"
CB_EDIT_PRIORITY  = "edit:priority"
CB_EDIT_CATEGORY  = "edit:category"
CB_EDIT_BACK      = "edit:back"       # back to confirm card

# Date picker (inside edit)
CB_DATE_TODAY     = "edate:today"
CB_DATE_TOMORROW  = "edate:tomorrow"
CB_DATE_CUSTOM    = "edate:custom"

# Time picker (inside edit)
CB_TIME_MORNING   = "etime:09:00"
CB_TIME_NOON      = "etime:13:00"
CB_TIME_EVENING   = "etime:19:00"
CB_TIME_NONE      = "etime:none"
CB_TIME_CUSTOM    = "etime:custom"

# Priority picker (inside edit)
CB_PRI_HIGH       = "epri:high"
CB_PRI_MED        = "epri:medium"
CB_PRI_LOW        = "epri:low"

# Saved task card actions
CB_TASK_DONE      = "task_done:"
CB_TASK_SKIP      = "task_skip:"
CB_TASK_DELETE    = "task_del:"
CB_TASK_DEL_YES   = "task_del_yes:"
CB_TASK_RESTORE   = "task_restore:"
CB_TASK_EDIT      = "task_edit:"      # edit a saved task


# ── Draft confirmation ────────────────────────────────────────────────────────

def task_confirm_keyboard(lang: str, has_time: bool, remind_set: bool) -> InlineKeyboardMarkup:
    """
    Main confirmation keyboard shown after AI parsing.

    has_time   → show the 'Remind before' button (only makes sense with exact time)
    remind_set → if a reminder is already set, show 'Remove reminder' instead
    """
    builder = InlineKeyboardBuilder()

    builder.button(text=t("btn_save_task", lang), callback_data=CB_TASK_CONFIRM)

    if has_time:
        if remind_set:
            builder.button(
                text=t("btn_remove_remind", lang),
                callback_data=CB_REMIND_REMOVE,
            )
        else:
            builder.button(
                text=t("btn_set_remind", lang),
                callback_data=CB_TASK_REMIND,
            )

    builder.button(text=t("btn_edit_task", lang), callback_data=CB_TASK_EDIT_OPEN)
    builder.button(text=t("btn_cancel", lang),    callback_data=CB_TASK_CANCEL)

    # Layout: Save + Remind on first row (if remind shown), then Edit + Cancel
    if has_time:
        builder.adjust(2, 2)
    else:
        builder.adjust(1, 2)

    return builder.as_markup()


# ── Remind-before picker ──────────────────────────────────────────────────────

def remind_before_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Shown when user taps 'Remind before'. Only relevant when task has exact time."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_remind_10", lang),     callback_data=CB_REMIND_10)
    builder.button(text=t("btn_remind_30", lang),     callback_data=CB_REMIND_30)
    builder.button(text=t("btn_remind_60", lang),     callback_data=CB_REMIND_60)
    builder.button(text=t("btn_remind_custom", lang), callback_data=CB_REMIND_CUSTOM)
    builder.button(text=t("btn_back", lang),          callback_data=CB_EDIT_BACK)
    builder.adjust(2, 2, 1)
    return builder.as_markup()


# ── Edit panel ────────────────────────────────────────────────────────────────

def edit_panel_keyboard(lang: str, draft: dict) -> InlineKeyboardMarkup:
    """
    One message showing all editable fields as buttons.
    Each button shows the current value inline so user sees what they're changing.
    """
    from formatters import fmt_date, fmt_time
    from datetime import date as _date

    d = _date.fromisoformat(draft["scheduled_date"])
    date_label = fmt_date(d, lang)
    time_label = fmt_time(draft.get("scheduled_time")) or ("—" if lang == "en" else "—")

    PRI_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    pri_emoji  = PRI_EMOJI.get(draft.get("priority", "medium"), "🟡")
    pri_name_map = {
        "ru": {"high": "Высокий", "medium": "Средний", "low": "Низкий"},
        "en": {"high": "High",    "medium": "Medium",  "low": "Low"},
    }
    pri_label = pri_emoji + " " + pri_name_map.get(lang, pri_name_map["en"]).get(
        draft.get("priority", "medium"), "Medium"
    )

    cat_label = draft.get("category_name") or ("—" if lang == "en" else "—")
    if draft.get("category_emoji"):
        cat_label = draft["category_emoji"] + " " + cat_label

    builder = InlineKeyboardBuilder()
    builder.button(text=f"📅 {date_label}",    callback_data=CB_EDIT_DATE)
    builder.button(text=f"🕐 {time_label}",    callback_data=CB_EDIT_TIME)
    builder.button(text=f"✏️ " + t("btn_edit_title",    lang), callback_data=CB_EDIT_TITLE)
    builder.button(text=f"{pri_label}",        callback_data=CB_EDIT_PRIORITY)
    builder.button(text=f"📌 {cat_label}",     callback_data=CB_EDIT_CATEGORY)
    builder.button(text=t("btn_back", lang),   callback_data=CB_EDIT_BACK)
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


# ── Sub-pickers used inside edit ──────────────────────────────────────────────

def edit_date_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_today_date",    lang), callback_data=CB_DATE_TODAY)
    builder.button(text=t("btn_tomorrow_date", lang), callback_data=CB_DATE_TOMORROW)
    builder.button(text=t("btn_choose_date",   lang), callback_data=CB_DATE_CUSTOM)
    builder.button(text=t("btn_back",          lang), callback_data=CB_EDIT_BACK)
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def edit_time_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_morning",    lang), callback_data=CB_TIME_MORNING)
    builder.button(text=t("btn_noon",       lang), callback_data=CB_TIME_NOON)
    builder.button(text=t("btn_evening",    lang), callback_data=CB_TIME_EVENING)
    builder.button(text=t("btn_no_time",    lang), callback_data=CB_TIME_NONE)
    builder.button(text=t("btn_custom_time",lang), callback_data=CB_TIME_CUSTOM)
    builder.button(text=t("btn_back",       lang), callback_data=CB_EDIT_BACK)
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def edit_priority_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔴 " + t("btn_priority_high",   lang), callback_data=CB_PRI_HIGH)
    builder.button(text="🟡 " + t("btn_priority_medium", lang), callback_data=CB_PRI_MED)
    builder.button(text="🟢 " + t("btn_priority_low",    lang), callback_data=CB_PRI_LOW)
    builder.button(text=t("btn_back", lang),                    callback_data=CB_EDIT_BACK)
    builder.adjust(3, 1)
    return builder.as_markup()


def edit_category_keyboard(categories: list[dict], lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=f"{cat['emoji']} {cat['name']}",
            callback_data=f"ecat:{cat['id']}",
        )
    no_cat = "📌 " + ("Без категории" if lang == "ru" else "No category")
    builder.button(text=no_cat,            callback_data="ecat:none")
    builder.button(text=t("btn_back", lang), callback_data=CB_EDIT_BACK)
    builder.adjust(2)
    return builder.as_markup()


# ── Saved task card ───────────────────────────────────────────────────────────

def task_card_keyboard(task_id: int, lang: str, status: str = "pending") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if status == "pending":
        builder.button(text=t("btn_done",   lang), callback_data=f"{CB_TASK_DONE}{task_id}")
        builder.button(text=t("btn_skip",   lang), callback_data=f"{CB_TASK_SKIP}{task_id}")
        builder.button(text=t("btn_edit",   lang), callback_data=f"{CB_TASK_EDIT}{task_id}")
        builder.button(text=t("btn_delete", lang), callback_data=f"{CB_TASK_DELETE}{task_id}")
        builder.adjust(2, 2)
    else:
        builder.button(text=t("btn_delete", lang), callback_data=f"{CB_TASK_DELETE}{task_id}")
        builder.adjust(1)
    builder.button(text=t("btn_back", lang), callback_data="back_schedule")
    return builder.as_markup()


def task_delete_confirm_keyboard(task_id: int, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_confirm_delete", lang), callback_data=f"{CB_TASK_DEL_YES}{task_id}")
    builder.button(text=t("btn_cancel",         lang), callback_data=f"back_task:{task_id}")
    builder.adjust(2)
    return builder.as_markup()


def task_undo_keyboard(task_id: int, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="↩️ " + t("task_undo", lang), callback_data=f"{CB_TASK_RESTORE}{task_id}")
    return builder.as_markup()
