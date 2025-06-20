from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from db.db import get_requests_by_store, get_offers_by_request_id, mark_offer_as_chosen # Исправлено: mark_offer_as_chosen из db

router = Router()

@router.message(F.text == "✉️ Choisir une offre") # Если есть такая кнопка в меню
async def show_offers_menu(message: Message):
    requests = await get_requests_by_store(message.from_user.id) # Получаем запросы, сделанные этим магазином
    if not requests:
        await message.answer("🛋 Vous n’avez pas encore fait de demandes.")
        return

    found_offers = False
    for req in requests:
        offers = await get_offers_by_request_id(req["id"]) # Получаем предложения по каждой из этих заявок
        if not offers:
            continue

        found_offers = True
        
        # Фильтруем выбранные предложения, если они уже есть
        active_offers = [offer for offer in offers if not offer.get('selected')]
        
        if not active_offers:
            await message.answer(
                f"🔍 Aucune nouvelle offre pour: <b>{req['part_name']}</b> ({req['car']}).",
                parse_mode="HTML"
            )
            continue


        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"✅ {offer.get('price', 'N/A')} € ({offer.get('delivery', 'N/A')})",
                        callback_data=f"choose_offer:{offer['id']}"
                    )
                ] for offer in active_offers
            ]
        )

        await message.answer(
            f"🔍 <b>Offres pour:</b> {req['part_name']} ({req['car']})",
            reply_markup=kb,
            parse_mode="HTML"
        )
    
    if not found_offers:
        await message.answer("🛋 Aucune nouvelle offre trouvée pour vos demandes.")


@router.callback_query(F.data.startswith("choose_offer:"))
async def choose_offer_callback(call: CallbackQuery):
    offer_id = int(call.data.split(":")[1])
    
    selected_offer_data = await mark_offer_as_chosen(offer_id) # Обновляем статус в БД и получаем данные
    
    if not selected_offer_data:
        await call.answer("❌ Erreur lors de la sélection de l'offre.", show_alert=True)
        return

    # Отключаем кнопки под сообщением с предложением
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(f"✅ Offre sélectionnée. Vous pouvez contacter le vendeur.")
    await call.answer("Offre enregistrée avec succès.")

    # Уведомляем продавца, что его предложение было выбрано
    responder_id = selected_offer_data['responder_id']
    responder_username = selected_offer_data['responder_username']
    request_id = selected_offer_data['request_id']
    offer_text = selected_offer_data['offer_text']

    try:
        await call.bot.send_message(
            chat_id=responder_id,
            text=f"🎉 Votre offre pour la demande #{request_id} a été sélectionnée !\n\n"
                 f"Votre offre: <code>{offer_text}</code>\n"
                 f"Pour contacter le demandeur: @{call.from_user.username or call.from_user.full_name}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"❌ Erreur en envoyant la notification au vendeur {responder_id}: {e}")
        await call.message.answer(f"⚠️ Impossible d'envoyer une notification au vendeur ({responder_username}).")
        return
    # Удаляем предложения из базы данных
    await delete_offers_by_request_id(request_id)  # Удаляем все предложения по этому запросу
    await call.message.answer("Toutes les autres offres pour cette demande ont été supprimées.")
    # Уведомляем всех остальных продавцов, что их предложения были отклонены
    for offer in selected_offer_data['other_offers']:
        if offer['id'] != offer_id:
            try:
                await call.bot.send_message(
                    chat_id=offer['responder_id'],
                    text=f"❌ Votre offre pour la demande #{request_id} a été rejetée.\n"
                         f"Pour contacter le demandeur: @{call.from_user.username or call.from_user.full_name}",
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"❌ Erreur en envoyant la notification au vendeur {offer['responder_id']}: {e}")
                await call.message.answer(f"⚠️ Impossible d'envoyer une notification au vendeur ({offer['responder_username']}).")
    # Уведомляем продавца, что его предложение было отклонено
    await call.message.answer("❌ Votre offre a été rejetée.")
    await call.answer() # Завершаем колбэк, чтобы убрать крутящийся индикатор загрузки  
@router.callback_query(F.data == "cancel_choose_offer")
async def cancel_choose_offer_callback(call: CallbackQuery):
    await call.message.edit_text("Sélection d'offre annulée.", reply_markup=None)
    await call.answer() # Завершаем колбэк, чтобы убрать крутящийся индикатор загрузки