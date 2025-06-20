from aiogram import Router, types, F
from db.db import save_offer_response # Используем save_offer_response из db

router = Router()

@router.callback_query(F.data.startswith("offer:")) # Обработка колбэков, начинающихся с "offer:"
async def handle_offer_response(callback: types.CallbackQuery):
    try:
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer("❌ Format incorrect.", show_alert=True)
            return

        response_type = parts[1]  # have / soon / none
        request_id = int(parts[2])

        # Сохраняем только тип ответа. Детали (цена, ETA) запрашиваются отдельно.
        # Это та часть, которая была в responses_handler.py и просто отвечала "да/нет/скоро"
        await save_offer_response( # Используем save_offer_response
            request_id=request_id,
            store_id=callback.from_user.id, # ID магазина, который отвечает
            price="-", # Можно запросить позже или оставить "-", если это первый ответ
            eta="-",
            delivery=response_type # Здесь хранится "have", "soon" или "none"
        )

        responses = {
            "have": "📦 Merci, vous avez indiqué avoir cette pièce. Le demandeur pourra vous contacter.",
            "soon": "🕒 Merci, vous avez indiqué que la pièce arrive bientôt. Le demandeur pourra vous contacter.",
            "none": "❌ Merci, vous avez indiqué ne pas avoir cette pièce."
        }

        if response_type in responses:
            await callback.message.edit_text(responses[response_type], reply_markup=None) # Удаляем кнопки после ответа
        else:
            await callback.answer("❌ Réponse inconnue.", show_alert=True)

        await callback.answer()

    except Exception as e:
        print(f"❌ Erreur dans handle_offer_response: {e}")
        await callback.answer("❌ Une erreur est survenue.", show_alert=True)

# Этот роутер будет обрабатывать offers:have/soon/none
# offer_reply.py, который был ранее, можно не использовать, если эта логика покроет все
# Если нужна детализация ответа (цена, ETA), то нужно добавить FSM здесь или в отдельном хендлере.
# Если нужно, чтобы пользователь мог ввести цену и ETA, то можно добавить отдельный хендлер для этого