import os
import logging
from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import setup_application
import openai

# 🔧 Загрузка переменных окружения
load_dotenv()

PORT = int(os.getenv("PORT", 8080))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ Проверка переменных
if not TELEGRAM_BOT_TOKEN or not WEBHOOK_URL:
    raise RuntimeError("Не заданы TELEGRAM_BOT_TOKEN или WEBHOOK_URL!")

# 🤖 Инициализация бота и OpenAI
bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
openai.api_key = OPENAI_API_KEY

# 🟢 Хендлер: /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("👋 Привет! Я работаю на Google Cloud Run.")

# 🤖 AI-команда: ai: твой текст
@dp.message(lambda message: message.text.lower().startswith("ai:"))
async def ai_handler(message: types.Message):
    prompt = message.text[3:].strip()
    if not prompt:
        await message.answer("❗ Пожалуйста, напиши текст после 'ai:'")
        return
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        reply = response.choices[0].message.content
        await message.answer(reply)
    except Exception as e:
        logging.exception("Ошибка AI:")
        await message.answer("⚠️ Ошибка при обращении к OpenAI.")

# 🔁 Echo и логирование
@dp.message()
async def echo(message: types.Message):
    logging.info(f"📩 От {message.from_user.id}: {message.text}")
    await message.answer(message.text)

# 🧪 Healthcheck для Render/GCP
async def health_check(request):
    return web.Response(text="✅ OK")

# 🔁 Webhook старт/стоп
async def on_startup(app):
    await bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}")
    logging.info(f"Webhook установлен: {WEBHOOK_URL}{WEBHOOK_PATH}")

async def on_shutdown(app):
    await bot.session.close()

# 🚀 Запуск aiohttp
def main():
    logging.basicConfig(level=logging.INFO)
    app = web.Application()
    setup_application(app, dp, bot=bot, path=WEBHOOK_PATH)
    app.router.add_get("/healthz", health_check)
    app["bot"] = bot
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()