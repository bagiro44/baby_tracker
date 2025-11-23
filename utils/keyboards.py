from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.time_utils import format_time_with_offset

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("😴 Начать сон", callback_data="sleep_start_menu")],
        [InlineKeyboardButton("🛌 Завершить сон", callback_data="sleep_end_menu")],
        [InlineKeyboardButton("🤱 Начать кормление грудью", callback_data="breast_start_menu")],
        [InlineKeyboardButton("✅ Завершить кормление грудью", callback_data="breast_end_menu")],
        [InlineKeyboardButton("🍼 Кормление из бутылочки", callback_data="bottle_feeding")],
        [InlineKeyboardButton("💩 Подгузник", callback_data="diaper")],
        [InlineKeyboardButton("⚖️ Вес", callback_data="weight")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("⏰ След. кормление", callback_data="next_feeding")]
    ]
    return InlineKeyboardMarkup(keyboard)

def gender_selection_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("👦 Мальчик", callback_data="gender_male"),
            InlineKeyboardButton("👧 Девочка", callback_data="gender_female")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def time_selection_keyboard(action):
    keyboard = [
        [InlineKeyboardButton(format_time_with_offset(0), callback_data=f"time_{action}_0")],
        [
            InlineKeyboardButton(format_time_with_offset(10), callback_data=f"time_{action}_10"),
            InlineKeyboardButton(format_time_with_offset(20), callback_data=f"time_{action}_20")
        ],
        [
            InlineKeyboardButton(format_time_with_offset(30), callback_data=f"time_{action}_30"),
            InlineKeyboardButton(format_time_with_offset(40), callback_data=f"time_{action}_40")
        ],
        [InlineKeyboardButton("Свое время", callback_data=f"time_{action}_custom")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def bottle_volume_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("20мл", callback_data="volume_20"),
            InlineKeyboardButton("30мл", callback_data="volume_30"),
            InlineKeyboardButton("40мл", callback_data="volume_40")
        ],
        [
            InlineKeyboardButton("50мл", callback_data="volume_50"),
            InlineKeyboardButton("60мл", callback_data="volume_60"),
            InlineKeyboardButton("70мл", callback_data="volume_70")
        ],
        [InlineKeyboardButton("Свой объем", callback_data="volume_custom")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def breast_side_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("👈 Левая", callback_data="breast_left"),
            InlineKeyboardButton("Правая 👉", callback_data="breast_right")
        ],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def diaper_type_keyboard():
    keyboard = [
        [InlineKeyboardButton("💦 Мокрый", callback_data="diaper_wet")],
        [InlineKeyboardButton("💩 Грязный", callback_data="diaper_dirty")],
        [InlineKeyboardButton("💦💩 Смешанный", callback_data="diaper_mixed")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def stats_period_keyboard():
    keyboard = [
        [InlineKeyboardButton("📅 Сегодня", callback_data="stats_today")],
        [InlineKeyboardButton("📆 Последние 24 часа", callback_data="stats_24h")],
        [InlineKeyboardButton("🗓️ Последние 3 дня", callback_data="stats_3days")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)