"""Habit tracker handler — Premium feature."""

from datetime import date

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.habits import (
    archive_habit,
    create_habit,
    get_habit_streak,
    get_today_habit_log,
    get_user_habits,
    log_habit,
)
from instance import dp
from keyboards.main import premium_upsell_keyboard
from locales import t


class HabitStates(StatesGroup):
    entering_title = State()
    choosing_freq  = State()
    entering_time  = State()


HABIT_EMOJIS = ["⭐", "🏃", "📚", "💧", "🧘", "💪", "🎯", "🌱", "🎸", "✍️"]


def _habits_list_keyboard(habits: list[dict], today: date, lang: str):
    builder = InlineKeyboardBuilder()
    for habit in habits:
        # Check if logged today
        label = f"{habit['emoji']} {habit['title']}"
        builder.button(text=label, callback_data=f"habit_view:{habit['id']}")
    builder.button(
        text=t("btn_add_habit", lang),
        callback_data="habit_add",
    )
    builder.adjust(1)
    return builder.as_markup()


def _habit_card_keyboard(habit_id: int, logged: bool, lang: str):
    builder = InlineKeyboardBuilder()
    if not logged:
        label = "✅ " + ("Отметить" if lang == "ru" else "Mark done")
        builder.button(text=label, callback_data=f"habit_log:{habit_id}")
    else:
        done_label = "✅ " + ("Выполнено сегодня!" if lang == "ru" else "Done today!")
        builder.button(text=done_label, callback_data="noop")
    del_label = "🗑 " + ("Удалить привычку" if lang == "ru" else "Delete habit")
    builder.button(text=del_label, callback_data=f"habit_del:{habit_id}")
    back_label = t("btn_back", lang)
    builder.button(text=back_label, callback_data="habits_back")
    builder.adjust(1)
    return builder.as_markup()


def _freq_keyboard(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_habit_daily", lang),    callback_data="hfreq:daily")
    builder.button(text=t("btn_habit_weekdays", lang), callback_data="hfreq:weekdays")
    builder.button(text=t("btn_habit_weekly", lang),   callback_data="hfreq:weekly")
    builder.adjust(1)
    return builder.as_markup()


# ── Entry: "Habits" button ────────────────────────────────────────────────

@dp.message(F.text.func(lambda x: x and "🔥" in x))
async def btn_habits(message: Message, lang: str, is_premium: bool) -> None:
    if not is_premium:
        await message.answer(
            t("habits_premium_only", lang),
            reply_markup=premium_upsell_keyboard(lang),
        )
        return
    await _show_habits_menu(message.chat.id, lang, message)


async def _show_habits_menu(chat_id: int, lang: str, target) -> None:
    habits = await get_user_habits(chat_id)
    today  = date.today()

    if not habits:
        text = t("habits_menu", lang) + "\n\n" + t("no_habits", lang)
    else:
        lines = [t("habits_menu", lang), ""]
        for h in habits:
            streak = await get_habit_streak(h["id"])
            logged = await get_today_habit_log(h["id"], today)
            status = "✅" if logged else "○"
            lines.append(f"{status} {h['emoji']} <b>{h['title']}</b>  🔥{streak}")
        text = "\n".join(lines)

    kb = _habits_list_keyboard(habits, today, lang)
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=kb)
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb)


# ── View habit card ───────────────────────────────────────────────────────

@dp.callback_query(F.data.startswith("habit_view:"))
async def cb_habit_view(call: CallbackQuery, lang: str) -> None:
    habit_id = int(call.data.split(":", 1)[1])
    habits   = await get_user_habits(call.message.chat.id)
    habit    = next((h for h in habits if h["id"] == habit_id), None)
    if not habit:
        await call.answer()
        return

    streak = await get_habit_streak(habit_id)
    logged = await get_today_habit_log(habit_id, date.today())

    freq_map = {
        "ru": {"daily": "каждый день", "weekdays": "по будням", "weekly": "раз в неделю"},
        "en": {"daily": "every day",   "weekdays": "weekdays",  "weekly": "once a week"},
    }
    freq_label = freq_map.get(lang, freq_map["en"]).get(habit["frequency"], habit["frequency"])

    text = (
        f"{habit['emoji']} <b>{habit['title']}</b>\n\n"
        f"📅 {freq_label}\n"
        f"🔥 " + t("habit_streak", lang, days=streak) + "\n"
        + ("✅ Выполнено сегодня!" if logged and lang == "ru" else
           "✅ Done today!" if logged else "")
    )
    await call.message.edit_text(
        text,
        reply_markup=_habit_card_keyboard(habit_id, bool(logged), lang),
    )
    await call.answer()


