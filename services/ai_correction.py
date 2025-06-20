import os
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def correct_car_info(marque: str, modele: str, annee: str) -> dict:
    prompt = (
        f"Corrige les informations du véhicule et retourne-les en JSON uniquement:\n"
        f"Marque: {marque}, Modèle: {modele}, Année: {annee}\n"
        f"Format: {{\"marque\": \"...\ИСПРАВЛЕНО, \"modele\": \"...\ИСПРАВЛЕНО, \"annee\": \"...\ИСПРАВЛЕНО}}."
        f"Si une information n'est pas claire, laisse-la telle quelle ou utilise 'N/A'."
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o", # Рекомендуется использовать gpt-4o или gpt-4-turbo
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={ "type": "json_object" } # Указываем, что хотим JSON-ответ
        )
        raw = response.choices[0].message.content.strip()
        # Попытка безопасного парсинга JSON
        import json
        return json.loads(raw)
    except Exception as e:
        print("❌ AI car info correction failed:", e)
        return {"marque": marque, "modele": modele, "annee": annee}

async def correct_part_name(nom_piece: str) -> str:
    prompt = (
        f"Corrige et standardise ce nom de pièce automobile, réponds uniquement par le nom corrigé, sans explication. "
        f"Si le nom ne peut pas être reconnu comme une pièce automobile valide ou si il est trop vague, retourne une phrase l'indiquant, par exemple 'Nom de pièce non reconnu'."
        f"Exemples de correction: 'batrie' -> 'Batterie', 'moteur v8' -> 'Moteur V8', 'disque' -> 'Disque de frein'."
        f"Entrée: {nom_piece}\nSortie:"
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o", # Рекомендуется использовать gpt-4o
            messages=[
                {"role": "system", "content": "Tu es un expert en pièces automobiles."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=50 # Ограничиваем длину ответа
        )
        result = response.choices[0].message.content.strip()
        # Дополнительная проверка на случаи, когда AI не распознал
        unrecognized_phrases = ["non reconnu", "non identifiable", "pas une pièce", "ne peut pas corriger"]
        if any(phrase in result.lower() for phrase in unrecognized_phrases):
             return "Nom de pièce non reconnu"
        return result
    except Exception as e:
        print("❌ AI part name correction failed:", e)
        return nom_piece # Возвращаем исходное имя в случае ошибки
    