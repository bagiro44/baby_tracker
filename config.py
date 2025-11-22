import os
import logging
from datetime import timezone, timedelta
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# === НАСТРОЙКИ ИЗ .env ===
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
SPREADSHEET_NAME = os.getenv('SPREADSHEET_NAME', 'Baby Tracker')
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
CHAT_ID = "-" + os.getenv('CHAT_ID') if os.getenv('CHAT_ID') else None

# Проверка обязательных переменных
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле")
if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS не найдены в .env файле")

# Московский часовой пояс (UTC+3)
MSK_TIMEZONE = timezone(timedelta(hours=3))

# Состояния для ConversationHandler
(SELECTING_AMOUNT, CUSTOM_AMOUNT, ENTERING_WEIGHT, SELECTING_TIME,
 ENTERING_CUSTOM_TIME, SELECTING_SLEEP_TIME, BREAST_FEEDING_TYPE, BREAST_FEEDING_SIDE) = range(8)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)