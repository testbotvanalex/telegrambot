from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu(role: str = "store"):
    if role == "admin":
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🛠 Panneau d'administration")],
                [KeyboardButton(text="📊 Statistiques"), KeyboardButton(text="👤 Utilisateurs")],
                [KeyboardButton(text="💳 Abonnements"), KeyboardButton(text="📢 Publicités")],
                [KeyboardButton(text="🧑‍💼 Clients"), KeyboardButton(text="⚙️ Paramètres")],
                [KeyboardButton(text="🧾 À modérer")],
                [KeyboardButton(text="➕ Nouvelle Pub"), KeyboardButton(text="➕ Nouveau Client")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Choisissez une option d'administration..."
        )
    elif role == "moderator":
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🧾 À modérer")]],
            resize_keyboard=True,
            input_field_placeholder="Actions de modération..."
        )
    else:  # store (en gast)
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📦 Demander une pièce"), KeyboardButton(text="🧾 Demande groupée")],
                [KeyboardButton(text="📄 Mes demandes"), KeyboardButton(text="📝 Mes infos")],
                [KeyboardButton(text="📊 Charger le stock"), KeyboardButton(text="📸 Lire un VIN")],
                [KeyboardButton(text="🔎 Rechercher stock"), KeyboardButton(text="❓ Aide")], # NIEUW: Zoek stock knop
                [KeyboardButton(text="📞 Contact")]
            ],
            resize_keyboard=True,
            one_time_keyboard=False,
            input_field_placeholder="Choisissez une option..."
        )