# ── Log habit ─────────────────────────────────────────────────────────────

@dp.callback_query(F.data.startswith("habit_log:"))
async def cb_habit_log(call: CallbackQuery, lang: str) -> None:
    habit_id = int(call.data.split(":", 1)[1])
    await log_habit(habit_id, call.message.chat.id, date.today())
    streak = await get_habit_streak(habit_id)
    await call.answer(t("habit_done", lang) + f" 🔥{streak}", show_alert=True)
    # Refresh card
    habits = await get_user_habits(call.message.chat.id)
    habit  = next((h for h in habits if h["id"] == habit_id), None)
    if habit:
        freq_map = {
            "ru": {"daily": "каждый день", "weekdays": "по будням", "weekly": "раз в неделю"},
            "en": {"daily": "every day",   "weekdays": "weekdays",  "weekly": "once a week"},
        }
        freq_label = freq_map.get(lang, freq_map["en"]).get(habit["frequency"], habit["frequency"])
        text = (
            f"{habit['emoji']} <b>{habit['title']}</b>\n\n"
            f"📅 {freq_label}\n"
            f"🔥 " + t("habit_streak", lang, days=streak) + "\n"
            + ("✅ Выполнено сегодня!" if lang == "ru" else "✅ Done today!")
        )
        await call.message.edit_text(
            text,
            reply_markup=_habit_card_keyboard(habit_id, True, lang),
        )


# ── Add habit FSM ─────────────────────────────────────────────────────────

@dp.callback_query(F.data == "habit_add")
async def cb_habit_add(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(HabitStates.entering_title)
    await state.update_data(lang=lang)
    await call.message.edit_text(t("habit_ask_title", lang))
    await call.answer()


@dp.message(HabitStates.entering_title)
async def habit_title(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(title=message.text.strip()[:80])
    await state.set_state(HabitStates.choosing_freq)
    await message.answer(t("habit_ask_freq", lang), reply_markup=_freq_keyboard(lang))


@dp.callback_query(F.data.startswith("hfreq:"), HabitStates.choosing_freq)
async def habit_freq(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    freq = call.data.split(":", 1)[1]
    await state.update_data(frequency=freq)
    await state.set_state(HabitStates.entering_time)

    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_skip_remind", lang), callback_data="htime:skip")
    await call.message.edit_text(
        t("habit_ask_time", lang),
        reply_markup=builder.as_markup(),
    )
    await call.answer()


@dp.callback_query(F.data == "htime:skip", HabitStates.entering_time)
async def habit_time_skip(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    await _save_habit(call, state, lang, remind_time=None)
    await call.answer()


@dp.message(HabitStates.entering_time)
async def habit_time_text(message: Message, state: FSMContext, lang: str) -> None:
    from datetime import datetime
    try:
        datetime.strptime(message.text.strip(), "%H:%M")
        remind_time = message.text.strip()
    except ValueError:
        remind_time = None
    await _save_habit(message, state, lang, remind_time=remind_time)


async def _save_habit(target, state: FSMContext, lang: str, remind_time: str | None) -> None:
    data  = await state.get_data()
    chat_id = (target.message.chat.id if isinstance(target, CallbackQuery)
               else target.chat.id)

    habit_id = await create_habit(
        chat_id    = chat_id,
        title      = data["title"],
        emoji      = "⭐",
        frequency  = data.get("frequency", "daily"),
        remind_time= remind_time,
    )
    await state.clear()

    text = t("habit_saved", lang, title=data["title"])
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text)
    else:
        await target.answer(text)

    # Show updated list
    await _show_habits_menu(chat_id, lang, target if isinstance(target, Message) else target.message)


# ── Delete habit ──────────────────────────────────────────────────────────

@dp.callback_query(F.data.startswith("habit_del:"))
async def cb_habit_del(call: CallbackQuery, lang: str) -> None:
    habit_id = int(call.data.split(":", 1)[1])
    await archive_habit(habit_id, call.message.chat.id)
    await _show_habits_menu(call.message.chat.id, lang, call)


@dp.callback_query(F.data == "habits_back")
async def cb_habits_back(call: CallbackQuery, lang: str) -> None:
    await _show_habits_menu(call.message.chat.id, lang, call)


@dp.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery) -> None:
    await call.answer()
