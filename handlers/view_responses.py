from aiogram import Router, types, F
from aiogram.enums.parse_mode import ParseMode
from db.db import get_offers_by_request_id # ИСПРАВЛЕНО: from db.db

router = Router()

@router.callback_query(F.data.startswith("view_offers:"))
async def view_offers_callback(callback: types.CallbackQuery):
    request_id = int(callback.data.split(":")[1])
    
    # --- ОТЛАДКА ---
    print(f"DEBUG_VR: Получен запрос предложений для request_id: {request_id}")
    offers = await get_offers_by_request_id(request_id)
    print(f"DEBUG_VR: get_offers_by_request_id вернул: {offers}")
    # --- КОНЕЦ ОТЛАДКИ ---

    if not offers:
        await callback.message.edit_text("❌ Aucun magasin n’a encore répondu à cette demande.", parse_mode=ParseMode.HTML)
        await callback.answer()
        return

    response_text = f"📨 Réponses pour la demande #{request_id} :\n\n"
    has_chosen_offer = False
    
    for offer in offers:
        offer_status = ""
        if offer.get('selected'):
            offer_status = " (✅ CHOISI)"
            has_chosen_offer = True

        response_text += (
            f"📦 <b>Réponse d’un magasin</b>{offer_status}\n"
            f"💰 <b>Prix:</b> {offer.get('price', 'N/A')}\n"
            f"⏳ <b>Délai:</b> {offer.get('eta', 'N/A')}\n"
            f"🚚 <b>Livraison:</b> {offer.get('delivery', 'N/A')}\n"
            f"👤 <b>Vendeur:</b> @{offer.get('responder_username', 'Inconnu')}\n\n"
        )
    
    if not has_chosen_offer and offers:
        selection_keyboard = []
        for offer in offers:
            if not offer.get('selected'):
                selection_keyboard.append([
                    InlineKeyboardButton(
                        text=f"✅ Choisir offre {offer.get('price', 'N/A')} € ({offer.get('delivery', 'N/A')})",
                        callback_data=f"choose_offer:{offer['id']}"
                    )
                ])
        if selection_keyboard:
            await callback.message.edit_text(response_text + "\nChoisissez une offre ci-dessous :",
                                             reply_markup=InlineKeyboardMarkup(inline_keyboard=selection_keyboard),
                                             parse_mode=ParseMode.HTML)
        else:
             await callback.message.edit_text(response_text, parse_mode=ParseMode.HTML)
    else:
        await callback.message.edit_text(response_text, parse_mode=ParseMode.HTML)

    await callback.answer()
