"""Statistics handler with period selector."""

from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import FREE_STATS_DAYS
from database.stats import (
    get_best_weekday,
    get_stats_by_category,
    get_stats_by_weekday,
    get_stats_summary,
    get_streak,
)
from formatters import format_stats
from instance import dp
from keyboards.main import premium_upsell_keyboard
from locales import t


def _stats_period_keyboard(lang: str, current_days: int, is_premium: bool):
    builder = InlineKeyboardBuilder()
    for days, key in [(7, "btn_stats_7d"), (30, "btn_stats_30d"), (90, "btn_stats_90d")]:
        label = t(key, lang)
        if days == current_days:
            label = "✓ " + label
        builder.button(text=label, callback_data=f"stats_period:{days}")
    builder.adjust(3)
    if not is_premium:
        builder.button(text=t("stats_premium_hint", lang), callback_data="open_premium")
        builder.adjust(3, 1)
    return builder.as_markup()


async def _show_stats(chat_id: int, lang: str, is_premium: bool, days: int, target) -> None:
    # Cap free users at 7 days
    if not is_premium and days > FREE_STATS_DAYS:
        days = FREE_STATS_DAYS

    summary    = await get_stats_summary(chat_id, days)
    streak     = await get_streak(chat_id)
    by_cat     = await get_stats_by_category(chat_id, days)
    by_weekday = await get_stats_by_weekday(chat_id, min(days, 30))
    best_dow   = await get_best_weekday(chat_id, min(days, 30))

    text = format_stats(summary, streak, by_cat, by_weekday, days, best_dow, lang)
    kb   = _stats_period_keyboard(lang, days, is_premium)

    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=kb)
        except Exception:
            await target.message.answer(text, reply_markup=kb)
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb)


@dp.message(F.text.func(lambda x: x and "📊" in x))
async def btn_stats(message: Message, lang: str, is_premium: bool) -> None:
    await _show_stats(message.chat.id, lang, is_premium, 7, message)


@dp.callback_query(F.data.startswith("stats_period:"))
async def cb_stats_period(call: CallbackQuery, lang: str, is_premium: bool) -> None:
    days = int(call.data.split(":", 1)[1])
    if not is_premium and days > FREE_STATS_DAYS:
        await call.message.answer(
            t("stats_premium_hint", lang),
            reply_markup=premium_upsell_keyboard(lang),
        )
        await call.answer()
        return
    await _show_stats(call.message.chat.id, lang, is_premium, days, call)
