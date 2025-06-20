from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters.state import StateFilter # ИСПРАВЛЕНО: Добавлен импорт StateFilter

from keyboards.store import store_registration_keyboard
from keyboards.admin import get_approval_keyboard
from db.db import save_store
from config.config import TELEGRAM_MOD_GROUP_ID
from services.ai_correction import correct_car_info
from services.ai_correction import correct_part_name

router = Router()

class Registration(StatesGroup):
    nom = State()
    adresse = State()
    ville = State()
    categories_group = State()
    categories = State()
    telephone = State()
    localisation = State()

retour_button = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Annuler")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

telephone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📲 Utiliser mon numéro Telegram")],
        [KeyboardButton(text="✍️ Entrer manuellement")],
        [KeyboardButton(text="⏭️ Ignorer")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

CATEGORY_GROUPS = [
    ("🔧 Mécanique", "mecanique"),
    ("⚡ Électrique", "electrique"),
    ("🛡 Carrosserie", "carrosserie"),
    ("🧰 Divers", "divers")
]

CATEGORIES_MAP = {
    "mecanique": ["Moteur", "Suspension", "Transmission"],
    "electrique": ["Batterie", "Éclairage", "Capteurs"],
    "carrosserie": ["Portières", "Pare-chocs", "Vitres"],
    "divers": ["Outillage", "Accessoires"]
}

def get_group_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=f"group:{value}")]
        for label, value in CATEGORY_GROUPS
    ])

