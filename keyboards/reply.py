from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_retour_button():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Retour")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_cancel_button():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Annuler")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Быстрые доступы (если нужно без функций)
# retour_button = get_retour_button() # Не используем глобально, чтобы не было конфликтов
# cancel_button = get_cancel_button() # Не используем глобально
# Используйте эти функции для создания кнопок в нужных местах