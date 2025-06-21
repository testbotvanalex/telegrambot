import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot

# Laad omgevingsvariabelen uit het .env-bestand
# Zorg ervoor dat het .env-bestand zich in dezelfde map bevindt van waaruit u dit script uitvoert
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# WEBHOOK_URL in uw .env-bestand moet de basis-URL van uw Cloud Run-service zijn
WEBHOOK_URL = os.getenv("WEBHOOK_URL") + "/webhook" # Voeg '/webhook' toe aan de basis-URL

async def set_webhook():
    if not TELEGRAM_BOT_TOKEN:
        print("Fout: TELEGRAM_BOT_TOKEN is niet ingesteld in .env")
        return
    if not WEBHOOK_URL:
        print("Fout: WEBHOOK_URL is niet ingesteld in .env")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        await bot.set_webhook(WEBHOOK_URL)
        print(f"Webhook succesvol ingesteld op: {WEBHOOK_URL}")
    except Exception as e:
        print(f"Fout bij het instellen van de webhook: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(set_webhook())
