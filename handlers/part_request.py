from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from keyboards.skip import skip_vin_kb, skip_photo_kb
from keyboards.menu import get_main_menu
from keyboards.reply import get_cancel_button # Использовать унифицированную кнопку отмены
from keyboards.ai_correct import get_ai_correct_keyboard

from services.ai_correction import correct_part_name # ИСПРАВЛЕНО: импорт из services.ai_correction
from db.db import save_part_request, get_store_by_telegram_id
from handlers.request_broadcast import broadcast_request_to_stores # ИСПРАВЛЕНО: использование новой функции
import textwrap
import asyncio # Для asyncio.sleep

router = Router()

class PartRequest(StatesGroup):
    waiting_for_marque = State()
    waiting_for_modele = State()
    waiting_for_annee = State()
    waiting_for_piece = State()
    waiting_for_quantite = State()
    waiting_for_vin = State()
    waiting_for_photo = State()

@router.message(Command("verzoek"))
@router.message(F.text == "📦 Demander une pièce")
async def start_request(message: Message, state: FSMContext):
    print(f"DEBUG_PR: start_request получил текст: '{message.text}' от пользователя ID: {message.from_user.id}")
    store = await get_store_by_telegram_id(message.from_user.id)
    if not store or not store["approved"]:
        await message.answer("❌ Votre magasin n'est pas encore approuvé pour faire des demandes.")
        return
    await message.answer("🚘 Marque du véhicule :", reply_markup=get_cancel_button())
    await state.set_state(PartRequest.waiting_for_marque)

