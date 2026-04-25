"""
Stripe payment service — для международных пользователей (USD, EUR и т.д.)

Поддерживаемые методы через Stripe:
  - Visa / Mastercard (любая страна)
  - American Express
  - Apple Pay / Google Pay
  - SEPA Debit (Европа)
  - iDEAL (Нидерланды)
  - Bancontact (Бельгия)
  - И ещё 135+ методов по всему миру

Валюта: USD (по умолчанию). Stripe автоматически показывает
локальную валюту пользователя в зависимости от страны его карты.
"""

import json
from typing import Optional

from config import logger, settings

# Цены в центах USD
PRICE_MONTH_USD_CENTS = 299   # $2.99/месяц
PRICE_YEAR_USD_CENTS  = 1499  # $14.99/год


def _stripe_available() -> bool:
    return bool(settings.STRIPE_SECRET_KEY)


async def create_checkout_session(
    chat_id: int,
    plan: str,          # "premium_month" | "premium_year"
    user_lang: str,
) -> dict | None:
    """
    Create a Stripe Checkout Session.
    Returns {session_id, checkout_url} or None if Stripe not configured.
    """
    if not _stripe_available():
        return None

    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
    except ImportError:
        logger.warning("stripe package not installed")
        return None

    is_month = plan == "premium_month"
    months   = 1 if is_month else 12
    amount   = PRICE_MONTH_USD_CENTS if is_month else PRICE_YEAR_USD_CENTS

    if user_lang == "ru":
        product_name = f"PlannerBot Premium — {'1 месяц' if is_month else '1 год'}"
    else:
        product_name = f"PlannerBot Premium — {'1 month' if is_month else '1 year'}"

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency":     "usd",
                    "unit_amount":  amount,
                    "product_data": {"name": product_name},
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=(
                f"{settings.WEBHOOK_HOST}/payment/success"
                f"?session_id={{CHECKOUT_SESSION_ID}}&chat_id={chat_id}"
            ),
            cancel_url=f"{settings.WEBHOOK_HOST}/payment/cancel?chat_id={chat_id}",
            metadata={
                "chat_id": str(chat_id),
                "plan":    plan,
                "months":  str(months),
            },
            # Enable automatic tax collection (optional)
            # automatic_tax={"enabled": True},
            # Allow 135+ payment methods automatically
            payment_method_options={},
            locale=user_lang if user_lang in ("ru", "en", "de", "fr", "es") else "auto",
        )

        logger.info("Stripe session created: %s for chat_id=%s", session.id, chat_id)
        return {
            "session_id":   session.id,
            "checkout_url": session.url,
            "amount_usd":   amount / 100,
            "months":       months,
        }

    except Exception as e:
        logger.error("Stripe create_session error: %s", e)
        return None


async def verify_webhook_signature(body: bytes, sig_header: str) -> bool:
    """Verify Stripe webhook signature using HMAC."""
    if not settings.STRIPE_WEBHOOK_SECRET:
        return False
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.Webhook.construct_event(
            body, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        return True
    except Exception:
        return False


async def handle_webhook_event(body: bytes, sig_header: str) -> tuple[int | None, int | None]:
    """
    Parse Stripe webhook event.
    Returns (chat_id, months) on successful payment, else (None, None).
    """
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        event = stripe.Webhook.construct_event(
            body, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )

        if event["type"] != "checkout.session.completed":
            return None, None

        session  = event["data"]["object"]
        metadata = session.get("metadata", {})
        chat_id  = int(metadata.get("chat_id", 0))
        months   = int(metadata.get("months",  1))

        if not chat_id:
            return None, None

        amount_total = session.get("amount_total", 0) / 100
        currency     = session.get("currency", "usd").upper()

        logger.info(
            "Stripe payment succeeded: session=%s chat_id=%s amount=%.2f %s months=%d",
            session["id"], chat_id, amount_total, currency, months,
        )

        await _record_payment(
            chat_id    = chat_id,
            provider   = "stripe",
            provider_id= session["id"],
            plan       = metadata.get("plan", "premium_month"),
            amount     = amount_total,
            currency   = currency,
            months     = months,
        )

        return chat_id, months

    except Exception as e:
        logger.error("Stripe webhook parse error: %s", e)
        return None, None


async def _record_payment(
    chat_id: int, provider: str, provider_id: str,
    plan: str, amount: float, currency: str, months: int,
) -> None:
    from database.pool import get_pool
    pool = await get_pool()
    await pool.execute(
        """
        INSERT INTO payments
            (chat_id, provider, provider_id, plan, amount, currency, status, period_months)
        VALUES ($1,$2,$3,$4,$5,$6,'success',$7)
        ON CONFLICT DO NOTHING
        """,
        chat_id, provider, provider_id, plan, amount, currency, months,
    )
