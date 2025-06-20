from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from db.db import save_part_request_with_items, get_store_by_telegram_id
from keyboards.reply import get_cancel_button # Используем унифицированную кнопку отмены
from keyboards.store import confirm_keyboard # Используем confirm_keyboard из keyboards.store
from services.ai_correction import correct_part_name # Исправлено на services.ai_correction

router = Router()

class MultiPartForm(StatesGroup):
    car_description = State()
    part_name = State() # Для ввода одной части за раз
    part_quantity = State() # Для ввода количества одной части
    confirm_add_more = State() # Для подтверждения добавления еще или завершения
    confirm_final = State() # Для окончательного подтверждения

@router.message(F.text == "🧾 Demande groupée") # Если есть кнопка "Demande groupée"
@router.message(Command("multi_request")) # Или команда
async def start_multi_request(message: types.Message, state: FSMContext):
    store = await get_store_by_telegram_id(message.from_user.id)
    if not store or not store["approved"]:
        await message.answer("❌ Votre magasin n'est pas encore approuvé pour faire des demandes.")
        return

    await state.clear() # Очищаем старые данные
    await state.update_data(items=[], car_description=None) # Инициализируем список для частей

    await message.answer(
        "🛻 Décrivez le véhicule (марка, модель, год) :",
        reply_markup=get_cancel_button()
    )
    await state.set_state(MultiPartForm.car_description)

@router.message(MultiPartForm.car_description)
async def receive_car(message: types.Message, state: FSMContext):
    await state.update_data(car_description=message.text)
    await message.answer("🔧 Nom ou numéro de la première pièce :", reply_markup=get_cancel_button())
    await state.set_state(MultiPartForm.part_name)

@router.message(MultiPartForm.part_name)
async def receive_part_name(message: types.Message, state: FSMContext):
    raw_piece = message.text
    corrected_piece = await correct_part_name(raw_piece) # Используем AI-коррекцию
    await state.update_data(current_part_name=corrected_piece) # Сохраняем скорректированное имя
    
    await message.answer(f"🔢 Quantité pour '{corrected_piece}' :", reply_markup=get_cancel_button())
    await state.set_state(MultiPartForm.part_quantity)

@router.message(MultiPartForm.part_quantity)
async def receive_part_quantity(message: types.Message, state: FSMContext):
    try:
        quantity = int(message.text.strip())
        if quantity <= 0:
            raise ValueError("La quantité doit être un nombre positif.")
        
        data = await state.get_data()
        current_part_name = data.get('current_part_name')
        
        items = data.get('items', [])
        items.append({"name": current_part_name, "qty": quantity})
        await state.update_data(items=items)

        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="➕ Ajouter une autre pièce")],
                [KeyboardButton(text="✅ Terminer la demande")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(
            f"✅ '{current_part_name}' x{quantity} ajouté. Que souhaitez-vous faire ensuite?",
            reply_markup=kb
        )
        await state.set_state(MultiPartForm.confirm_add_more)

    except ValueError:
        await message.answer("❌ Quantité invalide. Veuillez entrer un nombre entier positif.")
        await message.answer(f"🔢 Quantité pour '{data.get('current_part_name')}' :") # Повторяем запрос количества
        # Остаемся в том же состоянии

@router.message(MultiPartForm.confirm_add_more, F.text == "➕ Ajouter une autre pièce")
async def add_another_part(message: types.Message, state: FSMContext):
    await message.answer("🔧 Nom ou numéro de la pièce suivante :", reply_markup=get_cancel_button())
    await state.set_state(MultiPartForm.part_name)

@router.message(MultiPartForm.confirm_add_more, F.text == "✅ Terminer la demande")
async def confirm_final_multi_request(message: types.Message, state: FSMContext):
    data = await state.get_data()
    car = data.get("car_description")
    items = data.get("items")

    if not items:
        await message.answer("⚠️ Vous n'avez ajouté aucune pièce. Veuillez ajouter au moins une pièce.")
        await message.answer("🔧 Nom ou numéro de la première pièce :", reply_markup=get_cancel_button())
        await state.set_state(MultiPartForm.part_name)
        return

    summary = f"📝 Confirmez votre demande groupée pour le véhicule :\n<b>{car}</b>\n\n📦 Pièces :\n"
    for item in items:
        summary += f"- {item['name']} x{item['qty']}\n"
    
    await message.answer(
        summary,
        reply_markup=confirm_keyboard(), # Используем confirm_keyboard из keyboards.store
        parse_mode="HTML"
    )
    await state.set_state(MultiPartForm.confirm_final)


@router.message(MultiPartForm.confirm_final, F.text == "✅ Confirmer")
async def send_final_multi_request(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    
    request_id = await save_part_request_with_items(
        user_id=user_id,
        car_description=data["car_description"],
        items=data["items"]
    )

    if request_id:
        # Здесь можно добавить логику broadcast_request_to_stores для групповых запросов
        # Возможно, создать специальный формат сообщения для групповых запросов
        await message.answer("📨 Votre demande groupée a été enregistrée et envoyée aux magasins concernés.", reply_markup 
= ReplyKeyboardRemove())
        await state.clear()  # Очищаем состояние после успешной отправки
    else:
        await message.answer("❌ Une erreur s'est produite lors de l'envoi de votre demande. Veuillez réessayer plus tard.")
        await state.clear()  # Очищаем состояние в случае ошибки
@router.message(MultiPartForm.confirm_final, F.text == "❌ Annuler")
async def cancel_final_multi_request(message: types.Message, state: FSMContext):
    await message.answer("❌ Demande annulée.", reply_markup=ReplyKeyboardRemove())
    await state.clear()  # Очищаем состояние после отмены
