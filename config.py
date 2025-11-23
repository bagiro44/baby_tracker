import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT', '6432'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    # 'sslmode': 'verify-full',
    # 'sslrootcert': 'root.crt'
}

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_USER_IDS = list(map(int, os.getenv('ADMIN_USER_IDS', '').split(',')))
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

FEEDING_INTERVAL_HOURS = 3
REMINDER_MINUTES_BEFORE = 30

TIMEZONE = 'Europe/Moscow'