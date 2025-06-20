from aiogram import Router, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from db.db import get_pending_stores, approve_store, reject_store, get_store_by_telegram_id # ИСПРАВЛЕНО: from db.db
from config.config import TELEGRAM_MOD_GROUP_ID as MOD_GROUP_ID, TELEGRAM_ADMIN_GROUP_ID as ADMIN_GROUP_ID # ИСПРАВЛЕНО: из config.config
from utils.role_checker import is_admin # ИСПРАВЛЕНО: из utils.role_checker

router = Router()

@router.message(Command("modérer"))
@router.message(F.text == "🧾 À modérer") # Если есть кнопка для этого
async def show_pending_stores(message: Message, state: FSMContext):
    # Проверка, является ли пользователь админом или находится в группе модерации
    if not (await is_admin(message.from_user.id) or message.chat.id == MOD_GROUP_ID):
        await message.answer("⛔️ Vous n’avez pas accès à la file de modération.")
        return

    await state.clear()
    pending_stores = await get_pending_stores()
    if not pending_stores:
        await message.answer("✅ Aucun magasin en attente.")
        return

    for store in pending_stores:
        text = (
            f"🧾 <b>Demande de validation</b>\n"
            f"👤 <b>@{store['username'] or '—'}</b> (ID: <code>{store['telegram_id']}</code>)\n"
            f"🏪 <b>Magasin:</b> {store['name']}\n"
            f"📍 <b>Adresse:</b> {store['address']} — {store['city']}\n"
            f"📦 <b>Catégories:</b> {store['categories']}\n"
            f"📞 <b>Contact:</b> {store['contact'] or '—'}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approuver", callback_data=f"mod:approve:{store['telegram_id']}"),
                InlineKeyboardButton(text="❌ Rejeter", callback_data=f"mod:reject:{store['telegram_id']}")
            ]
        ])
        await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@router.callback_query(F.data.startswith("mod:approve:"))
async def approve_callback(call: CallbackQuery):
    if not (await is_admin(call.from_user.id) or call.message.chat.id == MOD_GROUP_ID):
        await call.answer("⛔️ Vous n’avez pas les droits.", show_alert=True)
        return

    telegram_id = int(call.data.split(":")[2])
    store = await get_store_by_telegram_id(telegram_id)
    if not store:
        await call.answer("❌ Déjà traité ou introuvable.", show_alert=True)
        return

    if store.get("approved"): # Проверка, если уже одобрен
        await call.answer("✅ Ce magasin est déjà approuvé.", show_alert=True)
        return

    await approve_store(telegram_id, True)
    await call.message.edit_text( # Обновляем сообщение, чтобы оно не висело
        f"✅ Magasin approuvé: @{store['username'] or '—'} (ID: {telegram_id})",
        parse_mode=ParseMode.HTML,
        reply_markup=None # Удаляем кнопки
    )

    admin_text = ( # Сообщение для админ-группы
        f"✅ <b>Magasin approuvé</b>\n"
        f"👤 <b>@{store['username'] or '—'}</b> (ID: <code>{telegram_id}</code>)\n"
        f"🏪 <b>Nom:</b> {store['name']}\n"
        f"📍 <b>Adresse:</b> {store['address']} — {store['city']}\n"
        f"🛒 <b>Catégories:</b> {store['categories']}\n"
        f"📞 <b>Contact:</b> {store['contact'] or '—'}"
    )
    if ADMIN_GROUP_ID != 0: # Отправляем сообщение в админ-группу
        await call.bot.send_message(chat_id=ADMIN_GROUP_ID, text=admin_text, parse_mode=ParseMode.HTML)


    try: # Отправляем уведомление пользователю
        await call.bot.send_message(
            chat_id=telegram_id,
            text="✅ <b>Félicitations !</b> Votre magasin a été approuvé 🎉\nVous pouvez maintenant utiliser toutes les fonctionnalités du bot.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(f"⚠️ Impossible d’envoyer le message d’approbation à l’utilisateur {telegram_id}: {e}")
        if ADMIN_GROUP_ID != 0:
            await call.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=f"⚠️ Impossible d’envoyer le message d’approbation à l’utilisateur <code>{telegram_id}</code>.",
                parse_mode=ParseMode.HTML
            )

    await call.answer("✅ Approuvé.")


@router.callback_query(F.data.startswith("mod:reject:"))
async def reject_callback(call: CallbackQuery):
    if not (await is_admin(call.from_user.id) or call.message.chat.id == MOD_GROUP_ID):
        await call.answer("⛔️ Vous n’avez pas les droits.", show_alert=True)
        return

    telegram_id = int(call.data.split(":")[2])
    store = await get_store_by_telegram_id(telegram_id)
    if not store:
        await call.answer("❌ Déjà traité ou introuvable.", show_alert=True)
        return

    if store.get("approved"): # Проверка, если уже одобрен
        await call.answer("⚠️ Magasin déjà approuvé — rejet impossible.", show_alert=True)
        return

    await reject_store(telegram_id) # Удаляем запись магазина
    await call.message.edit_text( # Обновляем сообщение
        f"❌ Magasin rejeté: @{store['username'] or '—'} (ID: {telegram_id})",
        parse_mode=ParseMode.HTML,
        reply_markup=None # Удаляем кнопки
    )

    try: # Отправляем уведомление пользователю
        await call.bot.send_message(
            chat_id=telegram_id,
            text="❌ <b>Désolé</b>, votre demande a été rejetée. Vous pouvez réessayer plus tard.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(f"⚠️ Impossible d’envoyer le message de rejet à l’utilisateur {telegram_id}: {e}")
        if ADMIN_GROUP_ID != 0:
            await call.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=f"⚠️ Impossible d’envoyer le rejet à l’utilisateur <code>{telegram_id}</code>.",
                parse_mode=ParseMode.HTML
            )

    await call.answer("❌ Rejeté.")
