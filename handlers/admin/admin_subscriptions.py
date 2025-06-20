from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.enums.parse_mode import ParseMode
from db.db import get_all_subscriptions, update_subscription, get_store_by_telegram_id
from utils.role_checker import is_admin # Импорт role_checker

router = Router()

@router.message(Command("subscriptions"))
@router.message(F.text == "💳 Abonnements") # Добавлен F.text для кнопки
async def list_subscriptions(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔️ Vous n’avez pas les droits.")
        return

    subscriptions = await get_all_subscriptions()

    if not subscriptions:
        await message.answer("❌ Aucune souscription trouvée.")
        return

    lines = ["<b>📋 Liste des abonnements :</b>"]
    for sub in subscriptions:
        plan = sub.get("plan", "Free")
        user_id = sub.get("telegram_id")
        store_name = sub.get('name') if sub.get('name') else "Inconnu"
        lines.append(
            f"\n👤 <b>{store_name}</b> (ID: <code>{user_id}</code>)\n"
            f"🔖 Plan: <b>{plan}</b>\n"
            f"📅 Expire: {sub.get('expires_at', '—')}\n"
            f"💳 Paiement: {sub.get('payment_method', '—')}"
        )
    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)
    await message.answer("Pour modifier un abonnement, utilisez /setplan <telegram_id> <Free|Pro|VIP>")


@router.message(F.text.startswith("/setplan"))
async def set_plan_command(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔️ Vous n’avez pas les droits.")
        return

    parts = message.text.strip().split()
    if len(parts) != 3:
        await message.answer("❗ Usage: /setplan <telegram_id> <Free|Pro|VIP>")
        return

    try:
        telegram_id = int(parts[1])
        plan = parts[2].capitalize()
        if plan not in ["Free", "Pro", "VIP"]:
            raise ValueError()
    except ValueError:
        await message.answer("❗ Format incorrect. Exemple: /setplan 123456789 Pro")
        return

    await update_subscription(telegram_id, plan)
    await message.answer(f"✅ Plan mis à jour pour l'utilisateur <code>{telegram_id}</code> : {plan}", parse_mode=ParseMode.HTML)
@router.message(F.text == "🔙 Retour")
async def go_back(message: types.Message):
    if not await is_admin(message.from_user.id):
        return
    await message.answer("📋 Menu principal:", reply_markup=None)  # You can add proper menu keyboard here
