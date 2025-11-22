from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from leo_bot.utils.time_utils import get_msk_time
from datetime import timedelta

def get_main_keyboard():
    keyboard = [
        ["👶 Начать сон", "🛏️ Закончить сон"],
        ["🍼 Грудное кормление", "🥛 Искусственное кормление"],
        ["⚖️ Вес ребенка", "📊 Статистика"],
        ["⏰ Следующее кормление", "📈 История веса"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_amount_keyboard():
    keyboard = [
        ["30 мл", "40 мл", "50 мл"],
        ["60 мл", "70 мл", "80 мл"],
        ["90 мл", "📝 Свое значение"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_time_keyboard():
    now = get_msk_time()
    times = []

    times.append("⏰ Сейчас")

    for i in range(1, 5):
        time_option = now - timedelta(minutes=i * 10)
        times.append(time_option.strftime("%H:%M"))

    keyboard = [
        [times[0], times[1]],
        [times[2], times[3]],
        [times[4], "📝 Свое время"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_breast_feeding_type_keyboard():
    keyboard = [
        ["Начало кормления", "Конец кормления"],
        ["Пропустить"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_breast_side_keyboard():
    keyboard = [
        ["Левая", "Правая"],
        ["Пропустить"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)