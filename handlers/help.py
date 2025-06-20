from aiogram import Router, types, F # Добавлен импорт F
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

HELP_TEXT = """
ℹ️ <b>Aide</b>

Voici les commandes disponibles :

/start — Recommencer le bot  
/menu — Afficher le menu  
/verzoek — Demander une pièce  
/my_requests — Voir vos demandes  
/contact — Contacter le support
"""

@router.message(Command("help"))
@router.message(F.text == "❓ Aide") # Добавлено для кнопки меню
async def help_handler(message: Message):
    await message.answer(HELP_TEXT, parse_mode="HTML")
