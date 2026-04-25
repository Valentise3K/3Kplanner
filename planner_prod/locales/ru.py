# All Russian UI strings for PlannerBot

STRINGS: dict[str, str] = {
    # ── Onboarding ──────────────────────────────────────────────
    "choose_language":      "🌍 Выбери язык / Choose language:",
    "lang_set":             "✅ Язык установлен: Русский",
    "welcome_new":          (
        "👋 Привет! Я <b>PlannerBot</b> — твой личный ежедневник в Telegram.\n\n"
        "Я помогу тебе:\n"
        "📋 Планировать день и задачи\n"
        "🔔 Напоминать о важных делах\n"
        "📊 Следить за продуктивностью\n\n"
        "Давай настроим бота за 1 минуту!"
    ),
    "ask_city":             (
        "🌍 <b>Укажи свой город</b>\n\n"
        "Это нужно для правильного часового пояса.\n"
        "Напиши название города:"
    ),
    "city_not_found":       "❌ Город не найден. Попробуй ещё раз или напиши на английском (например: Moscow):",
    "city_found":           "✅ Город: <b>{city}</b>\nЧасовой пояс: <b>{timezone}</b>",
    "ask_digest_time":      (
        "🌅 <b>Когда присылать утренний дайджест?</b>\n\n"
        "Каждый день в это время ты будешь получать сводку задач на день:"
    ),
    "digest_time_set":      "✅ Дайджест будет приходить в <b>{time}</b>",
    "onboarding_done":      (
        "🎉 <b>Всё готово!</b>\n\n"
        "Теперь ты можешь добавлять задачи текстом или голосом,\n"
        "просматривать расписание и отслеживать продуктивность.\n\n"
        "Попробуй добавить первую задачу!"
    ),

    # ── Main menu ────────────────────────────────────────────────
    "main_menu":            "📱 Главное меню",
    "btn_today":            "📅 Сегодня",
    "btn_schedule":         "📆 Расписание",
    "btn_add_task":         "✏️ Добавить задачу",
    "btn_stats":            "📊 Статистика",
    "btn_habits":           "🔥 Привычки",
    "btn_settings":         "⚙️ Настройки",
    "btn_premium":          "⭐ Premium",

    # ── Task creation ────────────────────────────────────────────
    "add_task_prompt":      "✏️ Просто напиши задачу — я сам всё разберу!",
    "btn_quick_add":        "⚡ Быстро (текстом)",  # unused
    "btn_step_add":         "📝 Пошагово",  # unused
    "btn_voice_add":        "🎤 Голосом (Premium)",
    "voice_premium_upsell": "🎤 Голосовой ввод доступен в <b>Premium</b>.\n\nПолучи Premium и добавляй задачи голосом!",
    "quick_add_prompt":     "✏️ Напиши задачу — я сам разберусь с датой, временем и приоритетом:",
    "parsing_task":         "⏳ Разбираю задачу...",
    "task_parsed":          (
        "📋 <b>Проверь задачу:</b>\n\n"
        "📌 <b>{title}</b>\n"
        "📅 {date}\n"
        "{time_line}"
        "{priority_line}"
        "{category_line}"
        "{remind_line}"
    ),
    "task_saved":           "✅ Задача добавлена!",
    "task_parse_failed":    (
        "🤔 Не смог разобрать задачу автоматически.\n"
        "Давай добавим пошагово:"
    ),
    "btn_save_task":        "✅ Сохранить",
    "btn_edit_task":        "✏️ Изменить",
    "btn_cancel":           "❌ Отмена",

    # Step-by-step FSM
    "step_title":           "📝 <b>Название задачи:</b>",
    "step_date":            "📅 <b>На какой день?</b>",
    "step_time":            "🕐 <b>Время выполнения?</b>",
    "step_remind":          "🔔 <b>Напомнить?</b>",
    "step_category":        "📌 <b>Категория?</b>",
    "step_priority":        "🔴 <b>Приоритет?</b>",
    "btn_today_date":       "📅 Сегодня",
    "btn_tomorrow_date":    "📅 Завтра",
    "btn_choose_date":      "📆 Выбрать дату",
    "btn_morning":          "🌅 Утро (9:00)",
    "btn_noon":             "☀️ День (13:00)",
    "btn_evening":          "🌆 Вечер (19:00)",
    "btn_no_time":          "⏰ Без времени",
    "btn_custom_time":      "🕐 Своё время",
    "ask_custom_time":      "Введи время в формате <b>ЧЧ:ММ</b>, например: 14:30",
    "invalid_time":         "❌ Неверный формат. Введи время как <b>ЧЧ:ММ</b>:",
    "ask_custom_date":      "Введи дату в формате <b>ДД.ММ</b> или <b>ДД.ММ.ГГГГ</b>:",
    "invalid_date":         "❌ Неверная дата. Попробуй ещё раз:",
    "btn_remind_30":        "🔔 За 30 мин",
    "btn_remind_10":        "🔔 За 10 мин",
    "btn_remind_60":        "🔔 За 1 час",
    "btn_remind_custom":    "🔔 Своё время",
    "btn_set_remind":       "🔔 Напомнить заранее",
    "btn_remove_remind":    "🔕 Убрать напоминание",
    "btn_edit_title":       "Изменить текст",
    "btn_no_remind":        "🔕 Не нужно",
    "btn_priority_high":    "🔴 Высокий",
    "btn_priority_medium":  "🟡 Средний",
    "btn_priority_low":     "🟢 Низкий",

    # ── Schedule view ────────────────────────────────────────────
    "schedule_header":      "📅 <b>{weekday}, {date}</b>",
    "schedule_morning":     "🌅 <b>УТРО</b>",
    "schedule_day":         "☀️ <b>ДЕНЬ</b>",
    "schedule_evening":     "🌆 <b>ВЕЧЕР</b>",
    "schedule_no_time":     "📋 <b>БЕЗ ВРЕМЕНИ</b>",
    "schedule_empty":       "😊 На этот день задач нет.\n\nДобавь первую задачу!",
    "schedule_footer":      "\n──────────────────\n✅ {done}/{total} задач выполнено",
    "btn_prev_day":         "◀ Вчера",
    "btn_next_day":         "Завтра ▶",
    "btn_back_today":       "📅 Сегодня",

    # Task card
    "task_card":            (
        "{priority_emoji} <b>{title}</b>\n\n"
        "📅 {date}{time_part}\n"
        "{category_line}"
        "{remind_line}"
        "{recurrence_line}"
    ),
    "btn_done":             "✅ Выполнено",
    "btn_skip":             "⏭ Пропустить",
    "btn_edit":             "✏️ Изменить",
    "btn_delete":           "🗑 Удалить",
    "btn_back":             "◀ Назад",
    "task_done_msg":        "✅ Отлично! Задача выполнена! 🎉",
    "task_skipped_msg":     "⏭ Задача пропущена.",
    "task_deleted_msg":     "🗑 Задача удалена.",
    "task_undo":            "Отменить",
    "task_restored":        "↩️ Задача восстановлена.",
    "confirm_delete":       "❓ Удалить задачу <b>{title}</b>?",
    "btn_confirm_delete":   "🗑 Да, удалить",

    # ── Stats ────────────────────────────────────────────────────
    "stats_header":         "📊 <b>Статистика</b>",
    "stats_period":         "Период: <b>{period}</b>",
    "stats_streak":         "🔥 Стрик: <b>{days} дн. подряд</b>",
    "stats_streak_none":    "🔥 Стрик: начни сегодня!",
    "stats_completion":     "📈 Выполнение: <b>{pct}%</b>  ({done}/{total} задач)",
    "stats_best_day":       "⭐ Лучший день: <b>{day}</b> ({pct}%)",
    "stats_by_category":    "📌 <b>По категориям:</b>",
    "stats_by_weekday":     "📅 <b>По дням недели:</b>",
    "stats_empty":          "📊 Пока нет данных. Выполни первые задачи!",
    "btn_stats_7d":         "7 дней",
    "btn_stats_30d":        "30 дней",
    "btn_stats_90d":        "90 дней ⭐",
    "stats_premium_hint":   "⭐ История за 30/90 дней доступна в Premium",

    # ── Settings ─────────────────────────────────────────────────
    "settings_menu":        (
        "⚙️ <b>Настройки</b>\n\n"
        "🌍 Язык: <b>{language}</b>\n"
        "📍 Город: <b>{city}</b>\n"
        "🕐 Часовой пояс: <b>{timezone}</b>\n"
        "🌅 Утренний дайджест: <b>{digest_time}</b>\n"
        "🌙 Вечерняя сводка: <b>{evening}</b>"
    ),
    "btn_change_language":  "🌍 Изменить язык",
    "btn_change_city":      "📍 Изменить город",
    "btn_change_digest":    "🌅 Время дайджеста",
    "btn_toggle_evening":   "🌙 Вечерняя сводка: {state}",
    "evening_on":           "включена ✅",
    "evening_off":          "выключена ❌",
    "city_updated":         "✅ Город обновлён: <b>{city}</b>\nЧасовой пояс: <b>{timezone}</b>",
    "digest_updated":       "✅ Дайджест будет приходить в <b>{time}</b>",

    # ── Habits (Premium) ─────────────────────────────────────────
    "habits_premium_only":  (
        "🔥 <b>Трекер привычек</b> — функция Premium.\n\n"
        "Отслеживай ежедневные привычки, стрики и прогресс!\n\n"
        "Получи Premium чтобы разблокировать:"
    ),
    "habits_menu":          "🔥 <b>Привычки</b>\n\nОтслеживай ежедневные привычки:",
    "no_habits":            "Привычек пока нет. Добавь первую!",
    "btn_add_habit":        "➕ Добавить привычку",
    "habit_ask_title":      "📝 Название привычки (например: «Зарядка», «Читать 30 мин»):",
    "habit_ask_emoji":      "😊 Выбери эмодзи для привычки:",
    "habit_ask_freq":       "📅 Как часто?",
    "btn_habit_daily":      "📅 Каждый день",
    "btn_habit_weekdays":   "💼 По будням",
    "btn_habit_weekly":     "📆 Раз в неделю",
    "habit_ask_time":       "🔔 Напоминание? Введи время (ЧЧ:ММ) или пропусти:",
    "btn_skip_remind":      "⏭ Без напоминания",
    "habit_saved":          "✅ Привычка <b>{title}</b> добавлена!",
    "habit_done":           "✅ Отмечено! Продолжай в том же духе! 🔥",
    "habit_streak":         "🔥 Стрик: <b>{days} дн.</b>",

    # ── Premium ──────────────────────────────────────────────────
    "premium_menu":         (
        "⭐ <b>PlannerBot Premium</b>\n\n"
        "<b>Что входит:</b>\n"
        "✅ Безлимитные задачи (у тебя сейчас лимит 10/день)\n"
        "✅ Голосовой ввод задач 🎤\n"
        "✅ Повторяющиеся задачи\n"
        "✅ До 5 напоминаний на задачу\n"
        "✅ Статистика за 90 дней\n"
        "✅ Трекер привычек 🔥\n"
        "✅ Совместные списки задач 👥\n"
        "✅ Экспорт в Google Calendar\n"
        "✅ AI-персонализированный дайджест\n\n"
        "💎 <b>7 дней бесплатно</b> при первой оплате!"
    ),
    "premium_active":       (
        "✅ <b>Premium активен</b>\n\n"
        "Действует до: <b>{until}</b>\n\n"
        "Спасибо, что используешь Premium! 🙏"
    ),
    "btn_month_stars":      "⭐ {stars} Stars / месяц",
    "btn_year_stars":       "⭐ {stars} Stars / год (−58%)",
    "btn_month_rub":        "💳 199 ₽ / месяц",
    "btn_year_rub":         "💳 990 ₽ / год (−58%)",
    "btn_pay_stars":        "⭐ Telegram Stars",
    "btn_pay_card":         "💳 Картой (ЮKassa)",
    "premium_trial_hint":   "🎁 Первые 7 дней — бесплатно!",
    "payment_processing":   "⏳ Обрабатываю платёж...",
    "payment_success":      "🎉 <b>Premium активирован!</b>\n\nДействует до: <b>{until}</b>",
    "payment_failed":       "❌ Платёж не прошёл. Попробуй ещё раз.",
    "premium_upsell":       (
        "⭐ Эта функция доступна в <b>Premium</b>.\n\n"
        "Разблокируй голосовой ввод, привычки, совместные списки и многое другое!"
    ),
    "btn_get_premium":      "⭐ Получить Premium",

    # ── Digest ───────────────────────────────────────────────────
    "digest_morning":       (
        "🌅 <b>Доброе утро!</b> Вот твой день:\n\n"
        "📅 <b>{weekday}, {date}</b>\n\n"
        "📋 Задач на сегодня: <b>{total}</b>\n"
        "{task_lines}\n"
        "{streak_line}"
    ),
    "digest_evening":       (
        "🌙 <b>Итоги дня</b>\n\n"
        "✅ Выполнено: <b>{done}</b> из <b>{total}</b>\n"
        "📊 Результат: <b>{pct}%</b>\n\n"
        "{streak_line}"
        "\nДо завтра! 😊"
    ),
    "digest_streak":        "🔥 Стрик: <b>{days} дн.</b> подряд!",
    "digest_no_streak":     "💪 Начни стрик — выполни хотя бы одну задачу сегодня!",
    "digest_empty":         "😊 На сегодня задач нет. Добавь первую!",
    "btn_open_today":       "📅 Открыть расписание",

    # ── Workspaces (Premium) ─────────────────────────────────────
    "workspaces_menu":      "👥 <b>Совместные списки</b>",
    "no_workspaces":        "Совместных списков нет.\nСоздай первый или присоединись по коду.",
    "btn_create_workspace": "➕ Создать список",
    "btn_join_workspace":   "🔗 Войти по коду",
    "workspace_ask_name":   "📝 Название совместного списка (например: «Семья», «Команда»):",
    "workspace_created":    (
        "✅ Список <b>{name}</b> создан!\n\n"
        "🔗 Код для приглашения: <code>{code}</code>\n"
        "Поделись ссылкой: {link}"
    ),
    "workspace_ask_code":   "🔗 Введи код приглашения:",
    "workspace_joined":     "✅ Ты присоединился к <b>{name}</b>!",
    "workspace_not_found":  "❌ Список с таким кодом не найден.",

    # ── General ──────────────────────────────────────────────────
    "error_generic":        "❌ Что-то пошло не так. Попробуй ещё раз.",
    "action_cancelled":     "❌ Действие отменено.",
    "not_implemented":      "🚧 Функция в разработке. Скоро появится!",

    # Weekday names
    "weekday_0": "Понедельник",
    "weekday_1": "Вторник",
    "weekday_2": "Среда",
    "weekday_3": "Четверг",
    "weekday_4": "Пятница",
    "weekday_5": "Суббота",
    "weekday_6": "Воскресенье",

    # Month names (short)
    "month_1":  "янв", "month_2":  "фев", "month_3":  "мар",
    "month_4":  "апр", "month_5":  "май", "month_6":  "июн",
    "month_7":  "июл", "month_8":  "авг", "month_9":  "сен",
    "month_10": "окт", "month_11": "ноя", "month_12": "дек",
}
