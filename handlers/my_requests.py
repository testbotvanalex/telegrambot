from aiogram import types, Router, F
from db.db import get_requests_by_store # ИСПРАВЛЕНО: from db.db
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums.parse_mode import ParseMode

router = Router()

@router.message(F.text == "📄 Mes demandes")
async def my_requests_handler(message: types.Message):
    requests = await get_requests_by_store(message.from_user.id)

    if not requests:
        await message.answer("🔎 Vous n’avez encore fait aucune demande.")
        return

    for req in requests:
        text = (
            f"📦 <b>Demande #{req['id']}</b>\n"
            f"🚗 <b>Véhicule:</b> {req['car']}\n"
            f"🔧 <b>Pièce:</b> {req['part_name']}\n"
            f"📅 <b>Date:</b> {req['requested_at'][:16].replace('T', ' ')}"
        )
        # Убедитесь, что callback_data здесь соответствует той, что обрабатывается в handlers.view_responses
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="🔍 Voir les réponses",
                callback_data=f"view_offers:{req['id']}"
            )
        ]])
        await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
