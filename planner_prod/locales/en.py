# All English UI strings for PlannerBot

STRINGS: dict[str, str] = {
    # ── Onboarding ──────────────────────────────────────────────
    "choose_language":      "🌍 Выбери язык / Choose language:",
    "lang_set":             "✅ Language set: English",
    "welcome_new":          (
        "👋 Hi! I'm <b>PlannerBot</b> — your personal daily planner in Telegram.\n\n"
        "I'll help you:\n"
        "📋 Plan your day and tasks\n"
        "🔔 Remind you about important things\n"
        "📊 Track your productivity\n\n"
        "Let's set up in 1 minute!"
    ),
    "ask_city":             (
        "🌍 <b>Enter your city</b>\n\n"
        "This is needed for the correct timezone.\n"
        "Type your city name:"
    ),
    "city_not_found":       "❌ City not found. Please try again:",
    "city_found":           "✅ City: <b>{city}</b>\nTimezone: <b>{timezone}</b>",
    "ask_digest_time":      (
        "🌅 <b>When should I send your morning digest?</b>\n\n"
        "Every day at this time you'll get a summary of tasks:"
    ),
    "digest_time_set":      "✅ Digest will arrive at <b>{time}</b>",
    "onboarding_done":      (
        "🎉 <b>All set!</b>\n\n"
        "You can now add tasks by text or voice,\n"
        "view your schedule and track productivity.\n\n"
        "Try adding your first task!"
    ),

    # ── Main menu ────────────────────────────────────────────────
    "main_menu":            "📱 Main Menu",
    "btn_today":            "📅 Today",
    "btn_schedule":         "📆 Schedule",
    "btn_add_task":         "✏️ Add Task",
    "btn_stats":            "📊 Statistics",
    "btn_habits":           "🔥 Habits",
    "btn_settings":         "⚙️ Settings",
    "btn_premium":          "⭐ Premium",

    # ── Task creation ────────────────────────────────────────────
    "add_task_prompt":      "✏️ Just write a task — I'll figure everything out!",
    "btn_quick_add":        "⚡ Quick (type it)",
    "btn_step_add":         "📝 Step by step",
    "btn_voice_add":        "🎤 Voice (Premium)",
    "voice_premium_upsell": "🎤 Voice input is available in <b>Premium</b>.\n\nUpgrade to add tasks by voice!",
    "quick_add_prompt":     "✏️ Write your task. I'll figure out the date, time and priority:",
    "parsing_task":         "⏳ Parsing your task...",
    "task_parsed":          (
        "📋 <b>Check your task:</b>\n\n"
        "📌 <b>{title}</b>\n"
        "📅 {date}\n"
        "{time_line}"
        "{priority_line}"
        "{category_line}"
        "{remind_line}"
    ),
    "task_saved":           "✅ Task added!",
    "task_parse_failed":    (
        "🤔 Couldn't parse the task automatically.\n"
        "Let's add it step by step:"
    ),
    "btn_save_task":        "✅ Save",
    "btn_edit_task":        "✏️ Edit",
    "btn_cancel":           "❌ Cancel",

    # Step-by-step FSM
    "step_title":           "📝 <b>Task title:</b>",
    "step_date":            "📅 <b>Which day?</b>",
    "step_time":            "🕐 <b>What time?</b>",
    "step_remind":          "🔔 <b>Set a reminder?</b>",
    "step_category":        "📌 <b>Category?</b>",
    "step_priority":        "🔴 <b>Priority?</b>",
    "btn_today_date":       "📅 Today",
    "btn_tomorrow_date":    "📅 Tomorrow",
    "btn_choose_date":      "📆 Choose date",
    "btn_morning":          "🌅 Morning (9:00)",
    "btn_noon":             "☀️ Afternoon (1:00 PM)",
    "btn_evening":          "🌆 Evening (7:00 PM)",
    "btn_no_time":          "⏰ No time",
    "btn_custom_time":      "🕐 Custom time",
    "ask_custom_time":      "Enter time in <b>HH:MM</b> format, e.g. 14:30:",
    "invalid_time":         "❌ Invalid format. Enter time as <b>HH:MM</b>:",
    "ask_custom_date":      "Enter date as <b>DD.MM</b> or <b>DD.MM.YYYY</b>:",
    "invalid_date":         "❌ Invalid date. Try again:",
    "btn_remind_30":        "🔔 30 min before",
    "btn_remind_10":        "🔔 10 min before",
    "btn_remind_60":        "🔔 1 hour before",
    "btn_remind_custom":    "🔔 Custom time",
    "btn_set_remind":       "🔔 Remind before",
    "btn_remove_remind":    "🔕 Remove reminder",
    "btn_edit_title":       "Edit text",
    "btn_no_remind":        "🔕 No reminder",
    "btn_priority_high":    "🔴 High",
    "btn_priority_medium":  "🟡 Medium",
    "btn_priority_low":     "🟢 Low",

    # ── Schedule view ────────────────────────────────────────────
    "schedule_header":      "📅 <b>{weekday}, {date}</b>",
    "schedule_morning":     "🌅 <b>MORNING</b>",
    "schedule_day":         "☀️ <b>AFTERNOON</b>",
    "schedule_evening":     "🌆 <b>EVENING</b>",
    "schedule_no_time":     "📋 <b>ALL DAY</b>",
    "schedule_empty":       "😊 No tasks for this day.\n\nAdd your first task!",
    "schedule_footer":      "\n──────────────────\n✅ {done}/{total} tasks done",
    "btn_prev_day":         "◀ Yesterday",
    "btn_next_day":         "Tomorrow ▶",
    "btn_back_today":       "📅 Today",

    # Task card
    "task_card":            (
        "{priority_emoji} <b>{title}</b>\n\n"
        "📅 {date}{time_part}\n"
        "{category_line}"
        "{remind_line}"
        "{recurrence_line}"
    ),
    "btn_done":             "✅ Done",
    "btn_skip":             "⏭ Skip",
    "btn_edit":             "✏️ Edit",
    "btn_delete":           "🗑 Delete",
    "btn_back":             "◀ Back",
    "task_done_msg":        "✅ Great job! Task completed! 🎉",
    "task_skipped_msg":     "⏭ Task skipped.",
    "task_deleted_msg":     "🗑 Task deleted.",
    "task_undo":            "Undo",
    "task_restored":        "↩️ Task restored.",
    "confirm_delete":       "❓ Delete task <b>{title}</b>?",
    "btn_confirm_delete":   "🗑 Yes, delete",

    # ── Stats ────────────────────────────────────────────────────
    "stats_header":         "📊 <b>Statistics</b>",
    "stats_period":         "Period: <b>{period}</b>",
    "stats_streak":         "🔥 Streak: <b>{days} days</b> in a row",
    "stats_streak_none":    "🔥 Streak: start today!",
    "stats_completion":     "📈 Completion: <b>{pct}%</b>  ({done}/{total} tasks)",
    "stats_best_day":       "⭐ Best day: <b>{day}</b> ({pct}%)",
    "stats_by_category":    "📌 <b>By category:</b>",
    "stats_by_weekday":     "📅 <b>By weekday:</b>",
    "stats_empty":          "📊 No data yet. Complete your first tasks!",
    "btn_stats_7d":         "7 days",
    "btn_stats_30d":        "30 days",
    "btn_stats_90d":        "90 days ⭐",
    "stats_premium_hint":   "⭐ 30/90-day history is available in Premium",

    # ── Settings ─────────────────────────────────────────────────
    "settings_menu":        (
        "⚙️ <b>Settings</b>\n\n"
        "🌍 Language: <b>{language}</b>\n"
        "📍 City: <b>{city}</b>\n"
        "🕐 Timezone: <b>{timezone}</b>\n"
        "🌅 Morning digest: <b>{digest_time}</b>\n"
        "🌙 Evening summary: <b>{evening}</b>"
    ),
    "btn_change_language":  "🌍 Change language",
    "btn_change_city":      "📍 Change city",
    "btn_change_digest":    "🌅 Digest time",
    "btn_toggle_evening":   "🌙 Evening digest: {state}",
    "evening_on":           "on ✅",
    "evening_off":          "off ❌",
    "city_updated":         "✅ City updated: <b>{city}</b>\nTimezone: <b>{timezone}</b>",
    "digest_updated":       "✅ Digest will arrive at <b>{time}</b>",

    # ── Habits (Premium) ─────────────────────────────────────────
    "habits_premium_only":  (
        "🔥 <b>Habit Tracker</b> is a Premium feature.\n\n"
        "Track daily habits, streaks and progress!\n\n"
        "Get Premium to unlock:"
    ),
    "habits_menu":          "🔥 <b>Habits</b>\n\nTrack your daily habits:",
    "no_habits":            "No habits yet. Add your first one!",
    "btn_add_habit":        "➕ Add habit",
    "habit_ask_title":      "📝 Habit name (e.g. «Workout», «Read 30 min»):",
    "habit_ask_emoji":      "😊 Choose an emoji for this habit:",
    "habit_ask_freq":       "📅 How often?",
    "btn_habit_daily":      "📅 Every day",
    "btn_habit_weekdays":   "💼 Weekdays only",
    "btn_habit_weekly":     "📆 Once a week",
    "habit_ask_time":       "🔔 Reminder? Enter time (HH:MM) or skip:",
    "btn_skip_remind":      "⏭ No reminder",
    "habit_saved":          "✅ Habit <b>{title}</b> added!",
    "habit_done":           "✅ Logged! Keep it up! 🔥",
    "habit_streak":         "🔥 Streak: <b>{days} days</b>",

    # ── Premium ──────────────────────────────────────────────────
    "premium_menu":         (
        "⭐ <b>PlannerBot Premium</b>\n\n"
        "<b>What's included:</b>\n"
        "✅ Unlimited tasks (you have 10/day limit now)\n"
        "✅ Voice task input 🎤\n"
        "✅ Recurring tasks\n"
        "✅ Up to 5 reminders per task\n"
        "✅ 90-day statistics\n"
        "✅ Habit tracker 🔥\n"
        "✅ Shared task lists 👥\n"
        "✅ Google Calendar export\n"
        "✅ AI-personalised daily digest\n\n"
        "💎 <b>7 days free</b> on your first payment!"
    ),
    "premium_active":       (
        "✅ <b>Premium is active</b>\n\n"
        "Valid until: <b>{until}</b>\n\n"
        "Thank you for using Premium! 🙏"
    ),
    "btn_month_stars":      "⭐ {stars} Stars / month",
    "btn_year_stars":       "⭐ {stars} Stars / year (−58%)",
    "btn_month_rub":        "💳 199 ₽ / month",
    "btn_year_rub":         "💳 990 ₽ / year (−58%)",
    "btn_pay_stars":        "⭐ Telegram Stars",
    "btn_pay_card":         "💳 Card (YooKassa)",
    "premium_trial_hint":   "🎁 First 7 days — free!",
    "payment_processing":   "⏳ Processing payment...",
    "payment_success":      "🎉 <b>Premium activated!</b>\n\nValid until: <b>{until}</b>",
    "payment_failed":       "❌ Payment failed. Please try again.",
    "premium_upsell":       (
        "⭐ This feature is available in <b>Premium</b>.\n\n"
        "Unlock voice input, habits, shared lists and much more!"
    ),
    "btn_get_premium":      "⭐ Get Premium",

    # ── Digest ───────────────────────────────────────────────────
    "digest_morning":       (
        "🌅 <b>Good morning!</b> Here's your day:\n\n"
        "📅 <b>{weekday}, {date}</b>\n\n"
        "📋 Tasks today: <b>{total}</b>\n"
        "{task_lines}\n"
        "{streak_line}"
    ),
    "digest_evening":       (
        "🌙 <b>Day Summary</b>\n\n"
        "✅ Completed: <b>{done}</b> of <b>{total}</b>\n"
        "📊 Result: <b>{pct}%</b>\n\n"
        "{streak_line}"
        "\nGoodnight! 😊"
    ),
    "digest_streak":        "🔥 Streak: <b>{days} days</b> in a row!",
    "digest_no_streak":     "💪 Start a streak — complete at least one task today!",
    "digest_empty":         "😊 No tasks today. Add your first one!",
    "btn_open_today":       "📅 Open schedule",

    # ── Workspaces (Premium) ─────────────────────────────────────
    "workspaces_menu":      "👥 <b>Shared Lists</b>",
    "no_workspaces":        "No shared lists yet.\nCreate one or join with a code.",
    "btn_create_workspace": "➕ Create list",
    "btn_join_workspace":   "🔗 Join with code",
    "workspace_ask_name":   "📝 Name of the shared list (e.g. «Family», «Team»):",
    "workspace_created":    (
        "✅ List <b>{name}</b> created!\n\n"
        "🔗 Invite code: <code>{code}</code>\n"
        "Share link: {link}"
    ),
    "workspace_ask_code":   "🔗 Enter invite code:",
    "workspace_joined":     "✅ You joined <b>{name}</b>!",
    "workspace_not_found":  "❌ No list found with that code.",

    # ── General ──────────────────────────────────────────────────
    "error_generic":        "❌ Something went wrong. Please try again.",
    "action_cancelled":     "❌ Action cancelled.",
    "not_implemented":      "🚧 Feature coming soon!",

    # Weekday names
    "weekday_0": "Monday",
    "weekday_1": "Tuesday",
    "weekday_2": "Wednesday",
    "weekday_3": "Thursday",
    "weekday_4": "Friday",
    "weekday_5": "Saturday",
    "weekday_6": "Sunday",

    # Month names (short)
    "month_1":  "Jan", "month_2":  "Feb", "month_3":  "Mar",
    "month_4":  "Apr", "month_5":  "May", "month_6":  "Jun",
    "month_7":  "Jul", "month_8":  "Aug", "month_9":  "Sep",
    "month_10": "Oct", "month_11": "Nov", "month_12": "Dec",
}
