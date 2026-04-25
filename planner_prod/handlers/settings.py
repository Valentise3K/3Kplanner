"""Settings handler: language, city, digest time, evening toggle."""

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.users import (
    get_user,
    save_digest_time,
    save_user_language,
    save_user_location,
    toggle_evening_digest,
)
from geocoding import resolve_timezone
from instance import dp
from keyboards.main import digest_time_keyboard, language_keyboard, main_keyboard
from locales import t
from crypto import decrypt


class SettingsStates(StatesGroup):
    entering_city   = State()
    entering_digest = State()


def _settings_digest_keyboard(lang: str):
    """Digest time picker for settings — uses 'sdigest:' prefix to avoid
    conflicting with the onboarding 'digest:' callback in start.py."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    times = ["06:00", "07:00", "08:00", "09:00", "10:00"]
    builder = InlineKeyboardBuilder()
    for time_str in times:
        builder.button(text=f"🕐 {time_str}", callback_data=f"sdigest:{time_str}")
    builder.adjust(3)
    return builder.as_markup()


def _settings_keyboard(lang: str, evening_on: bool):
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_change_language", lang), callback_data="settings:lang")
    builder.button(text=t("btn_change_city", lang),     callback_data="settings:city")
    builder.button(text=t("btn_change_digest", lang),   callback_data="settings:digest")

    evening_state = t("evening_on", lang) if evening_on else t("evening_off", lang)
    builder.button(
        text=t("btn_toggle_evening", lang, state=evening_state),
        callback_data="settings:toggle_evening",
    )
    builder.adjust(2, 1, 1)
    return builder.as_markup()


# ── "Settings" button ─────────────────────────────────────────────────────

@dp.message(F.text.func(lambda x: x and "⚙️" in x))
async def btn_settings(message: Message, lang: str) -> None:
    user = await get_user(message.chat.id)
    if not user:
        return

    city = decrypt(user["city"]) if user.get("city") else "—"
    tz   = decrypt(user["timezone"]) if user.get("timezone") else "UTC"
    dt   = user["digest_time"].strftime("%H:%M") if user.get("digest_time") else "08:00"

    await message.answer(
        t("settings_menu", lang,
          language="Русский" if lang == "ru" else "English",
          city=city,
          timezone=tz,
          digest_time=dt,
          evening=t("evening_on", lang) if user.get("evening_digest", True) else t("evening_off", lang)),
        reply_markup=_settings_keyboard(lang, user.get("evening_digest", True)),
    )


# ── Callbacks ────────────────────────────────────────────────────────────────

@dp.callback_query(F.data == "settings:lang")
async def cb_settings_lang(call: CallbackQuery, lang: str) -> None:
    await call.message.edit_text(
        t("choose_language", lang),
        reply_markup=language_keyboard(),
    )
    await call.answer()


@dp.callback_query(F.data == "settings:city")
async def cb_settings_city(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(SettingsStates.entering_city)
    await state.update_data(lang=lang)
    await call.message.edit_text(t("ask_city", lang))
    await call.answer()


@dp.message(SettingsStates.entering_city)
async def process_city_settings(message: Message, state: FSMContext, lang: str) -> None:
    city = message.text.strip()
    timezone = await resolve_timezone(city)
    if not timezone:
        await message.answer(t("city_not_found", lang))
        return

    await save_user_location(message.chat.id, city, timezone)
    await state.clear()
    await message.answer(
        t("city_updated", lang, city=city, timezone=timezone),
        reply_markup=main_keyboard(lang),
    )


@dp.callback_query(F.data == "settings:digest")
async def cb_settings_digest(call: CallbackQuery, lang: str) -> None:
    await call.message.edit_text(
        t("ask_digest_time", lang),
        reply_markup=_settings_digest_keyboard(lang),
    )
    await call.answer()


@dp.callback_query(F.data.startswith("sdigest:"))
async def cb_digest_time_settings(call: CallbackQuery, lang: str) -> None:
    time_str = call.data.split(":", 1)[1]
    await save_digest_time(call.message.chat.id, time_str)
    await call.message.edit_text(t("digest_updated", lang, time=time_str))
    await call.message.answer(t("main_menu", lang), reply_markup=main_keyboard(lang))
    await call.answer()


@dp.callback_query(F.data == "settings:toggle_evening")
async def cb_toggle_evening(call: CallbackQuery, lang: str) -> None:
    new_state = await toggle_evening_digest(call.message.chat.id)
    state_label = t("evening_on", lang) if new_state else t("evening_off", lang)
    notice = (f"🌙 Вечерняя сводка {state_label}" if lang == "ru"
              else f"🌙 Evening digest {state_label}")
    await call.answer(notice, show_alert=True)
    # Refresh settings menu
    user = await get_user(call.message.chat.id)
    city = decrypt(user["city"]) if user.get("city") else "—"
    tz   = decrypt(user["timezone"]) if user.get("timezone") else "UTC"
    dt   = user["digest_time"].strftime("%H:%M") if user.get("digest_time") else "08:00"
    await call.message.edit_text(
        t("settings_menu", lang,
          language="Русский" if lang == "ru" else "English",
          city=city, timezone=tz, digest_time=dt,
          evening=t("evening_on", lang) if new_state else t("evening_off", lang)),
        reply_markup=_settings_keyboard(lang, new_state),
    )


@dp.callback_query(F.data == "back_main")
async def cb_back_main(call: CallbackQuery, lang: str) -> None:
    await call.message.edit_text(t("main_menu", lang))
    await call.answer()
