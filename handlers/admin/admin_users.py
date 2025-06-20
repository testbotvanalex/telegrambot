from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.state import StateFilter
from aiogram.fsm.state import State, StatesGroup
from db.db import get_all_stores, approve_store, reject_store, get_store_by_telegram_id, update_store_status, get_subscription_by_store_id, update_subscription, add_user_note, get_user_notes
from utils.role_checker import is_admin

router = Router()

class UserManagement(StatesGroup):
    waiting_for_user_search = State()
    waiting_for_user_action_choice = State() # Это состояние может быть избыточным, если действия выбираются сразу
    waiting_for_plan_update = State()
    waiting_for_note_input = State()

@router.message(Command("users"))
@router.message(F.text == "👤 Utilisateurs")
async def list_users(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔️ Vous n’avez pas les droits pour gérer les utilisateurs.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Chercher un utilisateur", callback_data="users:search")],
        [InlineKeyboardButton(text="📋 Voir tous les utilisateurs", callback_data="users:show_all")]
    ])
    await message.answer("👤 Gestion des utilisateurs :", reply_markup=kb)

@router.callback_query(F.data == "users:show_all")
async def show_all_users_callback(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id): # Добавить проверку прав
        await callback.answer("⛔️ Vous n'avez pas les droits.", show_alert=True)
        return

    users = await get_all_stores()
    if not users:
        await callback.message.edit_text("📍 Aucun utilisateur enregistré.") # edit_text для обновления
        await callback.answer()
        return

    await callback.message.edit_reply_markup(reply_markup=None) # Удалить кнопки после выбора
    await send_user_list(callback.message, users)
    await callback.answer()


@router.callback_query(F.data == "users:search")
async def search_user_prompt(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id): # Добавить проверку прав
        await callback.answer("⛔️ Vous n'avez pas les droits.", show_alert=True)
        return

    await callback.message.edit_text("🔍 Entrez l'ID Telegram, le nom d'utilisateur ou le nom du magasin :")
    await state.set_state(UserManagement.waiting_for_user_search)
    await callback.answer()

@router.message(UserManagement.waiting_for_user_search)
async def process_user_search(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id): # Добавить проверку прав
        await message.answer("⛔️ Vous n'avez pas les droits.")
        await state.clear()
        return

    search_query = message.text.strip()
    users = await get_all_stores(search_query=search_query)

    if not users:
        await message.answer(f"❌ Aucun utilisateur trouvé pour '{search_query}'.")
        await state.clear()
        return

    if len(users) == 1:
        # Если найден один пользователь, сразу показываем его профиль
        await show_user_profile_direct(message, users[0]['telegram_id'])
    else:
        await message.answer("Plusieurs utilisateurs trouvés :")
        await send_user_list(message, users)
    await state.clear()


async def send_user_list(message_obj: types.Message, users_list: list):
    for user in users_list:
        status = "✅ Approuvé" if user['approved'] else "⏳ En attente"
        user_status = "🟢 Actif" if user.get('status', 'active') == 'active' else "🚫 Banni"
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📄 Profil", callback_data=f"user:profile:{user['telegram_id']}"),
                InlineKeyboardButton(text="✏️ Gérer", callback_data=f"user:manage:{user['telegram_id']}")
            ]
        ])
        await message_obj.answer(
            f"👤 <b>@{user['username'] or '—'}</b> (ID: <code>{user['telegram_id']}</code>)\n"
            f"🏪 {user['name']} — {status} ({user_status})",
            reply_markup=kb,
            parse_mode="HTML"
        )

# Хендлер для прямого вызова show_user_profile
async def show_user_profile_direct(message_obj: types.Message, telegram_id: int):
    await show_user_profile_logic(message_obj, telegram_id)

@router.callback_query(F.data.startswith("user:profile:"))
async def show_user_profile_callback(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id): # Добавить проверку прав
        await callback.answer("⛔️ Vous n'avez pas les droits.", show_alert=True)
        return

    telegram_id = int(callback.data.split(":")[2])
    await show_user_profile_logic(callback.message, telegram_id)
    await callback.answer()

