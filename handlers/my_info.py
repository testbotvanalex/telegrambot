from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter # Импортируем StateFilter

from db.db import get_store_by_telegram_id, update_store_field # ИСПРАВЛЕНО: from db.db
from keyboards.reply import get_cancel_button # Используем унифицированную кнопку отмены
from keyboards.menu import get_main_menu # Для возврата в главное меню

router = Router()

class EditInfoFSM(StatesGroup):
    choosing_field = State()
    new_value = State()

@router.message(F.text == "📝 Mes infos")
async def show_my_info(message: Message, state: FSMContext):
    store = await get_store_by_telegram_id(message.from_user.id)
    if not store:
        await message.answer("❌ Vous n'êtes pas enregistré comme magasin.")
        return

    info = (
        f"🏪 <b>Nom:</b> {store['name']}\n"
        f"📍 <b>Adresse:</b> {store['address']}\n"
        f"🏙 <b>Ville:</b> {store['city']}\n"
        f"🛒 <b>Catégories:</b> {store['categories']}\n"
        f"📞 <b>Contact:</b> {store.get('contact') or 'Non fourni'}"
    )

    await message.answer("Voici les informations de votre magasin :\n\n" + info, parse_mode="HTML")
    await message.answer(
        "Souhaitez-vous modifier quelque chose ? Tapez un des champs suivants :\n"
        "<code>name, address, city, categories, contact</code>\n\n"
        "Ou tapez ❌ Annuler pour quitter.", # Обновляем текст для кнопки отмены
        reply_markup=get_cancel_button(), # Добавляем кнопку отмены
        parse_mode="HTML"
    )
    await state.set_state(EditInfoFSM.choosing_field)

# Обработчик кнопки "❌ Annuler" для состояния выбора поля
@router.message(F.text == "❌ Annuler", StateFilter(EditInfoFSM.choosing_field))
async def cancel_choosing_field(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Modification annulée.", reply_markup=get_main_menu("store")) # Возвращаем в главное меню магазина

# Обработчик кнопки "❌ Annuler" для состояния ввода нового значения
@router.message(F.text == "❌ Annuler", StateFilter(EditInfoFSM.new_value))
async def cancel_new_value(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Modification annulée.", reply_markup=get_main_menu("store")) # Возвращаем в главное меню магазина


@router.message(EditInfoFSM.choosing_field)
async def choose_field(message: Message, state: FSMContext):
    field = message.text.strip().lower()
    if field not in {"name", "address", "city", "categories", "contact"}:
        await message.answer("❗️Champ invalide. Essayez encore : name, address, city, categories, contact")
        return
    await state.update_data(field=field)
    await message.answer(f"✏️ Entrez la nouvelle valeur для <b>{field}</b> :", parse_mode="HTML", reply_markup=get_cancel_button()) # Добавляем кнопку отмены
    await state.set_state(EditInfoFSM.new_value)

@router.message(EditInfoFSM.new_value)
async def save_new_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data["field"]
    value = message.text.strip()
    await update_store_field(message.from_user.id, field, value)
    await message.answer(f"✅ Le champ <b>{field}</b> a été mis à jour !", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    await state.clear()
    await show_my_info(message, state) # Показать обновленную информацию
