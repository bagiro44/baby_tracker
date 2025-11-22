"""
Инициализация трекера для избежания циклических импортов
"""

from leo_bot.database.sheets import GoogleSheetsBabyTracker
from leo_bot.config import GOOGLE_CREDENTIALS_FILE, SPREADSHEET_NAME

# Создаем экземпляр трекера
tracker = GoogleSheetsBabyTracker(GOOGLE_CREDENTIALS_FILE, SPREADSHEET_NAME)