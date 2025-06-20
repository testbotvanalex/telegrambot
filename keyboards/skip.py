from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

skip_vin_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="➖ Passer")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

skip_photo_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="➖ Passer")]],
    resize_keyboard=True,
    one_time_keyboard=True
)
