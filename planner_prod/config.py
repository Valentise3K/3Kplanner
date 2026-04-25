import logging
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("planner_bot")


@dataclass(frozen=True)
class Settings:
    BOT_TOKEN: str
    OPENAI_API_KEY: str
    DATABASE_URL: str
    REDIS_URL: str
    ENCRYPTION_KEY: str
    DEFAULT_TIMEZONE: str
    # Telegram Stars
    STARS_PREMIUM_MONTH: int
    STARS_PREMIUM_YEAR: int
    # YooKassa (RU/CIS)
    YOOKASSA_SHOP_ID: str
    YOOKASSA_SECRET_KEY: str
    YOOKASSA_WEBHOOK_URL: str
    # Stripe (International)
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    # Webhook server
    WEBHOOK_HOST: str
    WEBHOOK_PORT: int


def _load() -> Settings:
    bot_token              = os.getenv("PLANNER_BOT_TOKEN")
    openai_key             = os.getenv("OPENAI_API_KEY")
    db_url                 = os.getenv("PLANNER_DATABASE_URL")
    redis_url              = os.getenv("PLANNER_REDIS_URL", "redis://localhost:6379/1")
    encryption_key         = os.getenv("ENCRYPTION_KEY")
    default_tz             = os.getenv("DEFAULT_TIMEZONE", "UTC")
    stars_month            = int(os.getenv("STARS_PREMIUM_MONTH", "150"))
    stars_year             = int(os.getenv("STARS_PREMIUM_YEAR", "750"))
    yookassa_shop          = os.getenv("YOOKASSA_SHOP_ID", "")
    yookassa_secret        = os.getenv("YOOKASSA_SECRET_KEY", "")
    yookassa_webhook_url   = os.getenv("YOOKASSA_WEBHOOK_URL", "")
    stripe_secret          = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret  = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    webhook_host           = os.getenv("WEBHOOK_HOST", "")
    webhook_port           = int(os.getenv("WEBHOOK_PORT", "8080"))

    missing = [
        k for k, v in {
            "PLANNER_BOT_TOKEN":    bot_token,
            "OPENAI_API_KEY":       openai_key,
            "PLANNER_DATABASE_URL": db_url,
            "ENCRYPTION_KEY":       encryption_key,
        }.items() if not v
    ]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")

    return Settings(
        BOT_TOKEN=bot_token,
        OPENAI_API_KEY=openai_key,
        DATABASE_URL=db_url,
        REDIS_URL=redis_url,
        ENCRYPTION_KEY=encryption_key,
        DEFAULT_TIMEZONE=default_tz,
        STARS_PREMIUM_MONTH=stars_month,
        STARS_PREMIUM_YEAR=stars_year,
        YOOKASSA_SHOP_ID=yookassa_shop,
        YOOKASSA_SECRET_KEY=yookassa_secret,
        YOOKASSA_WEBHOOK_URL=yookassa_webhook_url,
        STRIPE_SECRET_KEY=stripe_secret,
        STRIPE_WEBHOOK_SECRET=stripe_webhook_secret,
        WEBHOOK_HOST=webhook_host,
        WEBHOOK_PORT=webhook_port,
    )


settings = _load()

# Plan limits
FREE_TASKS_PER_DAY    = 10
FREE_CATEGORIES_LIMIT = 3
FREE_STATS_DAYS       = 7
FREE_REMINDERS_LIMIT  = 1

PREMIUM_STATS_DAYS    = 90
PREMIUM_REMINDERS_LIMIT = 5
