"""
handlers/tasks.py — v2

Новый флоу ввода задач:
  1. Любое текстовое сообщение (или голосовое у Premium) → ИИ парсит
  2. ИИ возвращает is_task=True/False
  3. Если задача → показываем карточку подтверждения
  4. Кнопки: Сохранить | Напомнить заранее (только если есть время) | Изменить | Отмена
  5. «Напомнить заранее» → кнопки: 10 мин / 30 мин / 1 час / Своё
  6. «Изменить» → одно сообщение с кнопкой на каждое поле
  7. После сохранения remind_before устанавливается только если пользователь выбрал его явно

FSM states:
  - editing_*  → редактирование конкретного поля черновика
  - waiting_remind_custom  → ввод своего времени напоминания текстом
"""

import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, Voice

from config import FREE_TASKS_PER_DAY, logger
from database.categories import get_user_categories
from database.reminders import cancel_reminders_for_task, create_reminder
from database.tasks import (
    complete_task,
    count_tasks_today,
    create_task,
    delete_task,
    get_task,
    restore_task,
    skip_task,
)
from database.users import get_user_timezone
from formatters import fmt_date, fmt_time, format_task_card
from instance import bot, dp
from keyboards.main import main_keyboard, premium_upsell_keyboard
from keyboards.tasks import (
    CB_DATE_CUSTOM, CB_DATE_TODAY, CB_DATE_TOMORROW,
    CB_EDIT_BACK, CB_EDIT_CATEGORY, CB_EDIT_DATE,
    CB_EDIT_TIME, CB_EDIT_TITLE, CB_EDIT_PRIORITY,
    CB_PRI_HIGH, CB_PRI_LOW, CB_PRI_MED,
    CB_REMIND_10, CB_REMIND_30, CB_REMIND_60,
    CB_REMIND_CUSTOM, CB_REMIND_REMOVE,
    CB_TASK_CANCEL, CB_TASK_CONFIRM,
    CB_TASK_DEL_YES, CB_TASK_DELETE,
    CB_TASK_DONE, CB_TASK_EDIT_OPEN,
    CB_TASK_REMIND, CB_TASK_RESTORE, CB_TASK_SKIP,
    CB_TIME_CUSTOM, CB_TIME_MORNING, CB_TIME_NONE,
    CB_TIME_NOON, CB_TIME_EVENING,
    edit_category_keyboard, edit_date_keyboard,
    edit_panel_keyboard, edit_priority_keyboard,
    edit_time_keyboard, remind_before_keyboard,
    task_card_keyboard, task_confirm_keyboard,
    task_delete_confirm_keyboard, task_undo_keyboard,
)
from locales import t
from scheduler.reminders import schedule_task_reminders
from services.ai_parser import parse_message
from services.voice import transcribe_voice


# ── FSM states ────────────────────────────────────────────────────────────────

class TaskEditStates(StatesGroup):
    editing_date         = State()  # waiting for custom date input
    editing_time         = State()  # waiting for custom time input
    editing_title        = State()  # waiting for new title text
    waiting_remind_custom = State() # waiting for custom remind-before time


# ── Helpers ───────────────────────────────────────────────────────────────────

def _empty_draft(today: date) -> dict:
    return {
        "title":          "",
        "scheduled_date": today.isoformat(),
        "scheduled_time": None,
        "priority":       "medium",
        "remind_before":  None,      # None = not set by user
        "recurrence":     None,
        "category_id":    None,
        "category_name":  None,
        "category_emoji": None,
        "description":    None,
    }


def _parse_date(text: str) -> date | None:
    for fmt in ("%d.%m.%Y", "%d.%m", "%Y-%m-%d"):
        try:
            d = datetime.strptime(text.strip(), fmt)
            if fmt == "%d.%m":
                d = d.replace(year=date.today().year)
            return d.date()
        except ValueError:
            continue
    return None


def _parse_time_str(text: str) -> str | None:
    text = text.strip().replace(".", ":").replace("-", ":")
    try:
        return datetime.strptime(text, "%H:%M").strftime("%H:%M")
    except ValueError:
        return None


