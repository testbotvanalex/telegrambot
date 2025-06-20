from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.role_checker import is_admin
from db.db import create_ad, get_ads_list, toggle_ad_status, delete_ad, get_client_by_id
import textwrap

router = Router()

class AdCreation(StatesGroup):
    waiting_for_text = State()
    waiting_for_button_text = State()
    waiting_for_button_url = State()
    waiting_for_target = State()
    waiting_for_dates = State()
    waiting_for_client_id = State()
    waiting_for_approval = State()

@router.message(Command("newad"))
async def start_new_ad(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔️ Vous n'avez pas les droits.")
        return

    await message.answer("📝 Entrez le texte de l'annonce :")
    await state.set_state(AdCreation.waiting_for_text)

@router.message(AdCreation.waiting_for_text)
async def get_ad_text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer(
        "🔗 Entrez le **texte du bouton** (par ex. 'Visiter le site') ou tapez `/skip` pour ignorer :",
        parse_mode="Markdown"
    )
    await state.set_state(AdCreation.waiting_for_button_text)

@router.message(AdCreation.waiting_for_button_text, F.text == "/skip")
async def skip_button_text(message: types.Message, state: FSMContext):
    await state.update_data(button_text=None, button_url=None)
    await message.answer("🎯 Ciblez cette pub : \nEnvoyez une catégorie (par ex. 'Moteur'), 'all' pour tous, ou tapez `/skip` :", parse_mode="Markdown")
    await state.set_state(AdCreation.waiting_for_target)

@router.message(AdCreation.waiting_for_button_text)
async def get_button_text_value(message: types.Message, state: FSMContext):
    await state.update_data(button_text=message.text.strip())
    await message.answer(
        "🌐 Entrez l'**URL du bouton** (doit commencer par http:// ou https://) ou tapez `/skip` pour ignorer :", # ИСПРАВЛЕНО: добавлено /skip
        parse_mode="Markdown"
    )
    await state.set_state(AdCreation.waiting_for_button_url)

@router.message(AdCreation.waiting_for_button_url, F.text == "/skip") # ИСПРАВЛЕНО: добавлена обработка /skip для URL
async def skip_button_url(message: types.Message, state: FSMContext):
    await state.update_data(button_url=None)
    await message.answer("🎯 Ciblez cette pub : \nEnvoyez une catégorie (par ex. 'Moteur'), 'all' pour tous, ou tapez `/skip` :", parse_mode="Markdown")
    await state.set_state(AdCreation.waiting_for_target)

@router.message(AdCreation.waiting_for_button_url)
async def get_button_url(message: types.Message, state: FSMContext):
    url = message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        await message.answer("❌ URL invalide. L'URL doit commencer par `http://` ou `https://`. Réessayez ou tapez `/skip` pour ignorer le bouton.")
        return

    await state.update_data(button_url=url)
    await message.answer("🎯 Ciblez cette pub : \nEnvoyez une catégorie (par ex. 'Moteur'), 'all' pour tous, ou tapez `/skip` :", parse_mode="Markdown")
    await state.set_state(AdCreation.waiting_for_target)


@router.message(AdCreation.waiting_for_target, F.text == "/skip")
async def skip_target(message: types.Message, state: FSMContext):
    await state.update_data(target="all")
    await message.answer("📅 Entrez la période (ex: `2025-06-20 > 2025-06-25`) :", parse_mode="Markdown")
    await state.set_state(AdCreation.waiting_for_dates)

@router.message(AdCreation.waiting_for_target)
async def get_target(message: types.Message, state: FSMContext):
    await state.update_data(target=message.text.strip())
    await message.answer("📅 Entrez la période (ex: `2025-06-20 > 2025-06-25`) :", parse_mode="Markdown")
    await state.set_state(AdCreation.waiting_for_dates)

@router.message(AdCreation.waiting_for_dates)
async def get_dates(message: types.Message, state: FSMContext):
    try:
        start_date_str, end_date_str = [d.strip() for d in message.text.split(">")]
        # TODO: Добавить валидацию формата даты (YYYY-MM-DD)
    except ValueError:
        await message.answer("❌ Format de date invalide. Utilisez: `AAAA-MM-JJ > AAAA-MM-JJ`. Réessayez.")
        return

    await state.update_data(start_date=start_date_str, end_date=end_date_str)
    
    await message.answer("🆔 Entrez l'ID du client (numérique) auquel lier cette pub, ou tapez `/skip` :", parse_mode="Markdown")
    await state.set_state(AdCreation.waiting_for_client_id)

@router.message(AdCreation.waiting_for_client_id, F.text == "/skip")
async def skip_client_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await create_ad(
        text=data['text'],
        button=data.get('button_text'), # Используем button_text
        target=data['target'],
        start_date=data['start_date'],
        end_date=data['end_date'],
        client_id=None
    )
    await message.answer("✅ Publicité créée avec succès (non liée à un client).")
    await state.clear()


@router.message(AdCreation.waiting_for_client_id)
async def get_client_id_value(message: types.Message, state: FSMContext):
    try:
        client_id = int(message.text.strip())
        client = await get_client_by_id(client_id)
        if not client:
            await message.answer("❌ Client non trouvé avec cet ID. Veuillez entrer un ID de client valide ou tapez `/skip`.")
            return
            
        data = await state.get_data()
        await create_ad(
            text=data['text'],
            button=data.get('button_text'),
            target=data['target'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            client_id=client_id
        )
        await message.answer(f"✅ Publicité créée avec succès et liée au client **{client.get('name', 'N/A')}** (ID: <code>{client_id}</code>).", parse_mode="HTML")
        await state.clear()
    except ValueError:
        await message.answer("❌ ID client invalide. Veuillez entrer un nombre ou tapez `/skip`.")


@router.message(Command("ads"))
@router.message(F.text == "📢 Publicités")
async def list_ads(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔️ Vous n'avez pas les droits.")
        return

    ads = await get_ads_list()
    if not ads:
        await message.answer("📭 Aucune publicité active.")
        return

    for ad in ads:
        status = "✅ Active" if ad["active"] else "⏸️ En pause"
        client_info = ""
        if ad.get('client_id'):
            client = await get_client_by_id(ad['client_id'])
            if client:
                client_info = f"Client: {client.get('name', 'N/A')} (ID: {ad['client_id']})"
            else:
                client_info = f"Client ID: {ad['client_id']} (introuvable)"
        else:
            client_info = "Pas de client lié"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🟢 Activer" if not ad["active"] else "⏸️ Suspendre", callback_data=f"togglead:{ad['id']}"),
                InlineKeyboardButton(text="🗑 Supprimer", callback_data=f"deletead:{ad['id']}")
            ],
        ])
        await message.answer(
            f"📢 <b>Annonce</b> #{ad['id']}\n"
            f"Texte: {textwrap.shorten(ad['text'], 100, placeholder='...')}\n"
            f"Bouton: {ad['button'] or 'Aucun'}\n"
            f"Statut: {status}\n"
            f"Cible: {ad['target']}\n"
            f"Période: {ad['start_date']} > {ad['end_date']}\n"
            f"<i>{client_info}</i>",
            parse_mode="HTML",
            reply_markup=kb
        )

@router.callback_query(F.data.startswith("togglead:"))
async def toggle_ad(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔️ Vous n'avez pas les droits.", show_alert=True)
        return

    ad_id = int(callback.data.split(":")[1])
    await toggle_ad_status(ad_id)
    await callback.answer("🔁 Statut mis à jour.", show_alert=True)
    await callback.message.delete()

@router.callback_query(F.data.startswith("deletead:"))
async def delete_ad_cb(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔️ Vous n'avez pas les droits.", show_alert=True)
        return

    ad_id = int(callback.data.split(":")[1])
    await delete_ad(ad_id)
    await callback.answer("🗑 Supprimé.", show_alert=True)
    await callback.message.delete()
