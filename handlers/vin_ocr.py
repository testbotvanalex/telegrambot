import os
from openai import AsyncOpenAI # Изменено на AsyncOpenAI
import aiohttp
import base64
import hashlib
import aiosqlite
from aiogram import Router, F
from aiogram.types import Message
from config.config import OPENAI_API_KEY, DB_FILE # Изменено на config.config

router = Router()

client = AsyncOpenAI(api_key=OPENAI_API_KEY) # Инициализируем AsyncOpenAI

@router.message(F.text == "📸 Lire un VIN / numéro") # Если есть такая кнопка в меню
async def prompt_photo(message: Message):
    await message.answer("📷 Envoyez une photo contenant un numéro ou un code VIN.")

@router.message(F.photo)
async def process_vin_photo(message: Message):
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_path = file.file_path
    file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file_path}"

    # Кэширование по хэшу пути
    photo_hash = hashlib.md5(file_path.encode()).hexdigest()
    cached_result = await get_cached_vin(photo_hash)
    if cached_result:
        await message.answer(f"🔍 Résultat détecté (from cache):\n<code>{cached_result}</code>", parse_mode="HTML")
        return

    await message.answer("⏳ Analyse de l'image en cours...")
    try:
        result = await call_vision_api(file_url)
        await save_cached_vin(photo_hash, result)
        await message.answer(f"🔍 Résultat détecté:\n<code>{result}</code>", parse_mode="HTML")
    except Exception as e:
        await message.answer("❌ Erreur lors de l’analyse de la photo. Réessayez.")
        print(f"❌ Erreur dans vin_ocr: {e}")

async def call_vision_api(image_url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as resp:
            if resp.status != 200:
                raise Exception("Erreur lors du téléchargement de l’image.")
            image_data = await resp.read()

    base64_image = base64.b64encode(image_data).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{base64_image}"

    response = await client.chat.completions.create( # Использование AsyncOpenAI клиента
        model="gpt-4o", # Лучше использовать 'gpt-4o' или 'gpt-4-turbo' для vision
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Lis et extrait uniquement le numéro ou code VIN visible sur cette image. Si tu ne vois pas de VIN, indique tout autre numéro de série ou de pièce clairement visible."},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        max_tokens=100,
    )
    return response.choices[0].message.content.strip()

async def get_cached_vin(photo_hash: str) -> str:
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT result FROM vin_cache WHERE photo_hash = ?", (photo_hash,))
        row = await cursor.fetchone()
        return row["result"] if row else None

async def save_cached_vin(photo_hash: str, result: str):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS vin_cache (
                photo_hash TEXT PRIMARY KEY,
                result TEXT,
                cached_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("INSERT OR REPLACE INTO vin_cache (photo_hash, result) VALUES (?, ?)", (photo_hash, result))
        await db.commit()
        