@router.message(PartRequest.waiting_for_marque, F.text == "❌ Annuler")
@router.message(PartRequest.waiting_for_modele, F.text == "❌ Annuler")
@router.message(PartRequest.waiting_for_annee, F.text == "❌ Annuler")
@router.message(PartRequest.waiting_for_piece, F.text == "❌ Annuler")
@router.message(PartRequest.waiting_for_quantite, F.text == "❌ Annuler")
@router.message(PartRequest.waiting_for_vin, F.text == "❌ Annuler")
@router.message(PartRequest.waiting_for_photo, F.text == "❌ Annuler")
async def cancel_part_request(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Demande de pièce annulée.", reply_markup=ReplyKeyboardRemove())
    # from keyboards.menu import get_main_menu
    # await message.answer("📋 Menu principal:", reply_markup=get_main_menu("store"))


@router.message(PartRequest.waiting_for_marque)
async def get_marque(message: Message, state: FSMContext):
    await state.update_data(marque=message.text)
    await message.answer("📍 Modèle du véhicule :", reply_markup=get_cancel_button())
    await state.set_state(PartRequest.waiting_for_modele)

@router.message(PartRequest.waiting_for_modele)
async def get_modele(message: Message, state: FSMContext):
    await state.update_data(modele=message.text)
    await message.answer("📅 Année du véhicule :", reply_markup=get_cancel_button())
    await state.set_state(PartRequest.waiting_for_annee)

@router.message(PartRequest.waiting_for_annee)
async def get_annee(message: Message, state: FSMContext):
    await state.update_data(annee=message.text)
    await message.answer("🔧 Nom ou numéro de la pièce :", reply_markup=get_cancel_button())
    await state.set_state(PartRequest.waiting_for_piece)

@router.message(PartRequest.waiting_for_piece)
async def get_piece(message: Message, state: FSMContext):
    raw_piece = message.text
    corrected_piece = await correct_part_name(raw_piece)
    
    unrecognized_phrases = ["aucune pièce automobile connue", "veuillez vérifier", "non identifiable", "je ne peux pas corriger"]
    if any(phrase in corrected_piece.lower() for phrase in unrecognized_phrases) or not corrected_piece.strip() or len(corrected_piece.strip()) < 3:
        await message.answer("⚠️ Le nom de pièce n'a pas été reconnu. Veuillez être plus précis ou vérifier l'orthographe.")
        # Остаемся в том же состоянии, чтобы пользователь мог повторить ввод
        # await state.set_state(PartRequest.waiting_for_piece)
        return

    await state.update_data(nom_piece=corrected_piece, nom_piece_original=raw_piece)

    # Используем shorten для корректного отображения длинных названий в callback_data
    short_corrected_piece = textwrap.shorten(corrected_piece, width=50, placeholder="...")

    await message.answer(
        f"✅ Nom de pièce corrigé : <b>{corrected_piece}</b>\nSouhaitez-vous continuer avec ce nom ?",
        reply_markup=get_ai_correct_keyboard(short_corrected_piece),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("piece_ok:"))
async def confirm_piece(callback: CallbackQuery, state: FSMContext):
    # data = await state.get_data()
    # full_piece_name = data.get('nom_piece')
    # await state.update_data(nom_piece=full_piece_name) # Это уже есть в state.data
    
    await callback.message.edit_text("🔢 Quantité :", reply_markup=None) # Удаляем инлайн-клавиатуру
    await state.set_state(PartRequest.waiting_for_quantite)
    await callback.answer() # Закрываем уведомление о нажатии кнопки


@router.callback_query(F.data == "piece_retry")
async def retry_piece(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🔧 Entrez à nouveau le nom ou le numéro de la pièce :")
    await state.set_state(PartRequest.waiting_for_piece)
    await callback.answer()

@router.message(PartRequest.waiting_for_quantite)
async def get_quantity(message: Message, state: FSMContext):
    try:
        quantity = int(message.text.strip())
        if quantity <= 0:
            raise ValueError("La quantité doit être un nombre positif.")
        await state.update_data(quantite=quantity)
    except ValueError:
        await message.answer("❌ Quantité invalide. Veuillez entrer un nombre entier positif :")
        return # Остаемся в текущем состоянии

    await message.answer("🔍 Entrez le VIN du véhicule (optionnel) :", reply_markup=skip_vin_kb)
    await state.set_state(PartRequest.waiting_for_vin)

@router.message(PartRequest.waiting_for_vin)
async def get_vin(message: Message, state: FSMContext):
    if message.text != "➖ Passer":
        await state.update_data(vin=message.text)
    else:
        await state.update_data(vin=None)
    await message.answer("📷 Envoyez une photo ou scannez la pièce (optionnel) :", reply_markup=skip_photo_kb)
    await state.set_state(PartRequest.waiting_for_photo)

@router.message(PartRequest.waiting_for_photo)
async def get_photo(message: Message, state: FSMContext):
    photo_file_id = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id
        await state.update_data(photo=photo_file_id)
    else:
        await state.update_data(photo=None) # Если текст "➖ Passer" или другой текст

    data = await state.get_data()
    # Проверка, что 'nom_piece' существует, если нет, использовать 'nom_piece_original'
    if 'nom_piece' not in data:
        data['nom_piece'] = data.get('nom_piece_original', 'Pièce inconnue')

    request_id = await save_part_request(
        message.from_user.id,
        data.get("marque"),
        data.get("modele"),
        data.get("annee"),
        data.get("nom_piece"),
        data.get("quantite"),
        photo_file_id # Передаем photo_file_id
    )

    if request_id:
        print(f"DEBUG_PR: Запрос сохранен с ID: {request_id}")
        
        # Данные для рассылки
        broadcast_data = {
            "id": request_id,
            "store_id": message.from_user.id,
            "car": f"{data.get('marque')} {data.get('modele')} ({data.get('annee')})",
            "part_name": data.get("nom_piece"),
            "quantite": data.get("quantite"),
            "vin_code": data.get("vin"), # Передача VIN
            "photo_file_id": photo_file_id # Передача photo_file_id
        }
        await broadcast_request_to_stores(message.bot, broadcast_data)

        resume = (
            f"✅ Demande enregistrée :\n"
            f"🚗 {data.get('marque')} {data.get('modele')} ({data.get('annee')})\n"
            f"🔧 Pièce : {data.get('nom_piece')}\n"
            f"🔢 Quantité : {data.get('quantite')}"
        )
        if data.get("vin"):
            resume += f"\n🔍 VIN : {data.get('vin')}"
        if photo_file_id:
            resume += "\n📷 Photo jointe."
        
        callback_data_for_button = f"view_offers:{request_id}" # Это колбэк для просмотра ответов
        await message.answer(resume, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔍 Voir les réponses", callback_data=callback_data_for_button)]]), parse_mode="HTML")
        await state.clear()
    else:
        await message.answer("❌ Erreur lors de l'enregistrement de votre demande. Veuillez réessayer.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
@router.message(PartRequest.waiting_for_photo, F.text == "➖ Passer")
async def skip_photo(message: Message, state: FSMContext):
    await state.update_data(photo=None)
    data = await state.get_data()
    # Проверка, что 'nom_piece' существует, если нет, использовать 'nom_piece_original'
    if 'nom_piece' not in data:
        data['nom_piece'] = data.get('nom_piece_original', 'Pièce inconnue')
    await send_request_to_server(data, message, state)
@router.callback_query(F.data.startswith("view_offers:"))
async def view_offers(callback_query: CallbackQuery):
    request_id = callback_query.data.split(":")[1]
    # Здесь нужно реализовать логику для получения и отображения ответов на запрос
    # Например, получить ответы из базы данных и отправить их пользователю  