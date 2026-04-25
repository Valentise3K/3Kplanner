"""
Schedule view handler — shows tasks for a specific day with navigation.
"""

from datetime import date

from aiogram import F
from aiogram.types import CallbackQuery, Message

from database.tasks import get_tasks_for_date
from formatters import format_schedule_day
from instance import dp
from keyboards.schedule import CB_DAY_NAV, tasks_list_keyboard
from locales import t


async def _show_schedule(chat_id: int, target_date: date, lang: str, message_or_call) -> None:
    tasks = await get_tasks_for_date(chat_id, target_date)
    text  = format_schedule_day(tasks, target_date, lang)
    kb    = tasks_list_keyboard(tasks, target_date, lang)

    if isinstance(message_or_call, CallbackQuery):
        try:
            await message_or_call.message.edit_text(text, reply_markup=kb)
        except Exception:
            await message_or_call.message.answer(text, reply_markup=kb)
        await message_or_call.answer()
    else:
        await message_or_call.answer(text, reply_markup=kb)


# ── "Today" button / command ─────────────────────────────────────────────────

@dp.message(F.text.func(lambda x: bool(x) and ("Сегодня" in x or "Today" in x) and "Расписание" not in x and "Schedule" not in x))
async def btn_today(message: Message, lang: str) -> None:
    await _show_schedule(message.chat.id, date.today(), lang, message)


# ── "Schedule" button ────────────────────────────────────────────────────────

@dp.message(F.text.func(lambda x: bool(x) and ("Расписание" in x or "Schedule" in x)))
async def btn_schedule(message: Message, lang: str) -> None:
    await _show_schedule(message.chat.id, date.today(), lang, message)


# ── Day navigation ───────────────────────────────────────────────────────────

@dp.callback_query(F.data.startswith(CB_DAY_NAV))
async def cb_day_nav(call: CallbackQuery, lang: str) -> None:
    date_str    = call.data[len(CB_DAY_NAV):]
    target_date = date.fromisoformat(date_str)
    await _show_schedule(call.message.chat.id, target_date, lang, call)


# ── Back to schedule from task card ─────────────────────────────────────────

@dp.callback_query(F.data == "back_schedule")
async def cb_back_schedule(call: CallbackQuery, lang: str) -> None:
    await _show_schedule(call.message.chat.id, date.today(), lang, call)
