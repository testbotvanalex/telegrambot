from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_request_details_keyboard(request_id: int) -> InlineKeyboardMarkup:
    # Эти callback_data обрабатываются в handlers.responses_handler.py (offer:...)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📦 J’ai cette pièce", callback_data=f"offer:have:{request_id}"),
            InlineKeyboardButton(text="🕒 Je la reçois bientôt", callback_data=f"offer:soon:{request_id}"),
            InlineKeyboardButton(text="❌ Je ne l’ai pas", callback_data=f"offer:none:{request_id}")
        ]
    ])
def get_request_cancel_keyboard(request_id: int) -> InlineKeyboardMarkup:
    # Клавиатура для отмены запроса
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Annuler la demande", callback_data=f"cancel_request:{request_id}")
        ]
    ])