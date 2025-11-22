import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'baby_tracker'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

# Telegram Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Other settings
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))