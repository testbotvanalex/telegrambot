import asyncio
import logging
import os
from aiohttp import web
from dotenv import load_dotenv # Это не будет работать в Cloud Run, но оставлено для локальной совместимости
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import setup_application

# =========================================================
# ВНИМАНИЕ: ЭТОТ КОД ПРЕДСТАВЛЯЕТ АЛЬТЕРНАТИВНУЮ АРХИТЕКТУРУ.
# ОН НЕ СОВМЕСТИМ С ВАШИМ ОСНОВНЫМ ПРОЕКТОМ БЕЗ ПОЛНОЙ ПЕРЕСТРОЙКИ.
# ИСПОЛЬЗУЙТЕ ЕГО ТОЛЬКО ЕСЛИ ВЫ ХОТИТЕ ПОЛНОСТЬЮ ИЗМЕНИТЬ СТРУКТУРУ.
# =========================================================

# Загружаем переменные окружения
# ВНИМАНИЕ: load_dotenv() НЕ НУЖНА В CLOUD RUN.
# Убедитесь, что все переменные окружения настроены в Cloud Run напрямую.
load_dotenv()

# Конфигурация из .env (или из переменных окружения Cloud Run)
PORT = int(os.getenv("PORT", 8080))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "") # Это должен быть URL вашего Render/Cloud Run сервиса
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") # Используем TELEGRAM_BOT_TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_BOT_TOKEN, default=ParseMode.HTML)
dp = Dispatcher() # Используем 'dp' для главного диспетчера, это общепринято

# =========================================================
# ПЛЕЙСХОЛДЕРЫ ДЛЯ ВАШИХ ХЕНДЛЕРОВ
# В реальном проекте это были бы импорты из handlers/*.py
# и их роутеры были бы включены в dp.
# =========================================================

# Пример хендлера для демонстрации
@dp.message(types.Command(commands=["start"])) # <-- Теперь используем 'dp' напрямую
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я тестовый бот (из альтернативной структуры).")

# Функция setup_handlers теперь может быть удалена или изменена,
# если вы включаете другие роутеры в 'dp' напрямую здесь.
# Например, если у вас есть другие модули с хендлерами:
# from handlers.some_module import router as some_router
# dp.include_router(some_router)


async def on_startup(app: web.Application):
    logger.info("🔁 Запуск бота и установка вебхука...")
    # Здесь мы включаем роутеры в диспетчер.
    # В этом примере, поскольку cmd_start уже зарегистрирован в dp,
    # нам не нужно вызывать include_router(dp).
    # Если бы у вас были отдельные роутеры, вы бы их здесь включали:
    # dp.include_router(your_another_router)
    
    # Aiogram 3 рекомендует использовать метод .start() для диспетчера
    # для запуска Polling или Webhook-сервера
    # Но поскольку мы используем aiohttp и setup_application,
    # webhook устанавливается отдельно.
    
    # Установка вебхука
    await app["bot"].set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
    logger.info("✅ Вебхук установлен!")

async def on_shutdown(app: web.Application):
    logger.info("🛑 Остановка бота...")
    await app["bot"].session.close()

def main():
    app = web.Application()
    
    # setup_application связывает диспетчер с aiohttp приложением
    setup_application(app, dp, bot=bot, path=WEBHOOK_PATH) # Передаем 'dp' как диспетчер
    
    # Добавляем bot и dispatcher в приложение aiohttp для доступа в on_startup/on_shutdown
    app["bot"] = bot
    app["dispatcher"] = dp # Добавляем диспетчер под ключом "dispatcher"

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    logger.info(f"🌐 Запуск aiohttp сервера на порту {PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT, print=None)

if __name__ == "__main__":
    main()
