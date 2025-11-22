from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import ADMIN_USER_IDS

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("😴 Сон", callback_data="sleep")],
        [InlineKeyboardButton("🤱 Грудь", callback_data="breast_feeding")],
        [InlineKeyboardButton("🍼 Бутылочка", callback_data="bottle_feeding")],
        [InlineKeyboardButton("💩 Подгузник", callback_data="diaper")],
        [InlineKeyboardButton("⚖️ Вес", callback_data="weight")],
        [InlineKeyboardButton("⏰ След. кормление", callback_data="next_feeding")]
    ]
    return InlineKeyboardMarkup(keyboard)

def time_selection_keyboard(action):
    keyboard = [
        [InlineKeyboardButton("Сейчас", callback_data=f"time_{action}_0")],
        [
            InlineKeyboardButton("10 мин", callback_data=f"time_{action}_10"),
            InlineKeyboardButton("20 мин", callback_data=f"time_{action}_20")
        ],
        [
            InlineKeyboardButton("30 мин", callback_data=f"time_{action}_30"),
            InlineKeyboardButton("40 мин", callback_data=f"time_{action}_40")
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

def back_to_main_keyboard():
    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)