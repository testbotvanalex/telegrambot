import os
import logging
import sys

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
from aiohttp import web
from aiogram.webhook.aiohttp_server import setup_application

# Исправлено: изменен путь импорта для db.init_db
from config.config import TELEGRAM_BOT_TOKEN, WEBHOOK_URL, ENV, DB_FILE
from db.db import init_db

# Загрузка переменных окружения (убедитесь, что .env файл существует)
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# ✅ Подключение роутеров (порядок важен!)
# Примечание: порядок здесь важен для правильной обработки сообщений.
# Более специфичные хендлеры (FSM-состояния, конкретные команды) должны быть выше общих.

# --- Пользовательский функционал ---
from handlers.store_registration import router as store_registration_router
from handlers.part_request import router as part_request_router
from handlers.part_multi_request import router as part_multi_request_router
from handlers.my_info import router as my_info_router
from handlers.my_requests import router as my_requests_router
from handlers.responses_handler import router as responses_handler_router
from handlers.select_offer import router as select_offer_router
from handlers.store_info import router as store_info_router
from handlers.stock_upload import router as stock_upload_router # Добавлено
from handlers.vin_ocr import router as vin_ocr_router
from handlers.contact import router as contact_router # Добавлено
from handlers.help import router as help_router # Добавлено

dp.include_router(store_registration_router)
dp.include_router(part_request_router)
dp.include_router(part_multi_request_router)
dp.include_router(my_info_router)
dp.include_router(my_requests_router)
dp.include_router(responses_handler_router)
dp.include_router(select_offer_router)
dp.include_router(store_info_router)
dp.include_router(stock_upload_router) # Подключено
dp.include_router(vin_ocr_router)
dp.include_router(contact_router) # Подключено
dp.include_router(help_router) # Подключено

# --- Админ-панель (Высокий приоритет) ---
from handlers.admin.admin_dashboard import router as admin_dashboard_router
from handlers.admin.admin_users import router as admin_users_router
from handlers.admin.admin_subscriptions import router as admin_subscriptions_router
from handlers.admin.admin_ads import router as admin_ads_router
from handlers.admin.admin_clients import router as admin_clients_router
from handlers.admin.admin_tools import router as admin_tools_router
from handlers.admin.settings import router as admin_settings_router
from handlers.moderation_queue import router as moderation_queue_router
from handlers.statistics import router as statistics_router

dp.include_router(admin_dashboard_router)
dp.include_router(admin_users_router)
dp.include_router(admin_subscriptions_router)
dp.include_router(admin_ads_router)
dp.include_router(admin_clients_router)
dp.include_router(admin_tools_router)
dp.include_router(admin_settings_router)
dp.include_router(moderation_queue_router)
dp.include_router(statistics_router)

# --- Общее меню (Низкий приоритет, перехватывает все остальное) ---
from handlers.menu import router as menu_router
dp.include_router(menu_router)

# 🚀 Запуск бота
async def on_startup(dispatcher):
    logger.info("🔧 Инициализация БД...")
    await init_db()
    logger.info("БД инициализирована.")
    if ENV == "cloud":
        if not WEBHOOK_URL:
            logger.error("WEBHOOK_URL не установлен для Cloud Run!")
            raise ValueError("WEBHOOK_URL не установлен для Cloud Run!")
        webhook_url_full = f"{WEBHOOK_URL}/webhook"
        logger.info(f"🔗 Установка Webhook: {webhook_url_full}")
        await bot.set_webhook(webhook_url_full)
        logger.info("Webhook установлен.")
    else:
        logger.info("Запуск в режиме Polling...")


async def main_loop():
    if ENV == "local":
        await on_startup(dp)
        await dp.start_polling(bot)
    elif ENV == "cloud":
        logger.info("Запуск в режиме Webhook (Cloud Run)...")
        app = web.Application()
        app["bot"] = bot
        app["dp"] = dp
        setup_application(app, dp, bot=bot, path="/webhook")
        app.on_startup.append(on_startup)
        
        async def health_check(request):
            return web.Response(text="Bot is running!")
        app.router.add_get("/", health_check)

        port = int(os.getenv("PORT", 8080))
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        logger.info(f"Веб-сервер запущен на 0.0.0.0:{port}")
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logger.info("Бот остановлен вручную.")
    except Exception as e:
        logger.error(f"Произошла фатальная ошибка: {e}", exc_info=True)