async def show_user_profile_logic(message_obj: types.Message, telegram_id: int):
    user_store = await get_store_by_telegram_id(telegram_id)
    if not user_store:
        await message_obj.answer("❌ Utilisateur introuvable.")
        return

    subscription = await get_subscription_by_store_id(user_store['id'])
    notes = await get_user_notes(telegram_id)
    
    sub_info = f"🔖 Plan: <b>{subscription.get('plan', 'Free')}</b>\n" \
               f"📅 Expire: {subscription.get('expires_at', '—')}\n" \
               f"💳 Statut: {subscription.get('status', 'N/A')}\n" \
               f"💰 Montant: {subscription.get('amount', 'N/A')}\n" \
               f"💳 Paiement: {subscription.get('payment_method', 'N/A')}" if subscription else "🔖 Pas d'abonnement actif."
    
    notes_info = "\n".join([f"- {n['note']} ({n['created_at'][:10]})" for n in notes]) if notes else "Aucune note."

    text = (
        f"<b>📄 Profil utilisateur</b>\n\n"
        f"👤 <b>@{user_store['username'] or '—'}</b> (ID: <code>{user_store['telegram_id']}</code>)\n"
        f"🏪 <b>Magasin:</b> {user_store['name']}\n"
        f"📍 <b>Adresse:</b> {user_store['address']}, {user_store['city']}\n"
        f"🛒 <b>Catégories:</b> {user_store['categories']}\n"
        f"📞 <b>Contact:</b> {user_store['contact'] or '—'}\n"
        f"✅ <b>Approuvé:</b> {'Oui' if user_store['approved'] else 'Non'}\n"
        f"🔐 <b>Statut:</b> {'Actif' if user_store.get('status', 'active') == 'active' else 'Banni'}\n\n"
        f"<b>💳 Abonnement:</b>\n{sub_info}\n\n"
        f"<b>🗒 Notes internes:</b>\n{notes_info}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Gérer l'utilisateur", callback_data=f"user:manage:{telegram_id}")]
    ])
    await message_obj.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("user:manage:"))
async def manage_user_options(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id): # Добавить проверку прав
        await callback.answer("⛔️ Vous n'avez pas les droits.", show_alert=True)
        return

    telegram_id = int(callback.data.split(":")[2])
    await state.update_data(managing_user_id=telegram_id)
    user_store = await get_store_by_telegram_id(telegram_id)

    approve_text = "🆙 Désapprouver" if user_store['approved'] else "✅ Approuver"
    ban_text = "🟢 Déban" if user_store.get('status', 'active') == 'banned' else "🔒 Ban"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=approve_text, callback_data=f"user_m:toggle_approve:{telegram_id}")],
        [InlineKeyboardButton(text=ban_text, callback_data=f"user_m:toggle_ban:{telegram_id}")],
        [InlineKeyboardButton(text="🔖 Changer plan abonnement", callback_data=f"user_m:change_plan:{telegram_id}")],
        [InlineKeyboardButton(text="🗒 Ajouter note", callback_data=f"user_m:add_note:{telegram_id}")],
        [InlineKeyboardButton(text="⬅️ Retour au profil", callback_data=f"user:profile:{telegram_id}")]
    ])
    await callback.message.edit_text(f"🛠 Gérer l'utilisateur <b>@{user_store['username'] or '—'}</b> (ID: <code>{telegram_id}</code>) :", reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("user_m:toggle_approve:"))
async def toggle_approve_user(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id): # Добавить проверку прав
        await callback.answer("⛔️ Vous n'avez pas les droits.", show_alert=True)
        return

    telegram_id = int(callback.data.split(":")[2])
    user_store = await get_store_by_telegram_id(telegram_id)
    
    if user_store['approved']:
        await approve_store(telegram_id, False)
        await callback.message.answer(f"❌ Utilisateur <code>{telegram_id}</code> désapprouvé.", parse_mode="HTML")
    else:
        await approve_store(telegram_id, True)
        await callback.message.answer(f"✅ Utilisateur <code>{telegram_id}</code> approuvé.", parse_mode="HTML")
    
    await callback.answer("Statut mis à jour.", show_alert=True)
    # Показываем обновленный профиль
    await show_user_profile_logic(callback.message, telegram_id=telegram_id)


