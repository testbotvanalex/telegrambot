import os
import sys
import logging
import asyncio
from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import get_new_configured_app

# Добавляем путь к проекту (если нужно для ручного запуска)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import TELEGRAM_BOT_TOKEN, WEBHOOK_URL, ENV, DB_FILE
from db.db import init_db

# Загружаем переменные окружения (только локально)
if ENV == "local":
    load_dotenv()

# Настройка логгера
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Роутеры
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
from handlers.menu import router as menu_router

from handlers.admin.admin_dashboard import router as admin_dashboard_router
from handlers.admin.admin_users import router as admin_users_router
from handlers.admin.admin_subscriptions import router as admin_subscriptions_router
from handlers.admin.admin_ads import router as admin_ads_router
from handlers.admin.admin_clients import router as admin_clients_router
from handlers.admin.admin_tools import router as admin_tools_router
from handlers.admin.settings import router as admin_settings_router
from handlers.moderation_queue import router as moderation_queue_router
from handlers.statistics import router as statistics_router

# Регистрируем все роутеры
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
dp.include_router(menu_router)

dp.include_router(admin_dashboard_router)
dp.include_router(admin_users_router)
dp.include_router(admin_subscriptions_router)
dp.include_router(admin_ads_router)
dp.include_router(admin_clients_router)
dp.include_router(admin_tools_router)
dp.include_router(admin_settings_router)
dp.include_router(moderation_queue_router)
dp.include_router(statistics_router)

# Стартовые задачи
async def on_startup_tasks():
    logger.info("Инициализация базы данных...")
    await init_db()
    logger.info("База данных готова.")

# Основной цикл
async def main_loop():
    if ENV == "local":
        await on_startup_tasks()
        await dp.start_polling(bot)
    elif ENV == "cloud":
        logger.info("Запуск в режиме Webhook (Cloud Run)...")
        await on_startup_tasks()

        app = get_new_configured_app(dispatcher=dp, bot=bot, path="/webhook")

        async def health_check_route(request):
            return web.Response(text="Bot draait!")
        app.router.add_get("/", health_check_route)

        port = int(os.getenv("PORT", 8080))
        host = "0.0.0.0"

        logger.info(f"Сервер слушает на {host}:{port}")
        await web.run_app(app, host=host, port=port, print=None)

# Точка входа
if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logger.info("Остановка по Ctrl+C")
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}", exc_info=True)