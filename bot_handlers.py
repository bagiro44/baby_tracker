from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models import Baby, Event, UserState
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

# Constants
EVENT_TYPES = {
    'feeding': '🍼 Кормление',
    'sleep': '😴 Сон',
    'diaper': '💩 Смена подгузника'
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
👶 Привет, {user.first_name}!

Я бот для отслеживания режима ребенка.

Выберите действие:
    """

    keyboard = [
        [InlineKeyboardButton("👶 Добавить ребенка", callback_data="add_baby")],
        [InlineKeyboardButton("📊 Посмотреть детей", callback_data="list_babies")],
        [InlineKeyboardButton("📝 Добавить событие", callback_data="log_event")],
        [InlineKeyboardButton("📈 Статистика", callback_data="show_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "add_baby":
        await add_baby_start(update, context)
    elif data == "list_babies":
        await list_babies(update, context)
    elif data == "log_event":
        await log_event_start(update, context)
    elif data == "show_stats":
        await show_stats_start(update, context)
    elif data.startswith("baby_"):
        baby_id = int(data.split("_")[1])
        await show_baby_menu(update, context, baby_id)
    elif data.startswith("event_"):
        baby_id = int(data.split("_")[1])
        event_type = data.split("_")[2]
        await log_event_type(update, context, baby_id, event_type)
    elif data.startswith("stats_"):
        baby_id = int(data.split("_")[1])
        await show_baby_stats(update, context, baby_id)
    elif data == "main_menu":
        await show_main_menu(update, context)


async def add_baby_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    UserState.set_state(update.effective_user.id, "awaiting_baby_name")
    await update.callback_query.edit_message_text("Введите имя ребенка:")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state = UserState.get_state(user_id)

    if not user_state:
        await update.message.reply_text("Пожалуйста, используйте кнопки меню.")
        return

    state = user_state['state']
    text = update.message.text

    if state == "awaiting_baby_name":
        UserState.set_state(user_id, "awaiting_baby_birthdate", {"name": text})
        await update.message.reply_text("Введите дату рождения ребенка (в формате ДД.ММ.ГГГГ):")

    elif state == "awaiting_baby_birthdate":
        try:
            birth_date = datetime.strptime(text, "%d.%m.%Y").date()
            state_data = user_state['data'] or {}
            baby_name = state_data.get('name', '')

            baby_id = Baby.add(baby_name, birth_date)
            UserState.clear_state(user_id)

            await update.message.reply_text(
                f"✅ Ребенок {baby_name} успешно добавлен!\n"
                f"Дата рождения: {birth_date.strftime('%d.%m.%Y')}"
            )

        except ValueError:
            await update.message.reply_text("Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ:")


async def list_babies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    babies = Baby.get_all()

    if not babies:
        await update.callback_query.edit_message_text(
            "У вас пока нет добавленных детей.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👶 Добавить ребенка", callback_data="add_baby")],
                [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
            ])
        )
        return

    keyboard = []
    for baby in babies:
        age_days = (date.today() - baby['birth_date']).days
        keyboard.append([
            InlineKeyboardButton(
                f"{baby['name']} ({age_days} дней)",
                callback_data=f"baby_{baby['id']}"
            )
        ])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main_menu")])

    await update.callback_query.edit_message_text(
        "Выберите ребенка:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_baby_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, baby_id: int):
    baby = Baby.get_by_id(baby_id)
    if not baby:
        await update.callback_query.edit_message_text("Ребенок не найден.")
        return

    age_days = (date.today() - baby['birth_date']).days

    keyboard = [
        [InlineKeyboardButton("🍼 Кормление", callback_data=f"event_{baby_id}_feeding")],
        [InlineKeyboardButton("😴 Сон", callback_data=f"event_{baby_id}_sleep")],
        [InlineKeyboardButton("💩 Подгузник", callback_data=f"event_{baby_id}_diaper")],
        [InlineKeyboardButton("📈 Статистика", callback_data=f"stats_{baby_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="list_babies")]
    ]

    text = f"""
👶 {baby['name']}
Возраст: {age_days} дней

Выберите тип события:
    """

    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def log_event_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    babies = Baby.get_all()

    if not babies:
        await update.callback_query.edit_message_text(
            "Сначала добавьте ребенка.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👶 Добавить ребенка", callback_data="add_baby")],
                [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
            ])
        )
        return

    keyboard = []
    for baby in babies:
        keyboard.append([
            InlineKeyboardButton(baby['name'], callback_data=f"baby_{baby['id']}")
        ])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main_menu")])

    await update.callback_query.edit_message_text(
        "Выберите ребенка для записи события:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def log_event_type(update: Update, context: ContextTypes.DEFAULT_TYPE, baby_id: int, event_type: str):
    baby = Baby.get_by_id(baby_id)
    event_name = EVENT_TYPES.get(event_type, event_type)

    UserState.set_state(
        update.effective_user.id,
        f"awaiting_{event_type}",
        {"baby_id": baby_id}
    )

    if event_type == "feeding":
        text = f"Введите количество молока в мл для {baby['name']}:"
    elif event_type == "sleep":
        text = f"Введите продолжительность сна в минутах для {baby['name']}:"
    elif event_type == "diaper":
        text = f"Опишите содержимое подгузника для {baby['name']}:"
    else:
        text = f"Введите детали для {event_name} {baby['name']}:"

    await update.callback_query.edit_message_text(text)


async def show_stats_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    babies = Baby.get_all()

    if not babies:
        await update.callback_query.edit_message_text(
            "Сначала добавьте ребенка.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👶 Добавить ребенка", callback_data="add_baby")],
                [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
            ])
        )
        return

    keyboard = []
    for baby in babies:
        keyboard.append([
            InlineKeyboardButton(baby['name'], callback_data=f"stats_{baby['id']}")
        ])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main_menu")])

    await update.callback_query.edit_message_text(
        "Выберите ребенка для просмотра статистики:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_baby_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, baby_id: int):
    baby = Baby.get_by_id(baby_id)
    if not baby:
        await update.callback_query.edit_message_text("Ребенок не найден.")
        return

    # Get today's events
    today_events = Event.get_today_events(baby_id)

    # Get stats for last 7 days
    stats = Event.get_stats(baby_id, 7)

    text = f"📊 Статистика для {baby['name']}\n\n"
    text += "📅 Сегодня:\n"

    # Group today's events by type
    today_summary = {}
    for event in today_events:
        event_type = event['event_type']
        if event_type not in today_summary:
            today_summary[event_type] = 0
        today_summary[event_type] += 1

    for event_type, count in today_summary.items():
        event_name = EVENT_TYPES.get(event_type, event_type)
        text += f"  {event_name}: {count}\n"

    if not today_summary:
        text += "  Событий сегодня нет\n"

    text += "\n📈 За последние 7 дней:\n"

    # Process 7-day stats
    stats_summary = {}
    for stat in stats:
        event_type = stat['event_type']
        if event_type not in stats_summary:
            stats_summary[event_type] = 0
        stats_summary[event_type] += stat['count']

    for event_type, count in stats_summary.items():
        event_name = EVENT_TYPES.get(event_type, event_type)
        text += f"  {event_name}: {count}\n"

    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data=f"baby_{baby_id}")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]

    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👶 Добавить ребенка", callback_data="add_baby")],
        [InlineKeyboardButton("📊 Посмотреть детей", callback_data="list_babies")],
        [InlineKeyboardButton("📝 Добавить событие", callback_data="log_event")],
        [InlineKeyboardButton("📈 Статистика", callback_data="show_stats")]
    ]

    if hasattr(update, 'message'):
        await update.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text(
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# Handle event details input
async def handle_event_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state = UserState.get_state(user_id)

    if not user_state:
        return

    state = user_state['state']
    text = update.message.text
    state_data = user_state['data'] or {}
    baby_id = state_data.get('baby_id')

    if not baby_id:
        await update.message.reply_text("Ошибка: ребенок не найден.")
        UserState.clear_state(user_id)
        return

    baby = Baby.get_by_id(baby_id)
    if not baby:
        await update.message.reply_text("Ошибка: ребенок не найден.")
        UserState.clear_state(user_id)
        return

    try:
        if state == "awaiting_feeding":
            amount = int(text)
            Event.add(baby_id, "feeding", amount=amount)
            await update.message.reply_text(f"✅ Кормление {amount} мл записано для {baby['name']}")

        elif state == "awaiting_sleep":
            duration = int(text)
            Event.add(baby_id, "sleep", duration=duration)
            await update.message.reply_text(f"✅ Сон продолжительностью {duration} минут записан для {baby['name']}")

        elif state == "awaiting_diaper":
            Event.add(baby_id, "diaper", notes=text)
            await update.message.reply_text(f"✅ Смена подгузника записана для {baby['name']}")

    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число.")
        return

    UserState.clear_state(user_id)
    await show_main_menu(update, context)