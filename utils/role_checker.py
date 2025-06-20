from db.db import get_admin_by_telegram_id
from config.config import TELEGRAM_ADMIN_USER_IDS # Изменено на config.config

async def is_admin(user_id: int) -> bool:
    # Проверяем, является ли user_id одним из супер-админов из config.py
    if user_id in TELEGRAM_ADMIN_USER_IDS:
        return True
    
    # Также проверяем, есть ли пользователь в таблице admins
    admin_entry = await get_admin_by_telegram_id(user_id)
    return admin_entry is not None and admin_entry.get('role') == 'admin'