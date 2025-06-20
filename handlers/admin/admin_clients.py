from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.state import StateFilter

from db.db import get_all_clients, create_client, get_client_by_id, save_client_note # ИСПРАВЛЕНО: from db.db
from utils.role_checker import is_admin

router = Router()

class NewClient(StatesGroup):
    name = State()
    phone = State()
    business = State()

class ClientNote(StatesGroup):
    adding_note = State()

# Добавлен класс состояний для AdminStates, если он был задуман
# Если это состояния для управления клиентами, то лучше дать более специфичное имя.
# Я создам новый класс для ясности.
class ClientManagementStates(StatesGroup):
    waiting_for_client_name = State() # Если это часть процесса создания/редактирования клиента
    waiting_for_client_phone = State()
    waiting_for_client_business = State()


@router.message(Command("clients"))
async def list_clients(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔️ Vous n’avez pas les droits.")
        return

    clients = await get_all_clients()
    if not clients:
        await message.answer("📭 Aucun client enregistré.")
        return

    for client in clients:
        await message.answer(
            f"🧑‍💼 <b>{client['name']}</b>\n📞 {client['phone'] or 'N/A'}\n🏢 {client['business'] or 'N/A'}\n🗒 Notes: {client['notes'] or 'Aucune'}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🗒 Voir ou ajouter une note", callback_data=f"client:note:{client['id']}")]
            ]),
            parse_mode="HTML"
        )

@router.message(Command("newclient"))
async def new_client(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔️ Vous n’avez pas les droits.")
        return
    await message.answer("🧑‍💼 Entrez le nom du client :")
    await state.set_state(NewClient.name)

@router.message(NewClient.name)
async def client_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📞 Entrez le numéro de téléphone :")
    await state.set_state(NewClient.phone)

@router.message(NewClient.phone)
async def client_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("🏢 Entrez le nom du business :")
    await state.set_state(NewClient.business)

@router.message(NewClient.business)
async def client_business(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await create_client(data["name"], data["phone"], message.text)
    await message.answer("✅ Client enregistré.")
    await state.clear()

@router.callback_query(F.data.startswith("client:note:"))
async def handle_client_note(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔️ Vous n’avez pas les droits.")
        return
    
    client_id = int(callback.data.split(":")[2])
    client = await get_client_by_id(client_id)

    if not client:
        await callback.answer("❌ Client introuvable.", show_alert=True)
        return

    await state.update_data(client_id=client_id)
    await callback.message.edit_text(
        f"🗒 Note pour <b>{client['name']}</b> :\n"
        f"Note actuelle: {client['notes'] or 'Aucune'}\n\n"
        "Envoyez-moi une nouvelle note à ajouter/обновить.",
        parse_mode="HTML"
    )
    await state.set_state(ClientNote.adding_note)

@router.message(ClientNote.adding_note, F.text)
async def save_note(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔️ Vous n’avez pas les droits.")
        await state.clear()
        return

    data = await state.get_data()
    client_id = data.get("client_id")
    note_text = message.text.strip()

    if client_id:
        await save_client_note(client_id, note_text)
        await message.answer("✅ Note ajoutée/mise à jour.")
        await state.clear()
        await list_clients(message)
    else:
        await message.answer("❌ Erreur: ID client non défini.")
        await state.clear()

# Если AdminStates.waiting_for_client_name использовалось в старой версии,
# и это относится к созданию нового клиента, то его можно заменить на NewClient.name
# Я предположил, что NewClient уже используется для создания клиента.
# Если же это была отдельная FSM для другого процесса, то AdminStates
# нужно было бы определить отдельно.
# Учитывая, что в трейсбэке указана строка 168, это может быть старый закомментированный код
# или незавершенный FSM, который я не видел в предыдущих файлах.
# Если строка 168 была @router.message(AdminStates.waiting_for_client_name),
# то я предполагаю, что она должна была быть @router.message(NewClient.name)
# или AdminStates должен быть определен выше.
# Если этот код не является частью NewClient, то нужно добавить:
# class AdminStates(StatesGroup):
#     waiting_for_client_name = State()
#     ...
# Но это будет избыточно, если NewClient уже выполняет эту роль.
