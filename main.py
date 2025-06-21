import os
import logging
import sys

# Добавьте родительскую директорию в Python-путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
from aiohttp import web
# ИСПРАВЛЕНО: Убрано get_new_configured_app из импорта
from aiogram.webhook.aiohttp_server import setup_application

# Импортируем конфигурацию и инициализацию базы данных
from config.config import TELEGRAM_BOT_TOKEN, WEBHOOK_URL, ENV, DB_FILE
from db.db import init_db

# Загрузка переменных окружения: только для локальной среды
if ENV == "local":
    load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# --- Подключение роутеров ---
from handlers.store_registration import router as store_registration_router
from handlers.part_request import router as part_request_router
from handlers.part_multi_request import router as part_multi_request_router
from handlers.my_info import router as my_info_router
from handlers.my_requests import router as my_requests_router
from handlers.responses_handler import router as responses_handler_router
from handlers.select_offer import router as select_offer_router
from handlers.store_info import router as store_info_router
from handlers.stock_upload import router as stock_upload_router
from handlers.vin_ocr import router as vin_ocr_router
from handlers.contact import router as contact_router
from handlers.help import router as help_router

dp.include_router(store_registration_router)
dp.include_router(part_request_router)
dp.include_router(part_multi_request_router)
dp.include_router(my_info_router)
dp.include_router(my_requests_router)
dp.include_router(responses_handler_router)
dp.include_router(select_offer_router)
dp.include_router(store_info_router)
dp.include_router(stock_upload_router)
dp.include_router(vin_ocr_router)
dp.include_router(contact_router)
dp.include_router(help_router)

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

from handlers.menu import router as menu_router
dp.include_router(menu_router)

async def on_startup_tasks(dispatcher_instance: Dispatcher):
    logger.info("Database initialiseren...")
    await init_db()
    logger.info("Database geïnitialiseerd.")

async def main_loop():
    if ENV == "local":
        await on_startup_tasks(dp)
        await dp.start_polling(bot)
    elif ENV == "cloud":
        logger.info("Starten in Webhook-modus (Cloud Run)...")
        
        # ИСПРАВЛЕНО: Ручное создание aiohttp.web.Application
        app = web.Application()
        # ИСПРАВЛЕНО: Передача app в setup_application
        setup_application(app, dp, bot=bot, path="/webhook")
        
        # Добавляем задачи, которые должны запуститься при старте приложения
        app.on_startup.append(lambda app_instance: asyncio.create_task(on_startup_tasks(app_instance["dp"])))

        # Health check route (опционально)
        async def health_check_route(request):
            return web.Response(text="Bot draait!")
        app.router.add_get("/", health_check_route)

        port = int(os.getenv("PORT", 8080))
        host = '0.0.0.0'
        
        logger.info(f"Веб-сервер будет запущен на {host}:{port}")
        
        # Запускаем aiohttp-приложение
        await web.run_app(app, host=host, port=port, print=None)
        
if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logger.info("Bot handmatig gestopt.")
    except Exception as e:
        logger.error(f"Er is een fatale fout opgetreden: {e}", exc_info=True)
