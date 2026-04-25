# Import order is CRITICAL in aiogram 3.
# Handlers match in registration order — specific button handlers MUST be
# registered BEFORE the universal text interceptor (handlers.tasks), otherwise
# every menu button tap ("📅 Сегодня", "📊 Статистика", etc.) gets swallowed
# by the AI parser instead of opening the correct screen.

import handlers.start      # noqa: F401  /start + onboarding
import handlers.schedule   # noqa: F401  daily schedule   ← before tasks
import handlers.stats      # noqa: F401  statistics       ← before tasks
import handlers.settings   # noqa: F401  user settings    ← before tasks
import handlers.premium    # noqa: F401  payments         ← before tasks
import handlers.habits     # noqa: F401  habit tracker    ← before tasks
import handlers.tasks      # noqa: F401  universal AI interceptor — MUST BE LAST
