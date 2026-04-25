"""
Premium handler — Telegram Stars + YooKassa (RU/СНГ) + Stripe (International).

Логика выбора метода оплаты:
  - Telegram Stars    — доступно ВСЕМ пользователям (работает глобально)
  - YooKassa/карта    — показывается если YOOKASSA_SHOP_ID задан (для RU/СНГ)
  - Stripe/карта      — показывается если STRIPE_SECRET_KEY задан (для остальных)
  - Бот автоматически определяет регион по языку: ru → YooKassa, en → Stripe
    Пользователь может переключиться вручную кнопкой 🌍
"""

from datetime import datetime

from aiogram import F
from aiogram.types import (
    CallbackQuery, InlineKeyboardMarkup, LabeledPrice,
    Message, PreCheckoutQuery, SuccessfulPayment,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import settings
from database.users import activate_premium, get_user
from instance import bot, dp
from keyboards.main import main_keyboard
from locales import t

CB_BUY_STARS_MONTH = "buy:stars:month"
CB_BUY_STARS_YEAR  = "buy:stars:year"
CB_BUY_RUB_MONTH   = "buy:rub:month"
CB_BUY_RUB_YEAR    = "buy:rub:year"
CB_BUY_USD_MONTH   = "buy:usd:month"
CB_BUY_USD_YEAR    = "buy:usd:year"
CB_SWITCH_PAYMENT  = "premium:switch_payment"


def _payment_keyboard(lang: str, show_rub: bool, show_usd: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Telegram Stars — всегда первыми
    builder.button(
        text=f"⭐ {settings.STARS_PREMIUM_MONTH} Stars / " + ("мес." if lang == "ru" else "mo."),
        callback_data=CB_BUY_STARS_MONTH,
    )
    builder.button(
        text=f"⭐ {settings.STARS_PREMIUM_YEAR} Stars / " + ("год −58%" if lang == "ru" else "yr −58%"),
        callback_data=CB_BUY_STARS_YEAR,
    )

    # YooKassa (RUB)
    if show_rub and settings.YOOKASSA_SHOP_ID:
        builder.button(text="💳 199 ₽ / " + ("мес." if lang == "ru" else "mo."), callback_data=CB_BUY_RUB_MONTH)
        builder.button(text="💳 990 ₽ / " + ("год −58%" if lang == "ru" else "yr −58%"), callback_data=CB_BUY_RUB_YEAR)

    # Stripe (USD)
    if show_usd and settings.STRIPE_SECRET_KEY:
        builder.button(text="💳 $2.99 / " + ("мес." if lang == "ru" else "mo."), callback_data=CB_BUY_USD_MONTH)
        builder.button(text="💳 $14.99 / " + ("год −58%" if lang == "ru" else "yr −58%"), callback_data=CB_BUY_USD_YEAR)

    # Переключатель региона
    if settings.YOOKASSA_SHOP_ID and settings.STRIPE_SECRET_KEY:
        switch_label = ("🌍 Оплата картой (USD)" if show_rub else "🇷🇺 Оплата картой (RUB)")
        builder.button(text=switch_label, callback_data=CB_SWITCH_PAYMENT)

    builder.adjust(2)
    return builder.as_markup()


async def _send_premium_menu(chat_id: int, lang: str, target):
    show_rub = (lang == "ru")
    text = t("premium_menu", lang)
    kb   = _payment_keyboard(lang, show_rub=show_rub, show_usd=not show_rub)
    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=kb)
        except Exception:
            await target.message.answer(text, reply_markup=kb)
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb)


@dp.message(F.text.func(lambda x: x and "⭐" in x and "Premium" in x))
async def btn_premium(message: Message, lang: str, is_premium: bool) -> None:
    if is_premium:
        user  = await get_user(message.chat.id)
        until = user["plan_until"].strftime("%d.%m.%Y") if user.get("plan_until") else "—"
        await message.answer(t("premium_active", lang, until=until))
        return
    await _send_premium_menu(message.chat.id, lang, message)


@dp.callback_query(F.data == "open_premium")
async def cb_open_premium(call: CallbackQuery, lang: str, is_premium: bool) -> None:
    if is_premium:
        user  = await get_user(call.message.chat.id)
        until = user["plan_until"].strftime("%d.%m.%Y") if user.get("plan_until") else "—"
        try:
            await call.message.edit_text(t("premium_active", lang, until=until))
        except Exception:
            pass
        await call.answer()
        return
    await _send_premium_menu(call.message.chat.id, lang, call)


