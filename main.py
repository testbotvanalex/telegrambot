import os
import logging
from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import setup_application

# 🔧 Загрузка переменных окружения
load_dotenv()
PORT = int(os.getenv("PORT", 8080))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ✅ Проверка
if not TELEGRAM_BOT_TOKEN or not WEBHOOK_URL:
    raise RuntimeError("TELEGRAM_BOT_TOKEN и WEBHOOK_URL должны быть заданы!")

# 🤖 Инициализация
bot = Bot(
    token=TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# 🟢 Хендлеры
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("👋 Привет! Я работаю на Google Cloud Run.")

@dp.message()
async def echo(message: types.Message):
    await message.answer(message.text)

# 🔁 Запуск и остановка
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
    logging.info(f"Webhook установлен на: {WEBHOOK_URL + WEBHOOK_PATH}")

async def on_shutdown(app):
    await bot.session.close()

# 🚀 Запуск
def main():
    logging.basicConfig(level=logging.INFO)
    app = web.Application()
    setup_application(app, dp, bot=bot, path=WEBHOOK_PATH)
    app["bot"] = bot
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()