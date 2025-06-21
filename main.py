import asyncio
import logging
import os
from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types # Добавлены типы для хендлеров
from aiogram.enums import ParseMode # Для DefaultBotProperties
from aiogram.webhook.aiohttp_server import setup_application # Для настройки вебхука

# =========================================================
# ВНИМАНИЕ: ЭТОТ КОД ПРЕДСТАВЛЯЕТ АЛЬТЕРНАТИВНУЮ АРХИТЕКТУРУ.
# ОН НЕ СОВМЕСТИМ С ВАШИМ ОСНОВНЫМ ПРОЕКТОМ БЕЗ ПОЛНОЙ ПЕРЕСТРОЙКИ.
# ИСПОЛЬЗУЙТЕ ЕГО ТОЛЬКО ЕСЛИ ВЫ ХОТИТЕ ПОЛНОСТЬЮ ИЗМЕНИТЬ СТРУКТУРУ.
# =========================================================

# Загружаем переменные окружения
load_dotenv()

# Конфигурация из.env
PORT = int(os.getenv("PORT", 8080))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "") # Это должен быть URL вашего Render/Cloud Run сервиса
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") # Используем TELEGRAM_BOT_TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
# В этой альтернативной структуре, bot_app будет экземпляром Dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
bot_app = Dispatcher() # bot_app теперь является диспетчером

# =========================================================
# ПЛЕЙСХОЛДЕРЫ ДЛЯ ВАШИХ ХЕНДЛЕРОВ
# В реальном проекте это были бы импорты из handlers/*.py
# и их роутеры были бы включены в bot_app.
# =========================================================

# Пример хендлера для демонстрации
@bot_app.message(types.Command(commands=["start"]))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я тестовый бот (из альтернативной структуры).")

# Функция для настройки хендлеров (в этой структуре)
def setup_handlers(dispatcher_instance: Dispatcher):
    # Здесь вы бы включали все ваши роутеры из папки handlers
    # Например:
    # from handlers.store_registration import router as store_registration_router
    # dispatcher_instance.include_router(store_registration_router)
    # И так далее для всех ваших роутеров.
    # В данном случае, мы просто включаем сам bot_app, который уже содержит cmd_start
    dispatcher_instance.include_router(bot_app)
    logger.info("Хендлеры настроены.")


async def on_startup(app: web.Application):
    logger.info("🔁 Запуск бота и установка вебхука...")
    # setup_handlers(app["dp"]) # app["dp"] будет диспетчером
    # Убедитесь, что bot_app (диспетчер) и bot (экземпляр Bot) доступны
    setup_handlers(app["dispatcher"]) # Передаем диспетчер
    await app["bot"].set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
    logger.info("✅ Вебхук установлен!")

async def on_shutdown(app: web.Application):
    logger.info("🛑 Остановка бота...")
    await app["bot"].session.close()

# Этот handle_webhook не нужен, так как setup_application его создает
# async def handle_webhook(request: web.Request):
#     update_data = await request.json()
#     await bot_app.feed_update(bot_app.bot, update_data)
#     return web.Response()

def main():
    app = web.Application()
    
    # ИСПРАВЛЕНО: Использование setup_application из aiogram
    # Это настраивает маршрут /webhook автоматически
    setup_application(app, bot_app, bot=bot, path=WEBHOOK_PATH) # Передаем bot_app как диспетчер
    
    # Добавляем bot и dispatcher в приложение aiohttp для доступа в on_startup/on_shutdown
    app["bot"] = bot
    app["dispatcher"] = bot_app # Добавляем диспетчер под ключом "dispatcher"

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    logger.info(f"🌐 Запуск aiohttp сервера на порту {PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT, print=None)

if __name__ == "__main__":
    main()
