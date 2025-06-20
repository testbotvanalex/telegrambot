from aiogram import Router, types, F
from aiogram.filters import Command
from utils.role_checker import is_admin
from db.db import get_stats_summary

router = Router()

@router.message(Command("stats"))
@router.message(F.text == "📊 Statistiques")
async def show_analytics(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔️ Vous n'avez pas accès à cette section.")
        return

    stats = await get_stats_summary()

    await message.answer(
        f"📈 <b>Statistiques générales</b>\n\n"
        f"🏪 <b>Magasins enregistrés :</b> {stats['total_stores']}\n"
        f"✅ <b>Magasins approuvés :</b> {stats['stores_approved']}\n"
        f"📬 <b>Demandes envoyées :</b> {stats['total_requests']}\n"
        f"💬 <b>Offres reçues :</b> {stats['total_offers']}\n\n"
        f"<b>Abonnements:</b>\n"
        f"🆓 Gratuits: <b>{stats['users_free']}</b>\n"
        f"🌟 Pro: <b>{stats['users_pro']}</b>\n"
        f"💎 VIP: <b>{stats['users_vip']}</b>\n\n"
        f"📢 Publicités actives: <b>{stats['active_ads']}</b>\n"
        f"💰 Revenu total estimé: <b>{stats['total_revenue']:.2f} €</b>", # Форматируем доход с валютой
        parse_mode="HTML"
    )
async def get_stats_summary():
    # Получаем данные из базы данных
    total_stores = await db.get_total_stores()
    stores_approved = await db.get_approved_stores_count()
    total_requests = await db.get_total_requests()
    total_offers = await db.get_total_offers()
    users_free = await db.get_users_count_by_role('free')
    users_pro = await db.get_users_count_by_role('pro')
    users_vip = await db.get_users_count_by_role('vip')
    active_ads = await db.get_active_ads_count()
    total_revenue = await db.get_total_revenue()  # Предполагается, что эта функция возвращает доход в евро или другой валюте
    return {
        "total_stores": total_stores,
        "stores_approved": stores_approved,
        "total_requests": total_requests,
        "total_offers": total_offers,
        "users_free": users_free,
        "users_pro": users_pro,
        "users_vip": users_vip,
        "active_ads": active_ads,
        "total_revenue": total_revenue
    }