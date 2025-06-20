from aiogram import Router, types, F
from aiogram.filters import Command
from keyboards.admin import dashboard_keyboard
from keyboards.menu import get_main_menu
from utils.role_checker import is_admin
from db.db import get_stats_summary # ИСПРАВЛЕНО: from db.db
# Импорты хендлеров для перенаправления
from handlers.admin.admin_users import list_users
from handlers.admin.admin_subscriptions import list_subscriptions
# from handlers.admin.admin_ads import list_ads # Если нужно перенаправить на список рекламы
# from handlers.admin.admin_clients import list_clients # Если нужно перенаправить на список клиентов


router = Router()

@router.message(Command("dashboard"))
@router.message(F.text == "🛠 Panneau d'administration")
async def show_dashboard(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔️ Vous n’avez pas accès à ce panneau.")
        return

    await message.answer(
        "🛠 Panneau d'administration :\nChoisissez une section à gérer :",
        reply_markup=dashboard_keyboard
    )

@router.message(F.text == "📊 Statistiques")
async def handle_stats(message: types.Message):
    if not await is_admin(message.from_user.id):
        return
    stats = await get_stats_summary()
    await message.answer(
        f"📊 <b>Statistiques</b>\n\n"
        f"🏪 Magasins enregistrés: <b>{stats['total_stores']}</b>\n"
        f"✅ Magasins approuvés: <b>{stats['stores_approved']}</b>\n"
        f"📬 Demandes envoyées: <b>{stats['total_requests']}</b>\n"
        f"💬 Réponses enregistrées: <b>{stats['total_offers']}</b>\n\n"
        f"<b>Abonnements:</b>\n"
        f"🆓 Gratuits: <b>{stats['users_free']}</b>\n"
        f"🌟 Pro: <b>{stats['users_pro']}</b>\n"
        f"💎 VIP: <b>{stats['users_vip']}</b>\n\n"
        f"📢 Publicités actives: <b>{stats['active_ads']}</b>\n"
        f"💰 Revenu total estimé: <b>{stats['total_revenue']:.2f}</b>",
        parse_mode="HTML"
    )

@router.message(F.text == "👤 Utilisateurs")
async def handle_users(message: types.Message):
    if not await is_admin(message.from_user.id):
        return
    await message.answer("Redirection vers la gestion des utilisateurs...")
    await list_users(message)

@router.message(F.text == "💳 Abonnements")
async def handle_subscriptions(message: types.Message):
    if not await is_admin(message.from_user.id):
        return
    await message.answer("Redirection vers la gestion des abonnements...")
    await list_subscriptions(message)

@router.message(F.text == "💰 Revenus")
async def handle_revenue(message: types.Message):
    if not await is_admin(message.from_user.id):
        return
    stats = await get_stats_summary()
    await message.answer(
        f"💰 <b>Revenus</b>\n\n"
        f"Total estimé: <b>{stats['total_revenue']:.2f}</b>",
        parse_mode="HTML"
    )

@router.message(F.text == "↩ Retour")
async def go_back_to_menu(message: types.Message):
    if not await is_admin(message.from_user.id):
        return
    await message.answer(
        "📋 Menu principal:",
        reply_markup=get_main_menu("admin")
    )

@router.message(F.text == "❌ Quitter")
async def quit_dashboard(message: types.Message):
    if not await is_admin(message.from_user.id):
        return
    await message.answer("👋 Au revoir !", reply_markup=get_main_menu("admin"))
