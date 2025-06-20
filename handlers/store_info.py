from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from db.db import get_store_by_telegram_id # Исправлено: get_store_by_telegram_id вместо get_store_by_user_id

router = Router()

@router.message(Command("info"))
@router.message(F.text == "📝 Mes infos") # Добавлено для кнопки меню
async def show_store_info(message: Message):
    user_id = message.from_user.id
    store = await get_store_by_telegram_id(user_id) # Используем get_store_by_telegram_id

    if not store:
        await message.answer("❗ Vous n’êtes pas encore enregistré.")
        return

    approved = "✅ Oui" if store["approved"] else "⏳ En attente"

    location = (
        f"📍 <b>Localisation:</b> {store['latitude']}, {store['longitude']}"
        if store["latitude"] and store["longitude"] else "📍 <b>Localisation:</b> Aucune"
    )

    text = (
        "<b>📝 Vos informations</b>\n\n"
        f"🏪 <b>Nom:</b> {store['name']}\n"
        f"📍 <b>Adresse:</b> {store['address'] or '—'}\n"
        f"🏙️ <b>Ville:</b> {store['city'] or '—'}\n"
        f"🛠️ <b>Catégories:</b> {store['categories'] or '—'}\n"
        f"📞 <b>Contact:</b> {store['contact'] or '—'}\n"
        f"{location}\n"
        f"🔐 <b>Statut:</b> {approved}"
    )

    await message.answer(text, parse_mode="HTML")
