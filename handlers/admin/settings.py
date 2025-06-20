from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.role_checker import is_admin
from db.db import get_setting, set_setting, get_all_admins, add_admin_to_db, remove_admin_from_db # ИСПРАВЛЕНО: from db.db
from config.config import TELEGRAM_ADMIN_USER_IDS # Изменено на config.config

router = Router()

class SettingsState(StatesGroup):
    choosing_setting = State()
    editing_value = State()
    adding_admin_id = State()
    removing_admin_id = State()


@router.message(Command("settings"))
@router.message(F.text == "⚙️ Paramètres")
async def show_settings_menu(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔️ Vous n'avez pas les droits pour accéder à cette section.")
        return

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💰 Changer la devise", callback_data="settings:currency")],
        [types.InlineKeyboardButton(text="🗣 Changer la langue", callback_data="settings:language")],
        [types.InlineKeyboardButton(text="💬 Configurer les messages", callback_data="settings:messages")],
        [types.InlineKeyboardButton(text="🔔 Rappels automatiques", callback_data="settings:reminders")],
        [types.InlineKeyboardButton(text="➕ Gestion des admins", callback_data="settings:manage_admins")],
    ])
    await message.answer("⚙️ Menu des paramètres :", reply_markup=keyboard)


@router.callback_query(F.data.startswith("settings:"))
async def handle_settings_callback(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔️ Vous n'avez pas les droits.", show_alert=True)
        return

    action = callback.data.split(":")[1]

    if action == "currency":
        await callback.message.edit_text("💰 Entrez la nouvelle devise (par exemple, USD, EUR) :")
        await state.update_data(setting_key="currency")
        await state.set_state(SettingsState.editing_value)
    elif action == "language":
        await callback.message.edit_text("🗣 Entrez la nouvelle langue (par exemple, fr, en) :")
        await state.update_data(setting_key="language")
        await state.set_state(SettingsState.editing_value)
    elif action == "messages":
        await callback.message.edit_text("💬 Cette fonction nécessite une configuration manuelle pour le moment. Veuillez spécifier quel message vous souhaitez modifier (ex: welcome_message, ad_template).")
        await state.set_state(SettingsState.editing_value)
        await state.update_data(setting_key_prefix="message_")
    elif action == "reminders":
        await callback.message.edit_text("🔔 Indiquez l'intervalle pour les rappels automatiques (par exemple, '24h', '7j') :")
        await state.update_data(setting_key="auto_reminders_interval")
        await state.set_state(SettingsState.editing_value)
    elif action == "manage_admins":
        await show_admin_management_menu(callback.message)
    else:
        await callback.answer("❌ Action inconnue.")

    await callback.answer()


@router.message(SettingsState.editing_value)
async def process_new_setting_value(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔️ Vous n'avez pas les droits.")
        await state.clear()
        return

    data = await state.get_data()
    setting_key = data.get("setting_key")
    setting_key_prefix = data.get("setting_key_prefix")

    value = message.text.strip()

    if setting_key:
        await set_setting(setting_key, value)
        await message.answer(f"✅ Le paramètre '{setting_key}' a été mis à jour avec '{value}'.")
    elif setting_key_prefix:
        await message.answer("Veuillez spécifier le nom exact du message (par exemple 'welcome_message') :")
        await state.update_data(setting_key=setting_key_prefix + value)
        await message.answer("Veuillez entrer le nouveau texte pour ce message.")
        await state.set_state(SettingsState.editing_value)
        return

    await state.clear()
    await show_settings_menu(message)


async def show_admin_management_menu(message: types.Message):
    admins = await get_all_admins()
    admin_list = "\n".join([f"- <code>{admin['telegram_id']}</code>" for admin in admins]) if admins else "Aucun admin."

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ Ajouter un admin", callback_data="settings:add_admin")],
        [types.InlineKeyboardButton(text="➖ Supprimer un admin", callback_data="settings:remove_admin")],
        [types.InlineKeyboardButton(text="⬅️ Retour aux paramètres", callback_data="settings:back_to_main_settings")]
    ])
    await message.answer(
        f"👥 Administrateurs actuels :\n{admin_list}\n\nQue voulez-vous faire ?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "settings:add_admin")
async def add_admin_prompt(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in TELEGRAM_ADMIN_USER_IDS:
        await callback.answer("⛔️ Vous n'avez pas les droits pour ajouter des admins.", show_alert=True)
        return

    await callback.message.edit_text("➕ Entrez l'ID Telegram du nouvel administrateur :")
    await state.set_state(SettingsState.adding_admin_id)
    await callback.answer()

@router.message(SettingsState.adding_admin_id)
async def process_add_admin(message: types.Message, state: FSMContext):
    if message.from_user.id not in TELEGRAM_ADMIN_USER_IDS:
        await message.answer("⛔️ Vous n'avez pas les droits pour ajouter des admins.")
        await state.clear()
        return

    try:
        admin_id = int(message.text.strip())
        await add_admin_to_db(admin_id)
        await message.answer(f"✅ L'administrateur avec l'ID <code>{admin_id}</code> a été ajouté.", parse_mode="HTML")
    except ValueError:
        await message.answer("❌ Format d'ID invalide. Veuillez entrer un nombre.")
    except Exception as e:
        await message.answer(f"❌ Erreur lors de l'ajout de l'administrateur : {e}")
    finally:
        await state.clear()
        await show_settings_menu(message)


@router.callback_query(F.data == "settings:remove_admin")
async def remove_admin_prompt(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in TELEGRAM_ADMIN_USER_IDS:
        await callback.answer("⛔️ Vous n'avez pas les droits pour supprimer des admins.", show_alert=True)
        return

    await callback.message.edit_text("➖ Entrez l'ID Telegram de l'administrateur à supprimer :")
    await state.set_state(SettingsState.removing_admin_id)
    await callback.answer()

@router.message(SettingsState.removing_admin_id)
async def process_remove_admin(message: types.Message, state: FSMContext):
    if message.from_user.id not in TELEGRAM_ADMIN_USER_IDS:
        await message.answer("⛔️ Vous n'avez pas les droits pour supprimer des admins.")
        await state.clear()
        return

    try:
        admin_id = int(message.text.strip())
        await remove_admin_from_db(admin_id)
        await message.answer(f"✅ L'administrateur avec l'ID <code>{admin_id}</code> a été supprimé.", parse_mode="HTML")
    except ValueError:
        await message.answer("❌ Format d'ID invalide. Veuillez entrer un nombre.")
    except Exception as e:
        await message.answer(f"❌ Erreur lors de la suppression de l'administrateur : {e}")
    finally:
        await state.clear()
        await show_settings_menu(message)


@router.callback_query(F.data == "settings:back_to_main_settings")
async def back_to_main_settings(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔️ Vous n'avez pas les droits.", show_alert=True)
        return
        
    await state.clear()
    await show_settings_menu(callback.message)
    await callback.answer()
