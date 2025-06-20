import os
from dotenv import load_dotenv
from pathlib import Path

# Загрузка переменных окружения из .env файла
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_FILE = os.getenv("DB_FILE", "bot.db") # Путь к файлу базы данных

# ID администраторов и групп (убедитесь, что они установлены в .env)
TELEGRAM_ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))
TELEGRAM_ADMIN_USER_IDS = [int(x.strip()) for x in os.getenv("TELEGRAM_ADMIN_USER_IDS", "").split(",") if x.strip().isdigit()]
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0")) # Дублирование, но оставлено для совместимости

TELEGRAM_ADMIN_GROUP_ID = int(os.getenv("TELEGRAM_ADMIN_GROUP_ID", "0"))
TELEGRAM_MOD_GROUP_ID = int(os.getenv("TELEGRAM_MOD_GROUP_ID", "0"))

# Более унифицированные названия для групп
ADMIN_GROUP_ID = TELEGRAM_ADMIN_GROUP_ID
MODERATION_GROUP_ID = TELEGRAM_MOD_GROUP_ID

# Для тестов (если есть)
TEST_STORE_ID = int(os.getenv("TEST_STORE_ID", "0"))

# Для Cloud Run
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ENV = os.getenv("ENV", "local")