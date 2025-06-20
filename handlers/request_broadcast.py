from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from db.db import get_approved_stores
import asyncio
from aiogram.enums import ParseMode # Для ParseMode.HTML

# Эта функция НЕ ЯВЛЯЕТСЯ роутером, она вызывается из part_request.py
async def broadcast_request_to_stores(bot: Bot, data: dict):
    requester_id = data["store_id"]
    approved_stores = await get_approved_stores()
    if not approved_stores:
        print("DEBUG_BROADCAST: No approved stores to broadcast to.")
        return

    text = (
        f"🆕 <b>Nouvelle demande de pièce</b>\n\n"
        f"📦 <b>Pièce:</b> {data['part_name']}\n"
        f"🚗 <b>Véhicule:</b> {data['car']}\n"
        f"🔢 <b>Quantité:</b> {data['quantite']}"
    )
    if data.get('vin_code'):
        text += f"\n🧾 <b>VIN:</b> {data['vin_code']}"

    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📦 J’ai cette pièce", callback_data=f"offer:have:{data['id']}"),
            InlineKeyboardButton(text="🕒 Je la reçois bientôt", callback_data=f"offer:soon:{data['id']}"),
            InlineKeyboardButton(text="❌ Je ne l’ai pas", callback_data=f"offer:none:{data['id']}")
        ]
    ])

    tasks = []
    for store in approved_stores:
        if store["telegram_id"] == requester_id:
            continue # Не отправляем запрос тому, кто его создал
        
        try:
            if data.get("photo_file_id"):
                # Если есть фото, отправляем его
                tasks.append(
                    bot.send_photo(
                        chat_id=store["telegram_id"],
                        photo=data["photo_file_id"],
                        caption=text,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML
                    )
                )
            else:
                # Если фото нет, отправляем только текст
                tasks.append(
                    bot.send_message(
                        chat_id=store["telegram_id"],
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML
                    )
                )
        except Exception as e:
            print(f"❌ Erreur en envoyant le broadcast à {store['telegram_id']}: {e}")

    if tasks:
        # Запускаем все задачи параллельно
        await asyncio.gather(*tasks, return_exceptions=True)
    print("✅ Broadcast terminé.")
# Note: Cette fonction broadcast_request_to_stores est utilisée для рассылки запросов на магазины.