from aiogram import Router, types
from aiogram.filters import Command
import aiosqlite
from config.config import TELEGRAM_ADMIN_USER_IDS # Изменено на config.config
from utils.role_checker import is_admin # Добавлена проверка is_admin
from db.db import add_admin_to_db, remove_admin_from_db, get_all_admins

router = Router()

@router.message(Command("addadmin"))
async def add_admin(message: types.Message):
    if not await is_admin(message.from_user.id): # Используем is_admin
        await message.answer("⛔️ Vous n’avez pas les droits pour ajouter un admin.")
        return

    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("❗️Utilisation correcte : /addadmin 123456789")
        return

    new_admin_id = int(parts[1])

    # Добавляем в БД admins
    await add_admin_to_db(new_admin_id, 'admin')

    await message.answer(f"✅ L'utilisateur <code>{new_admin_id}</code> est maintenant admin.", parse_mode="HTML")

@router.message(Command("removeadmin"))
async def remove_admin(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔️ Vous n’avez pas les droits pour supprimer un admin.")
        return

    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("❗️Utilisation correcte : /removeadmin 123456789")
        return

    admin_id_to_remove = int(parts[1])

    # Удаляем из БД admins
    await remove_admin_from_db(admin_id_to_remove)

    await message.answer(f"✅ L'administrateur <code>{admin_id_to_remove}</code> a été supprimé.", parse_mode="HTML")
@router.message(Command("listadmins"))
async def list_admins(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔️ Vous n’avez pas les droits pour voir la liste des admins.")
        return

    # Получаем список администраторов из БД
    admins = await get_all_admins()
    if not admins:
        await message.answer("❗️ Il n'y a pas d'administrateurs enregistrés.")
        return
    admin_list = "\n".join([f"{admin['telegram_id']} - {admin['username'] or 'Pas de nom'}" for admin in admins])
    await message.answer(f"Liste des administrateurs :\n{admin_list}")

