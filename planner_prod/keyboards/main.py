from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from locales import t

# ── Callback data prefixes ───────────────────────────────────────────────────
CB_LANG          = "lang:"           # lang:ru  / lang:en
CB_DIGEST_TIME   = "digest:"         # digest:08:00
CB_MAIN_MENU     = "main_menu"

# ── Language selection ───────────────────────────────────────────────────────

def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇷🇺 Русский", callback_data="lang:ru")
    builder.button(text="🇬🇧 English", callback_data="lang:en")
    builder.adjust(2)
    return builder.as_markup()


# ── Digest time selection ────────────────────────────────────────────────────

def digest_time_keyboard(lang: str) -> InlineKeyboardMarkup:
    times = ["06:00", "07:00", "08:00", "09:00", "10:00"]
    builder = InlineKeyboardBuilder()
    for time_str in times:
        builder.button(text=f"🕐 {time_str}", callback_data=f"digest:{time_str}")
    builder.adjust(3)
    return builder.as_markup()


# ── Main menu (Reply keyboard) ───────────────────────────────────────────────

def main_keyboard(lang: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=t("btn_today", lang))
    builder.button(text=t("btn_schedule", lang))
    builder.button(text=t("btn_add_task", lang))
    builder.button(text=t("btn_stats", lang))
    builder.button(text=t("btn_habits", lang))
    builder.button(text=t("btn_settings", lang))
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)


# ── Back button ──────────────────────────────────────────────────────────────

def back_keyboard(lang: str, callback: str = "back_main") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_back", lang), callback_data=callback)
    return builder.as_markup()


# ── Premium upsell ───────────────────────────────────────────────────────────

def premium_upsell_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_get_premium", lang), callback_data="open_premium")
    return builder.as_markup()
