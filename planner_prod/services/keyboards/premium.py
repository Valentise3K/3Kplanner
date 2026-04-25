from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import settings
from locales import t

CB_BUY_STARS_MONTH  = "buy:stars:month"
CB_BUY_STARS_YEAR   = "buy:stars:year"
CB_BUY_RUB_MONTH    = "buy:rub:month"
CB_BUY_RUB_YEAR     = "buy:rub:year"


def premium_plans_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("btn_month_stars", lang, stars=settings.STARS_PREMIUM_MONTH),
        callback_data=CB_BUY_STARS_MONTH,
    )
    builder.button(
        text=t("btn_year_stars", lang, stars=settings.STARS_PREMIUM_YEAR),
        callback_data=CB_BUY_STARS_YEAR,
    )
    if settings.YOOKASSA_SHOP_ID:
        builder.button(text=t("btn_month_rub", lang), callback_data=CB_BUY_RUB_MONTH)
        builder.button(text=t("btn_year_rub", lang),  callback_data=CB_BUY_RUB_YEAR)

    builder.button(text=t("btn_back", lang), callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()
