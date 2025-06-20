from aiogram import Router, types, F
from aiogram.filters import Command
from db.db import save_stock_items # ИСПРАВЛЕНО: from db.db
import tempfile
import openpyxl
import os

router = Router()

@router.message(Command("uploadstock"))
async def ask_excel_file(message: types.Message):
    await message.answer(
        "📄 Veuillez envoyer un fichier Excel (.xlsx) contenant les articles de votre stock.\\n"
        "Le format attendu est : <b>Numéro de pièce | Nom | Quantité | Prix</b> dans la première ligne."
    )

@router.message(F.document)
async def handle_stock_file(message: types.Message):
    # Проверка на администратора (если это функция только для админов)
    # from utils.role_checker import is_admin
    # if not await is_admin(message.from_user.id):
    #     await message.answer("⛔️ Vous n’avez pas les droits pour cette action.")
    #     return

    if not message.document.file_name.endswith(".xlsx"):
        await message.answer("⚠️ Veuillez envoyer un fichier Excel au format .xlsx.")
        return

    try:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            await message.document.download(destination_file=tmp.name)
            wb = openpyxl.load_workbook(tmp.name)
            ws = wb.active

            stock_items = []
            errors = []
            # Пропускаем первую строку (заголовки)
            for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not row or all(cell is None for cell in row): # Пропускать пустые строки
                    continue
                try:
                    # Ожидаем 4 столбца
                    if len(row) < 4:
                        errors.append(f"Ligne {idx}: Nombre de colonnes insuffisant (attendu 4, trouvé {len(row)})")
                        continue

                    part_number = row[0]
                    part_name = row[1]
                    quantity = row[2]
                    price = row[3]

                    # Базовая валидация типов
                    if not all([part_number, part_name]):
                        errors.append(f"Ligne {idx}: Numéro de pièce ou nom manquant ({row})")
                        continue
                    
                    if not isinstance(quantity, (int, float)):
                        try:
                            quantity = int(quantity)
                        except (ValueError, TypeError):
                            errors.append(f"Ligne {idx}: Quantité invalide, doit être un nombre entier ({row[2]})")
                            continue
                    
                    if not isinstance(price, (int, float)):
                        try:
                            price = float(price)
                        except (ValueError, TypeError):
                            errors.append(f"Ligne {idx}: Prix invalide, doit être un nombre ({row[3]})")
                            continue

                    if quantity < 0 or price < 0:
                        errors.append(f"Ligne {idx}: Quantité ou prix négatif ({row})")
                        continue
                        
                    # Получаем store_id из user_id Telegram
                    store_id = message.from_user.id # Используем telegram_id как store_id для сохранения

                    stock_items.append({
                        "store_id": store_id,
                        "part_number": str(part_number),
                        "part_name": str(part_name),
                        "quantity": int(quantity),
                        "price": float(price)
                    })
                except Exception as e: # Общая ошибка для парсинга строки
                    errors.append(f"Ligne {idx}: Erreur de traitement ({row}) - {str(e)}")
                    continue

            if errors:
                error_message_text = "⚠️ Erreurs dans le fichier:\\n" + "\\n".join(errors[:10]) # Показать первые 10 ошибок
                if len(errors) > 10:
                    error_message_text += "\\n... et plus d'erreurs. (Voir les logs pour plus de détails)"
                await message.answer(error_message_text)
                
                if stock_items:
                    await message.answer(f"ℹ️ {len(stock_items)} articles valides seront enregistrés.")
                else:
                    return # Если нет валидных элементов, завершаем

            if stock_items:
                await save_stock_items(stock_items)
                await message.answer(f"✅ {len(stock_items)} articles ont été ajoutés au stock.")
            else:
                await message.answer("❌ Aucun article valide n'a été trouvé dans le fichier pour l'enregistrement.")


    except Exception as e:
        await message.answer(f"❌ Erreur lors du traitement du fichier: {str(e)}")
        print(f"❌ Erreur dans stock_upload: {e}") # Логируем полную ошибку

    finally:
        # Удаляем временный файл
        try:
            if 'tmp' in locals() and os.path.exists(tmp.name):
                os.remove(tmp.name)
        except Exception as e:
            print(f"❌ Erreur lors de la suppression du fichier temporaire: {e}")
