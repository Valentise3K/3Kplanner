"""
Webhook HTTP server (aiohttp) — запускается параллельно с ботом.

Обрабатывает:
  POST /webhook/yookassa  — уведомления от YooKassa
  POST /webhook/stripe    — уведомления от Stripe
  GET  /health            — healthcheck для мониторинга
"""

import asyncio

from aiohttp import web

from config import logger, settings
from database.users import activate_premium
from instance import bot
from locales import t


# ── YooKassa webhook ─────────────────────────────────────────────────────────

async def yookassa_webhook(request: web.Request) -> web.Response:
    body = await request.read()

    from services.payments_yookassa import handle_webhook_event
    chat_id, months = await handle_webhook_event(body)

    if chat_id and months:
        await _grant_premium_and_notify(chat_id, months)

    return web.Response(status=200, text="ok")


# ── Stripe webhook ────────────────────────────────────────────────────────────

async def stripe_webhook(request: web.Request) -> web.Response:
    body       = await request.read()
    sig_header = request.headers.get("Stripe-Signature", "")

    from services.payments_stripe import verify_webhook_signature, handle_webhook_event
    if not await verify_webhook_signature(body, sig_header):
        logger.warning("Stripe webhook: invalid signature")
        return web.Response(status=400, text="invalid signature")

    chat_id, months = await handle_webhook_event(body, sig_header)

    if chat_id and months:
        await _grant_premium_and_notify(chat_id, months)

    return web.Response(status=200, text="ok")


# ── Shared helper ─────────────────────────────────────────────────────────────

async def _grant_premium_and_notify(chat_id: int, months: int) -> None:
    """Activate premium in DB and send confirmation message to user."""
    from database.users import get_user_lang
    try:
        until    = await activate_premium(chat_id, months)
        lang     = await get_user_lang(chat_id)
        until_str = until.strftime("%d.%m.%Y")

        from keyboards.main import main_keyboard
        await bot.send_message(
            chat_id,
            t("payment_success", lang, until=until_str),
            reply_markup=main_keyboard(lang),
        )
        logger.info("Premium activated: chat_id=%s months=%d until=%s", chat_id, months, until_str)
    except Exception as e:
        logger.error("Failed to grant premium to %s: %s", chat_id, e)


# ── Health check ──────────────────────────────────────────────────────────────

async def health_check(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "service": "plannerbot"})


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> web.Application:
    app = web.Application()
    app.router.add_post("/webhook/yookassa", yookassa_webhook)
    app.router.add_post("/webhook/stripe",   stripe_webhook)
    app.router.add_get("/health",            health_check)
    return app


async def start_webhook_server() -> None:
    """Start the aiohttp server on port 8080. Call this from bot.py."""
    app    = create_app()
    runner = web.AppRunner(app)
    await runner.setup()

    port = int(getattr(settings, "WEBHOOK_PORT", 8080))
    site = web.TCPSite(runner, "127.0.0.1", port)
    await site.start()
    logger.info("Webhook server listening on 127.0.0.1:%d", port)