@dp.callback_query(F.data == CB_SWITCH_PAYMENT)
async def cb_switch_payment(call: CallbackQuery, lang: str) -> None:
    kb_rows = call.message.reply_markup.inline_keyboard if call.message.reply_markup else []
    currently_rub = any("₽" in btn.text for row in kb_rows for btn in row)
    new_show_rub  = not currently_rub
    await call.message.edit_reply_markup(
        reply_markup=_payment_keyboard(lang, show_rub=new_show_rub, show_usd=not new_show_rub)
    )
    await call.answer()


# ── Telegram Stars ────────────────────────────────────────────────────────────

@dp.callback_query(F.data.in_({CB_BUY_STARS_MONTH, CB_BUY_STARS_YEAR}))
async def cb_buy_stars(call: CallbackQuery, lang: str) -> None:
    is_month = call.data == CB_BUY_STARS_MONTH
    months   = 1 if is_month else 12
    stars    = settings.STARS_PREMIUM_MONTH if is_month else settings.STARS_PREMIUM_YEAR
    title    = ("Premium — 1 месяц" if is_month else "Premium — 1 год") if lang == "ru" else \
               ("Premium — 1 month" if is_month else "Premium — 1 year")
    desc     = ("Безлимитные задачи, голос, привычки и многое другое!" if lang == "ru"
                else "Unlimited tasks, voice, habits and much more!")
    await bot.send_invoice(
        chat_id=call.message.chat.id, title=title, description=desc,
        payload=f"premium:{months}:{call.message.chat.id}",
        currency="XTR", prices=[LabeledPrice(label="Premium", amount=stars)],
    )
    await call.answer()


@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@dp.message(F.successful_payment)
async def payment_stars_success(message: Message, lang: str) -> None:
    payload = message.successful_payment.invoice_payload
    try:
        _, months_str, _ = payload.split(":")
        months = int(months_str)
    except Exception:
        months = 1
    until = await activate_premium(message.chat.id, months)
    await message.answer(
        t("payment_success", lang, until=until.strftime("%d.%m.%Y")),
        reply_markup=main_keyboard(lang),
    )


# ── YooKassa (RUB) ────────────────────────────────────────────────────────────

@dp.callback_query(F.data.in_({CB_BUY_RUB_MONTH, CB_BUY_RUB_YEAR}))
async def cb_buy_rub(call: CallbackQuery, lang: str) -> None:
    is_month = call.data == CB_BUY_RUB_MONTH
    plan = "premium_month" if is_month else "premium_year"
    from services.payments_yookassa import create_payment
    result = await create_payment(call.message.chat.id, plan, lang)
    if not result:
        await call.answer(t("payment_failed", lang), show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Оплатить" if lang == "ru" else "💳 Pay now", url=result["confirmation_url"])
    text = (
        f"💳 <b>Оплата картой</b>\n\nСумма: <b>{result['amount']} ₽</b>\n\n"
        f"<i>После оплаты Premium активируется автоматически.</i>"
        if lang == "ru" else
        f"💳 <b>Card Payment</b>\n\nAmount: <b>{result['amount']} RUB</b>\n\n"
        f"<i>Premium activates automatically after payment.</i>"
    )
    await call.message.answer(text, reply_markup=builder.as_markup())
    await call.answer()


# ── Stripe (USD / International) ─────────────────────────────────────────────

@dp.callback_query(F.data.in_({CB_BUY_USD_MONTH, CB_BUY_USD_YEAR}))
async def cb_buy_usd(call: CallbackQuery, lang: str) -> None:
    is_month = call.data == CB_BUY_USD_MONTH
    plan = "premium_month" if is_month else "premium_year"
    from services.payments_stripe import create_checkout_session
    result = await create_checkout_session(call.message.chat.id, plan, lang)
    if not result:
        await call.answer(t("payment_failed", lang), show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Pay now" if lang == "en" else "💳 Оплатить", url=result["checkout_url"])
    text = (
        f"💳 <b>Card Payment</b>\n\nAmount: <b>${result['amount_usd']:.2f} USD</b>\n\n"
        f"<i>Visa, Mastercard, Amex, Apple Pay, Google Pay and 135+ methods.\n"
        f"Premium activates automatically after payment.</i>"
        if lang == "en" else
        f"💳 <b>Оплата картой (USD)</b>\n\nСумма: <b>${result['amount_usd']:.2f}</b>\n\n"
        f"<i>Visa, Mastercard, Amex, Apple Pay, Google Pay и 135+ методов.\n"
        f"Premium активируется автоматически.</i>"
    )
    await call.message.answer(text, reply_markup=builder.as_markup())
    await call.answer()
