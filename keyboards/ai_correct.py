from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_ai_correct_keyboard(corrected_name: str) -> InlineKeyboardMarkup:
    # Важно: callback_data имеет ограничение в 64 байта.
    # Если corrected_name может быть очень длинным, его нужно укорачивать
    # или передавать request_id/hash, а не полное имя.
    # textwrap.shorten используется в part_request.py
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Oui, continuer", callback_data=f"piece_ok:{corrected_name}")],
        [InlineKeyboardButton(text="🔄 Corriger à nouveau", callback_data="piece_retry")]
    ])