@router.callback_query(F.data.startswith("user_m:toggle_ban:"))
async def toggle_ban_user(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id): # Добавить проверку прав
        await callback.answer("⛔️ Vous n'avez pas les droits.", show_alert=True)
        return

    telegram_id = int(callback.data.split(":")[2])
    user_store = await get_store_by_telegram_id(telegram_id)
    current_status = user_store.get('status', 'active')

    new_status = 'banned' if current_status == 'active' else 'active'
    await update_store_status(telegram_id, new_status)

    await callback.answer(f"Statut mis à jour à {new_status}.", show_alert=True)
    # Показываем обновленный профиль
    await show_user_profile_logic(callback.message, telegram_id=telegram_id)


@router.callback_query(F.data.startswith("user_m:change_plan:"))
async def change_plan_prompt(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id): # Добавить проверку прав
        await callback.answer("⛔️ Vous n'avez pas les droits.", show_alert=True)
        return

    telegram_id = int(callback.data.split(":")[2])
    await state.update_data(target_user_id=telegram_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Free", callback_data="setplan:Free")],
        [InlineKeyboardButton(text="Pro", callback_data="setplan:Pro")],
        [InlineKeyboardButton(text="VIP", callback_data="setplan:VIP")]
    ])
    await callback.message.edit_text("Choisissez le nouveau plan :", reply_markup=kb)
    await state.set_state(UserManagement.waiting_for_plan_update)
    await callback.answer()

@router.callback_query(F.data.startswith("setplan:"), StateFilter(UserManagement.waiting_for_plan_update))
async def process_plan_change(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id): # Добавить проверку прав
        await callback.answer("⛔️ Vous n'avez pas les droits.", show_alert=True)
        return

    plan = callback.data.split(":")[1]
    data = await state.get_data()
    target_user_id = data.get("target_user_id")

    if target_user_id:
        await update_subscription(target_user_id, plan)
        await callback.answer(f"Plan mis à jour pour l'utilisateur {target_user_id} à {plan}.", show_alert=True)
        await state.clear()
        await show_user_profile_logic(callback.message, telegram_id=target_user_id) # Обновляем профиль
    else:
        await callback.answer("Erreur: Utilisateur non défini.", show_alert=True)
        await state.clear()

@router.callback_query(F.data.startswith("user_m:add_note:"))
async def add_note_prompt(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id): # Добавить проверку прав
        await callback.answer("⛔️ Vous n'avez pas les droits.", show_alert=True)
        return

    telegram_id = int(callback.data.split(":")[2])
    await state.update_data(target_user_id_for_note=telegram_id)
    await callback.message.edit_text(f"🗒 Entrez la note à ajouter pour l'utilisateur <code>{telegram_id}</code> :", parse_mode="HTML")
    await state.set_state(UserManagement.waiting_for_note_input)
    await callback.answer()

@router.message(F.text, StateFilter(UserManagement.waiting_for_note_input))
async def process_add_note(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id): # Добавить проверку прав
        await message.answer("⛔️ Vous n'avez pas les droits.")
        await state.clear()
        return

    data = await state.get_data()
    target_user_id = data.get("target_user_id_for_note")
    note_text = message.text.strip()

    if target_user_id:
        await add_user_note(target_user_id, note_text)
        await message.answer(f"✅ Note ajoutée pour l'utilisateur <code>{target_user_id}</code>.", parse_mode="HTML")
        await state.clear()
        await show_user_profile_logic(message, telegram_id=target_user_id) # Обновляем профиль
    else:
        await message.answer("Erreur: Utilisateur non défini pour la note.")
        await state.clear()
