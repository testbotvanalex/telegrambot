from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def cancel_keyboard(): # Уже есть в keyboards.reply.get_cancel_button() - можно унифицировать
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Annuler")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def confirm_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Confirmer"), KeyboardButton(text="❌ Annuler")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_city_keyboard(): # Используется в старой логике, если не FSM
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Paris"), KeyboardButton(text="Lyon")],
            [KeyboardButton(text="Marseille"), KeyboardButton(text="Autre")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_category_keyboard(): # Используется в старой логике, если не FSM
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔧 Pièces moteur"), KeyboardButton(text="🚗 Carrosserie")],
            [KeyboardButton(text="💡 Éclairage"), KeyboardButton(text="Autre")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_contact_choice_keyboard(): # Используется в старой логике, если не FSM
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📲 Utiliser mon numéro Telegram")],
            [KeyboardButton(text="✍️ Entrer manuellement")],
            [KeyboardButton(text="⏭️ Ignorer")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def store_registration_keyboard(): # Кнопка для начала регистрации
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Enregistrer mon magasin")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    