async def _resolve_category(category_hint: str | None, chat_id: int) -> tuple[int | None, str | None, str | None]:
    """Try to match category_hint from AI to user's actual categories. Returns (id, name, emoji)."""
    if not category_hint:
        return None, None, None
    cats = await get_user_categories(chat_id)
    hint_lower = category_hint.lower()
    # Map English hints to multilingual matching
    hint_map = {
        "work": ["work", "работа", "💼"],
        "personal": ["personal", "личное", "🏠", "home"],
        "health": ["health", "здоровье", "🏃", "sport"],
        "finance": ["finance", "финансы", "деньги"],
    }
    aliases = hint_map.get(hint_lower, [hint_lower])
    for cat in cats:
        if any(a in cat["name"].lower() or a == cat["emoji"] for a in aliases):
            return cat["id"], cat["name"], cat["emoji"]
    return None, None, None


def _build_confirm_text(draft: dict, lang: str) -> str:
    """Format the confirmation card message text."""
    d = date.fromisoformat(draft["scheduled_date"])
    date_str  = fmt_date(d, lang)
    time_str  = fmt_time(draft.get("scheduled_time"))

    PRI_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    pri_emoji = PRI_EMOJI.get(draft.get("priority", "medium"), "🟡")
    pri_name_map = {
        "ru": {"high": "Высокий", "medium": "Средний", "low": "Низкий"},
        "en": {"high": "High",    "medium": "Medium",  "low": "Low"},
    }
    pri_name  = pri_name_map.get(lang, pri_name_map["en"]).get(draft.get("priority", "medium"), "Medium")

    cat_line = ""
    if draft.get("category_name"):
        emoji    = draft.get("category_emoji") or "📌"
        cat_line = f"\n📌 {emoji} {draft['category_name']}"

    remind_line = ""
    rb = draft.get("remind_before")
    if rb is not None:
        if rb < 60:
            rb_str = f"{rb} " + ("мин" if lang == "ru" else "min")
        else:
            rb_str = f"{rb // 60} " + ("ч" if lang == "ru" else "hr")
        remind_line = "\n🔔 " + (f"За {rb_str}" if lang == "ru" else f"{rb_str} before")

    rec_line = ""
    if draft.get("recurrence"):
        rec_labels = {
            "ru": {"daily": "каждый день", "weekly": "каждую неделю",
                   "monthly": "каждый месяц", "weekdays": "по будням"},
            "en": {"daily": "every day",    "weekly": "every week",
                   "monthly": "every month","weekdays": "weekdays"},
        }
        label = rec_labels.get(lang, rec_labels["en"]).get(draft["recurrence"], draft["recurrence"])
        rec_line = f"\n🔁 {label}"

    header = "📋 <b>Проверь задачу:</b>" if lang == "ru" else "📋 <b>Check your task:</b>"

    return (
        f"{header}\n\n"
        f"<b>{draft['title']}</b>\n"
        f"📅 {date_str}"
        + (f"  🕐 {time_str}" if time_str else "")
        + f"\n{pri_emoji} {pri_name}"
        + cat_line
        + remind_line
        + rec_line
    )


async def _check_free_limit(chat_id: int, lang: str, is_premium: bool, message: Message) -> bool:
    if is_premium:
        return True
    today_count = await count_tasks_today(chat_id, date.today())
    if today_count >= FREE_TASKS_PER_DAY:
        await message.answer(
            ("⚠️ Лимит бесплатного плана: 10 задач в день.\n"
             "Получи Premium для безлимитного планирования!")
            if lang == "ru" else
            ("⚠️ Free plan limit: 10 tasks per day.\n"
             "Get Premium for unlimited tasks!"),
            reply_markup=premium_upsell_keyboard(lang),
        )
        return False
    return True


