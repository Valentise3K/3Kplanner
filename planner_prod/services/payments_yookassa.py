"""
YooKassa payment service — для пользователей из России и СНГ.

Поддерживаемые методы оплаты через YooKassa:
  - Банковские карты (Visa/MC/МИР)
  - ЮMoney (Яндекс.Деньги)
  - SberPay
  - Тинькофф Pay
  - СБП (Система быстрых платежей)
  - QIWI, WebMoney и др.

Валюта: RUB (рубли).
Иностранные карты (Visa/MC выпущенные не в RU) через YooKassa
принимаются, но сумма всегда в рублях — банк карты конвертирует сам.
"""

import hashlib
import hmac
import json
import uuid
from typing import Optional

from config import logger, settings

# Цены в рублях
PRICE_MONTH_RUB = "199.00"
PRICE_YEAR_RUB  = "990.00"


def _yookassa_available() -> bool:
    return bool(settings.YOOKASSA_SHOP_ID and settings.YOOKASSA_SECRET_KEY)


async def create_payment(
    chat_id: int,
    plan: str,          # "premium_month" | "premium_year"
    user_lang: str,
    idempotency_key: Optional[str] = None,
) -> dict | None:
    """
    Create a YooKassa payment and return {payment_id, confirmation_url}.
    Returns None if YooKassa is not configured.
    """
    if not _yookassa_available():
        return None

    try:
        from yookassa import Configuration, Payment
        Configuration.configure(
            account_id=settings.YOOKASSA_SHOP_ID,
            secret_key=settings.YOOKASSA_SECRET_KEY,
        )
    except ImportError:
        logger.warning("yookassa package not installed")
        return None

    is_month = plan == "premium_month"
    amount   = PRICE_MONTH_RUB if is_month else PRICE_YEAR_RUB
    months   = 1 if is_month else 12

    if user_lang == "ru":
        description = f"PlannerBot Premium — {'1 месяц' if is_month else '1 год'}"
    else:
        description = f"PlannerBot Premium — {'1 month' if is_month else '1 year'}"

    idem_key = idempotency_key or str(uuid.uuid4())

    try:
        payment = Payment.create({
            "amount": {
                "value":    amount,
                "currency": "RUB",
            },
            "confirmation": {
                "type":       "redirect",
                "return_url": f"{settings.YOOKASSA_WEBHOOK_URL}/return?chat_id={chat_id}",
            },
            "capture":      True,
            "description":  description,
            "metadata": {
                "chat_id": str(chat_id),
                "plan":    plan,
                "months":  str(months),
            },
        }, idem_key)

        return {
            "payment_id":        payment.id,
            "confirmation_url":  payment.confirmation.confirmation_url,
            "amount":            amount,
            "currency":          "RUB",
            "months":            months,
        }

    except Exception as e:
        logger.error("YooKassa create_payment error: %s", e)
        return None


async def verify_webhook(body: bytes, signature_header: str) -> bool:
    """
    Verify the YooKassa webhook signature.
    YooKassa does NOT sign webhooks with HMAC — it uses IP allowlist instead.
    This function validates the JSON structure as a basic sanity check.
    For production: restrict to YooKassa IPs in Nginx.
    """
    try:
        data = json.loads(body)
        return "event" in data and "object" in data
    except Exception:
        return False


async def handle_webhook_event(body: bytes) -> tuple[int | None, int | None]:
    """
    Parse a YooKassa webhook event.
    Returns (chat_id, months) if payment succeeded, else (None, None).
    """
    try:
        data    = json.loads(body)
        event   = data.get("event", "")
        obj     = data.get("object", {})
        status  = obj.get("status", "")

        if event != "payment.succeeded" or status != "succeeded":
            return None, None

        metadata = obj.get("metadata", {})
        chat_id  = int(metadata.get("chat_id", 0))
        months   = int(metadata.get("months",  1))

        if not chat_id:
            logger.warning("YooKassa webhook: no chat_id in metadata")
            return None, None

        payment_id = obj.get("id", "unknown")
        amount     = obj.get("amount", {}).get("value", "?")
        logger.info(
            "YooKassa payment succeeded: id=%s chat_id=%s amount=%s RUB months=%d",
            payment_id, chat_id, amount, months,
        )

        # Save to payments table
        await _record_payment(
            chat_id    = chat_id,
            provider   = "yookassa",
            provider_id= payment_id,
            plan       = metadata.get("plan", "premium_month"),
            amount     = float(amount),
            currency   = "RUB",
            months     = months,
        )

        return chat_id, months

    except Exception as e:
        logger.error("YooKassa webhook parse error: %s", e)
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
