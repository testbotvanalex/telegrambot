from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

# ✅ Клавиатура одобрения/отклонения заявки
def get_approval_keyboard(store_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Approuver",
                callback_data=f"mod:approve:{store_id}" # Изменено для соответствия moderation_queue.py
            ),
            InlineKeyboardButton(
                text="❌ Rejeter",
                callback_data=f"mod:reject:{store_id}" # Изменено для соответствия moderation_queue.py
            )
        ]
    ])

# 🛠 Админ-панель (reply-клавиатура) - используем для главного меню админа
dashboard_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Statistiques"), KeyboardButton(text="👤 Utilisateurs")],
        [KeyboardButton(text="💳 Abonnements"), KeyboardButton(text="📢 Publicités")],
        [KeyboardButton(text="🧑‍💼 Clients"), KeyboardButton(text="⚙️ Paramètres")],
        [KeyboardButton(text="🧾 À modérer")] # Добавлена кнопка для модерации
    ],
    resize_keyboard=True,
    one_time_keyboard=False # Пусть будет всегда видимой, если админ в админ-панели
)

# 📋 Кнопки управления магазином (инлайн) - используется в admin_users
def get_store_menu(store_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Voir les infos", callback_data=f"view:{store_id}")],
        [InlineKeyboardButton(text="✏️ Modifier", callback_data=f"edit:{store_id}")],
        [InlineKeyboardButton(text="🗑 Supprimer", callback_data=f"delete:{store_id}")]
    ])
    