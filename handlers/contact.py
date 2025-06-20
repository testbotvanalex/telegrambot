from aiogram import Router, types, F # ИСПРАВЛЕНО: добавлен импорт F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

router = Router()

CONTACT_TEXT = """
📞 <b>Contacter le support</b>

Si vous avez une question, une suggestion ou un problème — écrivez-nous sur Telegram.
Nous vous répondrons dès que possible !
"""

@router.message(Command("contact"))
@router.message(F.text == "📞 Contact") # Добавлено для кнопки меню
async def contact_handler(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📬 Écrire sur Telegram", url="https://t.me/BotmaticSupport")]
    ])
    await message.answer(CONTACT_TEXT, reply_markup=keyboard, parse_mode="HTML")
