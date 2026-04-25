"""
AI parser — определяет является ли сообщение задачей и извлекает её поля.

Ключевые изменения v2:
  - Добавлено поле is_task (bool) — ИИ сам решает задача это или нет
  - remind_before УБРАН из парсера — пользователь выбирает его вручную
  - recurrence остаётся (ИИ может распознать «каждый день»)
"""

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from zoneinfo import ZoneInfo

from openai import AsyncOpenAI

from config import logger, settings

_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


@dataclass
class TaskDraft:
    is_task: bool                        # False → не задача, игнорируем
    title: str
    scheduled_date: date
    scheduled_time: Optional[str]        # "HH:MM" or None
    priority: str                        # low | medium | high
    recurrence: Optional[str]            # daily | weekly | monthly | weekdays | None
    category_hint: Optional[str]         # "Work" | "Personal" | "Health" | etc.
    description: Optional[str] = None


_SYSTEM = """\
You are an AI assistant inside a personal planner Telegram bot.

Your job: decide if the user's message is a task/reminder/plan, and if so — extract its details.

Today's date: {today}
User's timezone: {tz}

Respond ONLY with a valid JSON object. No markdown, no explanation.

JSON schema:
{{
  "is_task": true | false,
  "title": "concise task title, max 80 chars (empty string if not a task)",
  "scheduled_date": "YYYY-MM-DD (use today if no date mentioned)",
  "scheduled_time": "HH:MM" or null,
  "priority": "low" | "medium" | "high",
  "recurrence": "daily" | "weekly" | "monthly" | "weekdays" | null,
  "category_hint": "Work" | "Personal" | "Health" | "Finance" | "Other" | null,
  "description": "string or null"
}}

Rules for is_task — set TRUE for any of these:
- Personal tasks: buy, call, send, write, fix, clean, cook, read, prepare, meet
- Appointments/events: meeting, doctor, dentist, gym, date, flight, trip
- Plans stated as facts: "есть дела" (have things), "нужно поесть" (need to eat)
- Any message with a date/time expression + any implied action
- Russian: есть, нужно, надо, должен, планирую, собираюсь, хочу
- English: have to, need to, gotta, supposed to, planning to, going to

Set FALSE only for:
- Pure questions: "what is...", "как...", "что такое..."
- Greetings: "hi", "hello", "привет", "спасибо"
- Bot menu commands in text: "покажи расписание", "статистика"
- Conversational replies: "ok", "понял", "хорошо", "да", "нет"

Rules for fields (only relevant when is_task=true):
- "today"/"сегодня" → {today}
- "tomorrow"/"завтра" → next day's date
- "послезавтра" → {today} + 2 days
- "next week"/"на следующей неделе" → +7 days
- "в пятницу"/"on friday" → nearest upcoming Friday
- "в 5 вечера"/"at 5pm"/"в 17:00" → "17:00"
- "в 5 утра"/"at 5am" → "05:00"
- "в полдень"/"at noon"/"в обед" → "12:00"
- "утром"/"вечером" with no specific time → scheduled_time = null
- Words like "важно", "срочно", "urgent", "asap" → priority "high"
- Default priority: "medium"
- NEVER include remind_before in output
- If no date mentioned → use today's date ({today})
- If no time mentioned → scheduled_time = null
"""


async def parse_message(text: str, user_tz: str = "UTC") -> "TaskDraft | None":
    """
    Parse any user message.
    Returns TaskDraft with is_task=False if it's not a task.
    Returns None only on hard API failure.
    """
    today = datetime.now(ZoneInfo(user_tz)).date()
    system_prompt = _SYSTEM.format(today=today.isoformat(), tz=user_tz)

    try:
        response = await _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": text},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=250,
        )
        data = json.loads(response.choices[0].message.content)

        if not data.get("is_task"):
            return TaskDraft(
                is_task=False,
                title="",
                scheduled_date=today,
                scheduled_time=None,
                priority="medium",
                recurrence=None,
                category_hint=None,
            )

        scheduled_date = date.fromisoformat(data["scheduled_date"])

        return TaskDraft(
            is_task=True,
            title=(data.get("title") or "")[:80].strip(),
            scheduled_date=scheduled_date,
            scheduled_time=data.get("scheduled_time"),
            priority=data.get("priority", "medium"),
            recurrence=data.get("recurrence"),
            category_hint=data.get("category_hint"),
            description=data.get("description"),
        )

    except Exception as e:
        logger.warning("ai_parser.parse_message failed: %s", e)
        return None


# Alias for backward compat
async def parse_task(text: str, user_tz: str = "UTC") -> "TaskDraft | None":
    return await parse_message(text, user_tz)


async def generate_ai_digest(
    tasks: list[dict],
    user_name: str,
    lang: str,
    user_tz: str = "UTC",
) -> "str | None":
    """Premium: personalised morning digest summary (2-3 sentences)."""
    if not tasks:
        return None

    task_list = "\n".join(
        f"- {t.get('scheduled_time', 'no time')}: {t['title']} (priority: {t.get('priority', 'medium')})"
        for t in tasks[:10]
    )
    lang_instruction = "Respond in Russian." if lang == "ru" else "Respond in English."
    prompt = (
        f"User name: {user_name or 'the user'}\n"
        f"Their tasks for today:\n{task_list}\n\n"
        f"Write a short, warm, motivating 2-3 sentence morning summary "
        f"mentioning the most important tasks. Be friendly and encouraging. "
        f"{lang_instruction}"
    )

    try:
        response = await _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("generate_ai_digest failed: %s", e)
        return None
