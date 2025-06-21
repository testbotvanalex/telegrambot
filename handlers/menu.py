from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from db.db import get_store_by_telegram_id
from keyboards.menu import get_main_menu
from utils.role_checker import is_admin

from handlers.my_requests import my_requests_handler
from handlers.contact import contact_handler
from handlers.help import help_handler
from handlers.my_info import show_my_info
from handlers.store_registration import register_store
from handlers.part_request import start_request
from handlers.part_multi_request import start_multi_request
from handlers.stock_upload import ask_excel_file
from handlers.vin_ocr import prompt_photo
from handlers.admin.admin_ads import start_new_ad
from handlers.admin.admin_clients import new_client
from handlers.stock_search import start_stock_search

router = Router()

@router.message(Command(commands=["start", "menu"]))
async def show_menu(message: types.Message, state: FSMContext):
    await try_show_menu(message, state)

@router.message(StateFilter(None), F.text.in_({
    "📦 Demander une pièce",
    "📄 Mes demandes",
    "❓ Aide",
    "📞 Contact",
    "📝 Mes infos",
    "🧾 Demande groupée",
    "📊 Charger le stock",
    "📸 Lire un VIN",
    "🔎 Rechercher stock",
    "➕ Nouvelle Pub",
    "➕ Nouveau Client"
}))
async def handle_reply_buttons(message: types.Message, state: FSMContext):
    await state.clear()
    match message.text:
        case "📦 Demander une pièce":
            await start_request(message, state)
        case "📄 Mes demandes":
            await my_requests_handler(message)
        case "❓ Aide":
            await help_handler(message)
        case "📞 Contact":
            await contact_handler(message)
        case "📝 Mes infos":
            await show_my_info(message, state)
        case "🧾 Demande groupée":
            await start_multi_request(message, state)
        case "📊 Charger le stock":
            await ask_excel_file(message)
        case "📸 Lire un VIN":
            await prompt_photo(message)
        case "🔎 Rechercher stock":
            await start_stock_search(message, state)
        case "➕ Nouvelle Pub":
            await start_new_ad(message, state)
        case "➕ Nouveau Client":
            await new_client(message, state)

@router.message(StateFilter(None))
async def fallback_menu(message: types.Message, state: FSMContext):
    print(f"[DEBUG] Texte non reconnu: '{message.text}' de {message.from_user.id}")
    await try_show_menu(message, state)

async def try_show_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if await is_admin(user_id):
        role = "admin"
    else:
        try:
            store = await get_store_by_telegram_id(user_id)
        except Exception as e:
            await message.answer(f"❌ Erreur lors de la récupération des données. Réessayez plus tard.\n\n{e}")
            return

        if not store:
            await message.answer(
                "👋 Bienvenue dans le réseau B2B de pièces automobiles.\n\n"
                "Veuillez enregistrer votre magasin pour commencer."
            )
            await register_store(message, state)
            return

        if not store.get("approved", False):
            await message.answer("⏳ Votre inscription est en cours de validation. Merci de patienter.")
            return
        role = "store"

    await message.answer(
        "📋 Choisissez une option ci-dessous.",
        reply_markup=get_main_menu(role)
    )