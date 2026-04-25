"""
/start handler + onboarding FSM.
Flow: language → city → digest time → main menu
"""

from aiogram import F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import logger
from database.users import (
    create_default_categories,
    get_or_create_user,
    mark_onboarding_done,
    save_digest_time,
    save_user_language,
    save_user_location,
)
from geocoding import resolve_timezone
from instance import dp
from keyboards.main import (
    back_keyboard,
    digest_time_keyboard,
    language_keyboard,
    main_keyboard,
)
from locales import t


class OnboardingStates(StatesGroup):
    choosing_language = State()
    entering_city     = State()
    choosing_digest   = State()


# ── /start ──────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, user: dict | None) -> None:
    # Always ensure user row exists
    db_user = await get_or_create_user(
        message.chat.id, message.from_user.username
    )

    if db_user.get("onboarding_done"):
        lang = db_user.get("language", "ru")
        await state.clear()  # always reset any stale FSM state
        await message.answer(
            t("main_menu", lang),
            reply_markup=main_keyboard(lang),
        )
        return

    # New user → pick language first
    await state.set_state(OnboardingStates.choosing_language)
    await message.answer(
        t("choose_language", "ru"),   # shown in both langs always
        reply_markup=language_keyboard(),
    )


# ── Language selection ───────────────────────────────────────────────────────

@dp.callback_query(F.data.startswith("lang:"), OnboardingStates.choosing_language)
async def cb_language_onboarding(call: CallbackQuery, state: FSMContext) -> None:
    lang = call.data.split(":", 1)[1]  # "ru" or "en"

    await save_user_language(call.message.chat.id, lang)
    await state.update_data(lang=lang)
    await state.set_state(OnboardingStates.entering_city)

    await call.message.edit_text(t("lang_set", lang))
    await call.message.answer(
        t("welcome_new", lang),
    )
    await call.message.answer(
        t("ask_city", lang),
        reply_markup=back_keyboard(lang, "back_to_lang"),
    )
    await call.answer()


# Also handle language change from settings (no FSM state guard needed — handled in settings.py)
@dp.callback_query(F.data.startswith("lang:"))
async def cb_language_change(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    new_lang = call.data.split(":", 1)[1]
    await save_user_language(call.message.chat.id, new_lang)
    await call.message.edit_text(t("lang_set", new_lang))
    await call.message.answer(
        t("main_menu", new_lang),
        reply_markup=main_keyboard(new_lang),
    )
    await call.answer()


# ── City entry ───────────────────────────────────────────────────────────────

@dp.message(OnboardingStates.entering_city)
async def process_city(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    city = message.text.strip()

    timezone = await resolve_timezone(city)
    if not timezone:
        await message.answer(t("city_not_found", lang))
        return

    await save_user_location(message.chat.id, city, timezone)
    await state.update_data(city=city, timezone=timezone)

    await message.answer(t("city_found", lang, city=city, timezone=timezone))
    await state.set_state(OnboardingStates.choosing_digest)
    await message.answer(
        t("ask_digest_time", lang),
        reply_markup=digest_time_keyboard(lang),
    )


# ── Digest time selection ────────────────────────────────────────────────────

@dp.callback_query(F.data.startswith("digest:"), OnboardingStates.choosing_digest)
async def cb_digest_time(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    time_str = call.data.split(":", 1)[1]   # e.g. "08:00"

    await save_digest_time(call.message.chat.id, time_str)
    await create_default_categories(call.message.chat.id, lang)
    await mark_onboarding_done(call.message.chat.id)

    await state.clear()

    await call.message.edit_text(t("digest_time_set", lang, time=time_str))
    await call.message.answer(t("onboarding_done", lang))
    await call.message.answer(
        t("main_menu", lang),
        reply_markup=main_keyboard(lang),
    )
    await call.answer()


# ── /cancel — escape any stuck FSM state ────────────────────────────────────

@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Clear any active FSM state and return to main menu."""
    db_user = await get_or_create_user(message.chat.id)
    lang = db_user.get("language", "ru") if db_user else "ru"
    await state.clear()
    cancel_text = "✅ Готово. Можешь писать задачи!" if lang == "ru" else "✅ Done. You can write tasks now!"
    await message.answer(cancel_text, reply_markup=main_keyboard(lang))


# ── /menu — quick return to main menu ───────────────────────────────────────

@dp.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    """Show main menu and clear any stuck state."""
    db_user = await get_or_create_user(message.chat.id)
    lang = db_user.get("language", "ru") if db_user else "ru"
    await state.clear()
    await message.answer(t("main_menu", lang), reply_markup=main_keyboard(lang))