def get_category_keyboard(group, selected):
    keyboard = []
    row = []
    for i, name in enumerate(CATEGORIES_MAP[group]):
        prefix = "✅" if name in selected else "▫️"
        row.append(InlineKeyboardButton(text=f"{prefix} {name}", callback_data=f"cat:{name}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Retour", callback_data="cat_back"),
        InlineKeyboardButton(text="✅ Terminé", callback_data="cat_done")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(F.text == "📝 Enregistrer mon magasin")
async def register_store(message: types.Message, state: FSMContext):
    await state.clear()
    await state.update_data(categories_selected=[])
    await message.answer("Quel est le **nom** de votre magasin ?", reply_markup=retour_button)
    await state.set_state(Registration.nom)

@router.message(F.text == "❌ Annuler", StateFilter(Registration))
async def cancel_registration(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Enregistrement annulé. Vous pouvez recommencer à tout moment.", reply_markup=ReplyKeyboardRemove())


@router.message(Registration.nom)
async def process_nom(message: types.Message, state: FSMContext):
    corrected_nom = message.text.strip()
    await state.update_data(nom=corrected_nom)
    await message.answer("📍 Quelle est l’**adresse** de votre magasin ?", reply_markup=retour_button)
    await state.set_state(Registration.adresse)

@router.message(Registration.adresse)
async def process_adresse(message: types.Message, state: FSMContext):
    corrected_adresse = message.text.strip()
    await state.update_data(adresse=corrected_adresse)
    await message.answer("🌇 Dans quelle **ville** vous situez-vous ?", reply_markup=retour_button)
    await state.set_state(Registration.ville)

@router.message(Registration.ville)
async def process_ville(message: types.Message, state: FSMContext):
    corrected_ville = message.text.strip()
    await state.update_data(ville=corrected_ville)
    await message.answer("📦 Sélectionnez une ou plusieurs catégories principales (par ex. 'Mécanique') :", reply_markup=get_group_keyboard())
    await state.set_state(Registration.categories_group)

@router.callback_query(F.data.startswith("group:"), Registration.categories_group)
async def select_group(call: types.CallbackQuery, state: FSMContext):
    group = call.data.split(":")[1]
    data = await state.get_data()
    selected_categories = data.get("categories_selected", [])
    await state.update_data(current_group=group)
    await call.message.edit_text("🧩 Sélectionnez une ou plusieurs sous-catégories :",
                                 reply_markup=get_category_keyboard(group, selected_categories))
    await state.set_state(Registration.categories)
    await call.answer()

@router.callback_query(F.data.startswith("cat:"), Registration.categories)
async def toggle_category(call: types.CallbackQuery, state: FSMContext):
    value = call.data.split(":")[1]
    data = await state.get_data()
    selected = data.get("categories_selected", [])
    group = data.get("current_group")

    if value in selected:
        selected.remove(value)
    else:
        selected.append(value)
    await state.update_data(categories_selected=selected)
    await call.message.edit_reply_markup(reply_markup=get_category_keyboard(group, selected))
    await call.answer()

@router.callback_query(F.data == "cat_done", Registration.categories)
async def category_done(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("categories_selected", [])
    if not selected:
        await call.answer("⚠️ Veuillez sélectionner au moins une catégorie.", show_alert=True)
        return

    await state.update_data(categories=", ".join(selected))

    await call.message.answer(
        "📞 Numéro WhatsApp ou téléphone :\nChoisissez une option ou entrez manuellement votre numéro :",
        reply_markup=telephone_keyboard
    )
    await call.message.edit_reply_markup(reply_markup=None)

    await state.set_state(Registration.telephone)
    await call.answer()

@router.callback_query(F.data == "cat_back", Registration.categories)
async def category_back(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text("📦 Reprenez une catégorie principale :", reply_markup=get_group_keyboard())
    await state.set_state(Registration.categories_group)
    await call.answer()

@router.message(Registration.telephone, F.text == "📲 Utiliser mon numéro Telegram")
async def use_telegram_number(message: types.Message, state: FSMContext):
    await state.update_data(telephone=message.from_user.username or str(message.from_user.id))
    await ask_location(message, state)

@router.message(Registration.telephone, F.text == "✍️ Entrer manuellement")
async def ask_manual_telephone(message: types.Message, state: FSMContext):
    await message.answer("📞 Entrez manuellement votre numéro WhatsApp ou téléphone :", reply_markup=retour_button)
    
@router.message(Registration.telephone, F.text == "⏭️ Ignorer")
async def skip_telephone(message: types.Message, state: FSMContext):
    await state.update_data(telephone=None)
    await ask_location(message, state)

@router.message(Registration.telephone, F.text)
async def manual_telephone(message: types.Message, state: FSMContext):
    await state.update_data(telephone=message.text)
    await ask_location(message, state)

async def ask_location(message: types.Message, state: FSMContext):
    await message.answer(
        "📌 Vous pouvez maintenant envoyer votre **localisation** (optionnel).",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📍 Envoyer ma localisation", request_location=True)],
                [KeyboardButton(text="⏭ Ignorer")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    await state.set_state(Registration.localisation)

@router.message(Registration.localisation, F.location)
async def process_location(message: types.Message, state: FSMContext):
    await state.update_data(latitude=message.location.latitude, longitude=message.location.longitude)
    await validate_registration(message, state)

@router.message(Registration.localisation, F.text == "⏭ Ignorer")
async def skip_location_button(message: types.Message, state: FSMContext):
    await state.update_data(latitude=None, longitude=None)
    await validate_registration(message, state)

@router.message(Registration.localisation)
async def skip_location_text(message: types.Message, state: FSMContext):
    await state.update_data(latitude=None, longitude=None)
    await validate_registration(message, state)

async def validate_registration(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user = message.from_user

    await save_store(
        user.id,
        user.username or "",
        data.get("nom"),
        data.get("adresse"),
        data.get("ville"),
        data.get("categories"),
        data.get("telephone"),
        False,
        data.get("latitude"),
        data.get("longitude")
    )

    text = (
        f"📝 Nouvelle demande d’enregistrement de magasin :\n"
        f"👤 @{user.username or user.full_name} (ID: <code>{user.id}</code>)\n"
        f"🏪 Nom: {data.get('nom')}\n"
        f"📍 Adresse: {data.get('adresse')}, {data.get('ville')}\n"
        f"📦 Catégories: {data.get('categories')}\n"
        f"📞 Téléphone: {data.get('telephone') or 'Non fourni'}\n"
        f"🗺 Localisation: {data.get('latitude', 'N/A')}, {data.get('longitude', 'N/A')}"
    )

    await message.answer("✅ Merci ! Votre demande a été envoyée pour validation.", reply_markup=ReplyKeyboardRemove())
    await state.clear()

    if TELEGRAM_MOD_GROUP_ID != 0:
        await message.bot.send_message(
            chat_id=TELEGRAM_MOD_GROUP_ID,
            text=text,
            reply_markup=get_approval_keyboard(user.id),
            parse_mode="HTML"
        )
    else:
        print("WARNING: TELEGRAM_MOD_GROUP_ID is not set. Moderation request not sent.")

    await message.bot.send_message(
        chat_id=user.id,
        text="Votre demande d’enregistrement de magasin a été envoyée pour validation. Vous serez informé dès qu’elle sera approuvée."
    )