async def _refresh_confirm_card(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Re-render the confirmation card after any draft change."""
    data  = await state.get_data()
    draft = data.get("draft", {})
    text  = _build_confirm_text(draft, lang)
    kb    = task_confirm_keyboard(
        lang,
        has_time   = bool(draft.get("scheduled_time")),
        remind_set = draft.get("remind_before") is not None,
    )
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except TelegramBadRequest:
        pass  # message unchanged
    await call.answer()



# ── 'Добавить задачу' / 'Add Task' button ── hint ───────────────────────────

@dp.message(F.text.func(lambda x: bool(x) and ('Добавить задач' in x or 'Add Task' in x)))
async def btn_add_task_hint(message: Message, lang: str) -> None:
    hint = (
        '✏️ Просто напиши свою задачу прямо здесь!\n\n'
        '<i>Например: «Позвонить врачу завтра в 15:00» или «Купить молоко сегодня»</i>'
        if lang == 'ru' else
        '✏️ Just type your task right here!\n\n'
        '<i>E.g. «Call the doctor tomorrow at 3pm» or «Buy milk today»</i>'
    )
    await message.answer(hint)


# ── Universal message interceptor ────────────────────────────────────────────
# Catches ALL text messages that are not commands and not in an FSM state.
# Priority is LOW — specific handlers (schedule, stats, etc.) run first
# because they match on button text which is more specific.

@dp.message(F.text, ~F.text.startswith("/"))
async def universal_text_handler(message: Message, state: FSMContext, lang: str, is_premium: bool) -> None:
    """Intercept any text message and try to parse it as a task via AI."""
    # Only block when user is actively typing input for a specific field.
    # Do NOT block on ALL states — that makes the bot deaf if state gets stuck.
    current = await state.get_state()
    _input_states = {
        "TaskEditStates:editing_date",
        "TaskEditStates:editing_time",
        "TaskEditStates:editing_title",
        "TaskEditStates:waiting_remind_custom",
        "SettingsStates:entering_city",
        "SettingsStates:entering_digest",
        "OnboardingStates:entering_city",
        "HabitStates:entering_title",
        "HabitStates:entering_time",
    }
    if current in _input_states:
        return

    if not await _check_free_limit(message.chat.id, lang, is_premium, message):
        return

    tz     = await get_user_timezone(message.chat.id)
    status = await message.answer("⏳")

    try:
        draft_obj = await parse_message(message.text, tz)
    except Exception as e:
        logger.error("parse_message failed: %s", e)
        draft_obj = None

    try:
        await status.delete()
    except Exception:
        pass

    if draft_obj is None or not draft_obj.is_task:
        return  # not a task — silently ignore

    # Resolve category hint → actual category
    cat_id, cat_name, cat_emoji = await _resolve_category(
        draft_obj.category_hint, message.chat.id
    )

    draft = {
        "title":          draft_obj.title,
        "scheduled_date": draft_obj.scheduled_date.isoformat(),
        "scheduled_time": draft_obj.scheduled_time,
        "priority":       draft_obj.priority,
        "remind_before":  None,          # NOT set by AI — user must choose
        "recurrence":     draft_obj.recurrence,
        "category_id":    cat_id,
        "category_name":  cat_name,
        "category_emoji": cat_emoji,
        "description":    draft_obj.description,
    }

    await state.update_data(draft=draft)

    text = _build_confirm_text(draft, lang)
    kb   = task_confirm_keyboard(
        lang,
        has_time   = bool(draft["scheduled_time"]),
        remind_set = False,
    )
    await message.answer(text, reply_markup=kb)


# ── Voice message interceptor (Premium) ──────────────────────────────────────

@dp.message(F.voice)
async def universal_voice_handler(message: Message, state: FSMContext, lang: str, is_premium: bool) -> None:
    # Block only during active text-input FSM states
    current = await state.get_state()
    _input_states = {
        "TaskEditStates:editing_date",
        "TaskEditStates:editing_time",
        "TaskEditStates:editing_title",
        "TaskEditStates:waiting_remind_custom",
        "SettingsStates:entering_city",
        "OnboardingStates:entering_city",
        "HabitStates:entering_title",
    }
    if current in _input_states:
        return

    if not is_premium:
        await message.answer(
            t("voice_premium_upsell", lang),
            reply_markup=premium_upsell_keyboard(lang),
        )
        return

    if not await _check_free_limit(message.chat.id, lang, is_premium, message):
        return

    status = await message.answer("🎤 ⏳")
    voice: Voice = message.voice
    file_info  = await bot.get_file(voice.file_id)
    file_bytes = await bot.download_file(file_info.file_path)
    raw_bytes  = file_bytes.read()

    text = await transcribe_voice(raw_bytes, lang=lang)
    await status.delete()

    if not text:
        err = "🎤 Не удалось распознать голос. Попробуй ещё раз." if lang == "ru" \
              else "🎤 Could not transcribe voice. Please try again."
        await message.answer(err)
        return

    # Re-use the same AI parser flow
    tz        = await get_user_timezone(message.chat.id)
    draft_obj = await parse_message(text, tz)

    if draft_obj is None or not draft_obj.is_task:
        no_task = "🤔 Не понял задачу в голосовом сообщении." if lang == "ru" \
                  else "🤔 Couldn't detect a task in the voice message."
        await message.answer(no_task)
        return

    cat_id, cat_name, cat_emoji = await _resolve_category(
        draft_obj.category_hint, message.chat.id
    )

    draft = {
        "title":          draft_obj.title,
        "scheduled_date": draft_obj.scheduled_date.isoformat(),
        "scheduled_time": draft_obj.scheduled_time,
        "priority":       draft_obj.priority,
        "remind_before":  None,
        "recurrence":     draft_obj.recurrence,
        "category_id":    cat_id,
        "category_name":  cat_name,
        "category_emoji": cat_emoji,
        "description":    draft_obj.description,
    }

    await state.update_data(draft=draft)

    text_out = _build_confirm_text(draft, lang)
    kb       = task_confirm_keyboard(
        lang,
        has_time   = bool(draft["scheduled_time"]),
        remind_set = False,
    )
    await message.answer(text_out, reply_markup=kb)


# ── Confirm: Save ─────────────────────────────────────────────────────────────

@dp.callback_query(F.data == CB_TASK_CONFIRM)
async def cb_save_task(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    data  = await state.get_data()
    draft = data.get("draft")
    if not draft:
        await call.answer()
        return

    chat_id = call.message.chat.id
    tz      = await get_user_timezone(chat_id)

    scheduled_date = date.fromisoformat(draft["scheduled_date"])

    task_id = await create_task(
        chat_id        = chat_id,
        title          = draft["title"],
        scheduled_date = scheduled_date,
        scheduled_time = draft.get("scheduled_time"),
        priority       = draft.get("priority", "medium"),
        category_id    = draft.get("category_id"),
        remind_before  = [draft["remind_before"]] if draft.get("remind_before") else [],
        recurrence     = draft.get("recurrence"),
        description    = draft.get("description"),
        source         = "text",
    )

    # Schedule reminder only if user explicitly chose one
    rb = draft.get("remind_before")
    if rb is not None and draft.get("scheduled_time"):
        await schedule_task_reminders(
            task_id, chat_id, scheduled_date,
            draft["scheduled_time"], [rb], tz,
        )

    await state.clear()
    await call.message.edit_text(t("task_saved", lang))
    await call.answer()


# ── Confirm: Cancel ───────────────────────────────────────────────────────────

@dp.callback_query(F.data == CB_TASK_CANCEL)
async def cb_cancel_task(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await call.message.edit_text(t("action_cancelled", lang))
    await call.answer()


# ── Remind-before picker ──────────────────────────────────────────────────────

@dp.callback_query(F.data == CB_TASK_REMIND)
async def cb_open_remind(call: CallbackQuery, lang: str) -> None:
    await call.message.edit_reply_markup(reply_markup=remind_before_keyboard(lang))
    await call.answer()


@dp.callback_query(F.data.in_({CB_REMIND_10, CB_REMIND_30, CB_REMIND_60}))
async def cb_remind_preset(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    minutes = int(call.data.split(":")[1])
    data    = await state.get_data()
    draft   = data.get("draft", {})
    draft["remind_before"] = minutes
    await state.update_data(draft=draft)
    await _refresh_confirm_card(call, state, lang)


@dp.callback_query(F.data == CB_REMIND_CUSTOM)
async def cb_remind_custom_open(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(TaskEditStates.waiting_remind_custom)
    prompt = ("✍️ Введи за сколько минут напомнить (например: 20):"
              if lang == "ru" else
              "✍️ Enter how many minutes before to remind (e.g. 20):")
    await call.message.edit_text(prompt)
    await call.answer()


@dp.message(TaskEditStates.waiting_remind_custom)
async def process_remind_custom(message: Message, state: FSMContext, lang: str) -> None:
    try:
        minutes = int(message.text.strip())
        if minutes <= 0:
            raise ValueError
    except ValueError:
        err = "❌ Введи число минут, например: 15" if lang == "ru" else "❌ Enter a number of minutes, e.g. 15"
        await message.answer(err)
        return

    data  = await state.get_data()
    draft = data.get("draft", {})
    draft["remind_before"] = minutes
    await state.update_data(draft=draft)
    await state.set_state(None)

    text = _build_confirm_text(draft, lang)
    kb   = task_confirm_keyboard(lang, has_time=bool(draft.get("scheduled_time")), remind_set=True)
    await message.answer(text, reply_markup=kb)


@dp.callback_query(F.data == CB_REMIND_REMOVE)
async def cb_remind_remove(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    data  = await state.get_data()
    draft = data.get("draft", {})
    draft["remind_before"] = None
    await state.update_data(draft=draft)
    await _refresh_confirm_card(call, state, lang)


# ── Edit panel ────────────────────────────────────────────────────────────────

@dp.callback_query(F.data == CB_TASK_EDIT_OPEN)
async def cb_open_edit(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    data  = await state.get_data()
    draft = data.get("draft", {})
    header = "✏️ <b>Что изменить?</b>" if lang == "ru" else "✏️ <b>What to edit?</b>"
    await call.message.edit_text(header, reply_markup=edit_panel_keyboard(lang, draft))
    await call.answer()


@dp.callback_query(F.data == CB_EDIT_BACK)
async def cb_edit_back(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(None)
    await _refresh_confirm_card(call, state, lang)


# Edit: Date
@dp.callback_query(F.data == CB_EDIT_DATE)
async def cb_edit_date(call: CallbackQuery, lang: str) -> None:
    label = "📅 <b>Выбери дату:</b>" if lang == "ru" else "📅 <b>Choose date:</b>"
    await call.message.edit_text(label, reply_markup=edit_date_keyboard(lang))
    await call.answer()


@dp.callback_query(F.data.in_({CB_DATE_TODAY, CB_DATE_TOMORROW}))
async def cb_edit_date_preset(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    today = date.today()
    d = today if call.data == CB_DATE_TODAY else today + timedelta(days=1)
    data  = await state.get_data()
    draft = data.get("draft", {})
    draft["scheduled_date"] = d.isoformat()
    await state.update_data(draft=draft)
    await _refresh_confirm_card(call, state, lang)


@dp.callback_query(F.data == CB_DATE_CUSTOM)
async def cb_edit_date_custom(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(TaskEditStates.editing_date)
    prompt = "✍️ Введи дату: <b>ДД.ММ</b> или <b>ДД.ММ.ГГГГ</b>" if lang == "ru" \
             else "✍️ Enter date: <b>DD.MM</b> or <b>DD.MM.YYYY</b>"
    await call.message.edit_text(prompt)
    await call.answer()


@dp.message(TaskEditStates.editing_date)
async def process_edit_date(message: Message, state: FSMContext, lang: str) -> None:
    d = _parse_date(message.text)
    if not d:
        err = "❌ Неверный формат. Попробуй ещё раз:" if lang == "ru" else "❌ Invalid format. Try again:"
        await message.answer(err)
        return
    data  = await state.get_data()
    draft = data.get("draft", {})
    draft["scheduled_date"] = d.isoformat()
    await state.update_data(draft=draft)
    await state.set_state(None)
    text = _build_confirm_text(draft, lang)
    kb   = task_confirm_keyboard(lang, has_time=bool(draft.get("scheduled_time")),
                                  remind_set=draft.get("remind_before") is not None)
    await message.answer(text, reply_markup=kb)


# Edit: Time
@dp.callback_query(F.data == CB_EDIT_TIME)
async def cb_edit_time(call: CallbackQuery, lang: str) -> None:
    label = "🕐 <b>Выбери время:</b>" if lang == "ru" else "🕐 <b>Choose time:</b>"
    await call.message.edit_text(label, reply_markup=edit_time_keyboard(lang))
    await call.answer()


@dp.callback_query(F.data.in_({CB_TIME_MORNING, CB_TIME_NOON, CB_TIME_EVENING}))
async def cb_edit_time_preset(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    time_val = call.data.split(":", 1)[1]  # "09:00" etc
    data  = await state.get_data()
    draft = data.get("draft", {})
    draft["scheduled_time"] = time_val
    # Clear remind if user changes time
    draft["remind_before"]  = None
    await state.update_data(draft=draft)
    await _refresh_confirm_card(call, state, lang)


@dp.callback_query(F.data == CB_TIME_NONE)
async def cb_edit_time_none(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    data  = await state.get_data()
    draft = data.get("draft", {})
    draft["scheduled_time"] = None
    draft["remind_before"]  = None   # no time → no reminder
    await state.update_data(draft=draft)
    await _refresh_confirm_card(call, state, lang)


@dp.callback_query(F.data == CB_TIME_CUSTOM)
async def cb_edit_time_custom(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(TaskEditStates.editing_time)
    prompt = "✍️ Введи время <b>ЧЧ:ММ</b>, например: 14:30" if lang == "ru" \
             else "✍️ Enter time <b>HH:MM</b>, e.g. 14:30"
    await call.message.edit_text(prompt)
    await call.answer()


@dp.message(TaskEditStates.editing_time)
async def process_edit_time(message: Message, state: FSMContext, lang: str) -> None:
    parsed = _parse_time_str(message.text)
    if not parsed:
        err = "❌ Неверный формат. Попробуй: 14:30" if lang == "ru" else "❌ Invalid format. Try: 14:30"
        await message.answer(err)
        return
    data  = await state.get_data()
    draft = data.get("draft", {})
    draft["scheduled_time"] = parsed
    draft["remind_before"]  = None
    await state.update_data(draft=draft)
    await state.set_state(None)
    text = _build_confirm_text(draft, lang)
    kb   = task_confirm_keyboard(lang, has_time=True, remind_set=False)
    await message.answer(text, reply_markup=kb)


# Edit: Title
@dp.callback_query(F.data == CB_EDIT_TITLE)
async def cb_edit_title(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(TaskEditStates.editing_title)
    prompt = "✍️ Введи новое название задачи:" if lang == "ru" else "✍️ Enter new task title:"
    await call.message.edit_text(prompt)
    await call.answer()


@dp.message(TaskEditStates.editing_title)
async def process_edit_title(message: Message, state: FSMContext, lang: str) -> None:
    data  = await state.get_data()
    draft = data.get("draft", {})
    draft["title"] = message.text.strip()[:80]
    await state.update_data(draft=draft)
    await state.set_state(None)
    text = _build_confirm_text(draft, lang)
    kb   = task_confirm_keyboard(lang, has_time=bool(draft.get("scheduled_time")),
                                  remind_set=draft.get("remind_before") is not None)
    await message.answer(text, reply_markup=kb)


# Edit: Priority
@dp.callback_query(F.data == CB_EDIT_PRIORITY)
async def cb_edit_priority(call: CallbackQuery, lang: str) -> None:
    label = "🎯 <b>Выбери приоритет:</b>" if lang == "ru" else "🎯 <b>Choose priority:</b>"
    await call.message.edit_text(label, reply_markup=edit_priority_keyboard(lang))
    await call.answer()


@dp.callback_query(F.data.in_({CB_PRI_HIGH, CB_PRI_MED, CB_PRI_LOW}))
async def cb_edit_priority_set(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    pri   = call.data.split(":")[1]
    data  = await state.get_data()
    draft = data.get("draft", {})
    draft["priority"] = pri
    await state.update_data(draft=draft)
    await _refresh_confirm_card(call, state, lang)


# Edit: Category
@dp.callback_query(F.data == CB_EDIT_CATEGORY)
async def cb_edit_category(call: CallbackQuery, lang: str) -> None:
    cats  = await get_user_categories(call.message.chat.id)
    label = "📌 <b>Выбери категорию:</b>" if lang == "ru" else "📌 <b>Choose category:</b>"
    await call.message.edit_text(label, reply_markup=edit_category_keyboard(cats, lang))
    await call.answer()


@dp.callback_query(F.data.startswith("ecat:"))
async def cb_edit_category_set(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    val   = call.data.split(":")[1]
    data  = await state.get_data()
    draft = data.get("draft", {})

    if val == "none":
        draft["category_id"]    = None
        draft["category_name"]  = None
        draft["category_emoji"] = None
    else:
        cats = await get_user_categories(call.message.chat.id)
        cat  = next((c for c in cats if str(c["id"]) == val), None)
        if cat:
            draft["category_id"]    = cat["id"]
            draft["category_name"]  = cat["name"]
            draft["category_emoji"] = cat["emoji"]

    await state.update_data(draft=draft)
    await _refresh_confirm_card(call, state, lang)


# ── Saved task card callbacks ─────────────────────────────────────────────────

@dp.callback_query(F.data.startswith("open_task:"))
async def cb_open_task(call: CallbackQuery, lang: str) -> None:
    task_id = int(call.data.split(":")[1])
    task    = await get_task(task_id)
    if not task:
        await call.answer("Not found", show_alert=True)
        return
    await call.message.edit_text(
        format_task_card(task, lang),
        reply_markup=task_card_keyboard(task_id, lang, task["status"]),
    )
    await call.answer()


@dp.callback_query(F.data.startswith(CB_TASK_DONE))
async def cb_task_done(call: CallbackQuery, lang: str) -> None:
    task_id = int(call.data[len(CB_TASK_DONE):])
    await complete_task(task_id)
    await call.answer(t("task_done_msg", lang), show_alert=False)
    await call.message.edit_text(
        t("task_done_msg", lang),
        reply_markup=task_undo_keyboard(task_id, lang),
    )


@dp.callback_query(F.data.startswith(CB_TASK_SKIP))
async def cb_task_skip(call: CallbackQuery, lang: str) -> None:
    task_id = int(call.data[len(CB_TASK_SKIP):])
    await skip_task(task_id)
    await call.answer(t("task_skipped_msg", lang), show_alert=False)
    await call.message.edit_text(
        t("task_skipped_msg", lang),
        reply_markup=task_undo_keyboard(task_id, lang),
    )


@dp.callback_query(F.data.startswith(CB_TASK_RESTORE))
async def cb_task_restore(call: CallbackQuery, lang: str) -> None:
    task_id = int(call.data[len(CB_TASK_RESTORE):])
    await restore_task(task_id)
    task = await get_task(task_id)
    await call.message.edit_text(
        format_task_card(task, lang),
        reply_markup=task_card_keyboard(task_id, lang, "pending"),
    )
    await call.answer(t("task_restored", lang))


@dp.callback_query(F.data.startswith(CB_TASK_DELETE))
async def cb_task_delete(call: CallbackQuery, lang: str) -> None:
    task_id = int(call.data[len(CB_TASK_DELETE):])
    task    = await get_task(task_id)
    title   = task["title"] if task else "?"
    await call.message.edit_text(
        t("confirm_delete", lang, title=title),
        reply_markup=task_delete_confirm_keyboard(task_id, lang),
    )
    await call.answer()


@dp.callback_query(F.data.startswith(CB_TASK_DEL_YES))
async def cb_task_delete_confirm(call: CallbackQuery, lang: str) -> None:
    task_id = int(call.data[len(CB_TASK_DEL_YES):])
    await delete_task(task_id)
    await cancel_reminders_for_task(task_id)
    await call.message.edit_text(t("task_deleted_msg", lang))
    await call.answer()


@dp.callback_query(F.data.startswith("back_task:"))
async def cb_back_to_task(call: CallbackQuery, lang: str) -> None:
    task_id = int(call.data.split(":")[1])
    task    = await get_task(task_id)
    if task:
        await call.message.edit_text(
            format_task_card(task, lang),
            reply_markup=task_card_keyboard(task_id, lang, task["status"]),
        )
    await call.answer()
