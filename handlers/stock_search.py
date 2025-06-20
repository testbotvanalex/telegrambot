from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.reply import get_cancel_button
from db.db import search_stock_by_name, get_store_by_telegram_id
from services.ai_correction import correct_part_name # NOUVEAU : Importe la fonction de correction IA

router = Router()

class StockSearch(StatesGroup):
    waiting_for_part_name = State()

@router.message(F.text == "🔎 Rechercher stock")
async def start_stock_search(message: types.Message, state: FSMContext):
    store = await get_store_by_telegram_id(message.from_user.id)
    if not store or not store["approved"]:
        await message.answer("❌ Vous n'êtes pas un magasin approuvé pour effectuer des recherches de stock.")
        return

    await state.clear()
    await message.answer("🔧 Entrez le nom ou le numéro de la pièce que vous recherchez :", reply_markup=get_cancel_button())
    await state.set_state(StockSearch.waiting_for_part_name)

@router.message(StockSearch.waiting_for_part_name, F.text == "❌ Annuler")
async def cancel_stock_search(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Recherche de stock annulée.", reply_markup=ReplyKeyboardRemove())

@router.message(StockSearch.waiting_for_part_name)
async def process_part_name_search(message: types.Message, state: FSMContext):
    raw_query = message.text.strip()
    
    corrected_query = await correct_part_name(raw_query)

    # --- ОТЛАДКА ---
    print(f"DEBUG_STOCK_SEARCH: Исходный запрос: '{raw_query}'")
    print(f"DEBUG_STOCK_SEARCH: Скорректированный запрос от AI: '{corrected_query}'")
    # --- КОНЕЦ ОТЛАДКИ ---

    unrecognized_phrases = ["nom de pièce non reconnu", "terme non identifié", "je ne peux pas corriger", "votre requête est ambiguë"] # Добавлены возможные фразы
    if any(phrase in corrected_query.lower() for phrase in unrecognized_phrases) or not corrected_query.strip() or len(corrected_query.strip()) < 3:
        await message.answer("⚠️ Le terme de recherche n'a pas été reconnu. Veuillez essayer une description plus précise ou vérifier l'orthographe.")
        return

    await message.answer(f"🔎 Recherche de : <b>{corrected_query}</b>...", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    
    results = await search_stock_by_name(corrected_query)

    if not results:
        await message.answer(f"🔎 Aucun article trouvé pour '{corrected_query}'. Veuillez essayer un autre terme de recherche.", reply_markup=ReplyKeyboardRemove())
        await state.clear() # Сброс состояния, если ничего не найдено
        return

    response_text = f"📦 Stock trouvé pour '{corrected_query}' :\n\n"
    for item in results:
        store_info = await get_store_by_telegram_id(item['store_id'])
        store_name = store_info['name'] if store_info else "Magasin inconnu"
        store_contact = store_info.get('contact', 'N/A') if store_info else "N/A"

        response_text += (
            f"🏪 Magasin : <b>{store_name}</b>\n"
            f"🔧 Pièce : {item['part_name']}\n"
            f"🔢 Quantité : {item['quantity']}\n"
            f"💰 Prix : {item.get('price', 'N/A')} €\n"
            f"📞 Contact : {store_contact}\n\n"
        )
    
    await message.answer(response_text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    await state.clear()
