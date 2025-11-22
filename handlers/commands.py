from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from datetime import datetime, timedelta
import re
from leo_bot.config import logger, MSK_TIMEZONE
from leo_bot.utils.telegram_utils import check_access, get_user_display_name, send_to_chat
from leo_bot.utils.time_utils import get_msk_time
from leo_bot.utils.reminders import schedule_feeding_reminder, send_feeding_reminder
from leo_bot.keyboards.menus import get_main_keyboard

# Импортируем tracker из модуля tracker, чтобы избежать циклических импортов
from leo_bot.tracker import tracker


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start для приветствия"""
    if not await check_access(update):
        return

    stats = tracker.get_stats()

    welcome_text = (
        "👶 Добро пожаловать в BabyTracker!\n\n"
        "📊 Текущая статистика:\n"
        f"• Всего сеансов сна: {stats.get('total_sleep_sessions', 0)}\n"
        f"• Всего кормлений: {stats.get('total_feedings', 0)}\n"
        f"• Кормлений сегодня: {stats.get('today_feedings', 0)}\n"
        f"• Искусственных кормлений сегодня: {stats.get('today_bottle_feedings', 0)}\n"
        f"• Всего смеси сегодня: {stats.get('total_bottle_amount', 0)} мл\n"
        f"• Последнее искусственное кормление: {stats.get('last_bottle_feeding', 'еще не было')}\n"
        f"• Последний вес: {stats.get('last_weight', 'нет данных')}\n"
        f"• Активный сон: {'🔴 Да' if stats.get('active_sleep') else '🟢 Нет'}\n\n"
        "💡 Просто нажимайте на кнопки ниже для записи событий!\n"
        "⏰ Напоминания о кормлении приходят через 2.5 часа"
    )

    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())


async def start_sleep_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для начала сна"""
    if not await check_access(update):
        return
    user_id = update.effective_user.id
    result = tracker.start_sleep(user_id)

    user_name = await get_user_display_name(update)
    chat_message = (
        f"😴 <b>Малыш уснул</b>\n\n"
        f"• Время: {get_msk_time().strftime('%H:%M')}\n"
        f"• Внес: {user_name}"
    )
    await send_to_chat(context, chat_message)
    await update.message.reply_text(result, reply_markup=get_main_keyboard())


async def end_sleep_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для окончания сна"""
    if not await check_access(update):
        return
    user_id = update.effective_user.id
    result = tracker.end_sleep(user_id)

    duration_match = re.search(r'Продолжительность: (\d+)ч (\d+)м', result)
    if duration_match:
        hours = duration_match.group(1)
        minutes = duration_match.group(2)

        user_name = await get_user_display_name(update)
        chat_message = (
            f"🛌 <b>Малыш проснулся</b>\n\n"
            f"• Время: {get_msk_time().strftime('%H:%M')}\n"
            f"• Продолжительность сна: {hours}ч {minutes}м\n"
            f"• Внес: {user_name}"
        )
        await send_to_chat(context, chat_message)

    await update.message.reply_text(result, reply_markup=get_main_keyboard())


async def breastfeeding_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для грудного кормления"""
    if not await check_access(update):
        return
    user_id = update.effective_user.id
    result = tracker.add_feeding(user_id, "breast")

    user_name = await get_user_display_name(update)
    chat_message = (
        f"🍼 <b>Грудное кормление</b>\n\n"
        f"• Время: {get_msk_time().strftime('%H:%M')}\n"
        f"• Внес: {user_name}"
    )
    await send_to_chat(context, chat_message)
    await update.message.reply_text(result, reply_markup=get_main_keyboard())


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для просмотра статистики"""
    if not await check_access(update):
        return

    stats = tracker.get_stats()

    stats_text = (
        "📈 <b>Подробная статистика</b>\n\n"
        f"• Всего сеансов сна: {stats.get('total_sleep_sessions', 0)}\n"
        f"• Завершенных сеансов: {stats.get('completed_sleep_sessions', 0)}\n"
        f"• Средняя продолжительность сна: {stats.get('avg_duration', 'нет данных')}\n"
        f"• Всего кормлений: {stats.get('total_feedings', 0)}\n"
        f"• Грудных кормлений: {stats.get('breast_feedings', 0)}\n"
        f"• Искусственных кормлений: {stats.get('bottle_feedings', 0)}\n"
        f"• Всего смеси: {stats.get('total_bottle_all_time', 0)} мл\n"
        f"• Кормлений сегодня: {stats.get('today_feedings', 0)}\n"
        f"• Последнее искусственное кормление: {stats.get('last_bottle_feeding', 'еще не было')}\n"
        f"• Последний вес: {stats.get('last_weight', 'нет данных')}\n"
    )

    if stats.get('weight_trend'):
        stats_text += f"• Динамика веса: {stats.get('weight_trend')}\n"

    stats_text += f"• Активный сон: {'🔴 Да' if stats.get('active_sleep') else '🟢 Нет'}\n\n"
    stats_text += "📊 Данные сохраняются в Google Таблице"

    await update.message.reply_text(stats_text, reply_markup=get_main_keyboard(), parse_mode='HTML')


async def next_feeding_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать когда следующее кормление"""
    if not await check_access(update):
        return

    last_bottle_time = tracker.get_last_bottle_feeding_time()

    if last_bottle_time:
        next_feeding_time = last_bottle_time + timedelta(hours=3)
        reminder_time = last_bottle_time + timedelta(hours=2, minutes=30)

        time_until_reminder = reminder_time - get_msk_time()
        time_until_next_feeding = next_feeding_time - get_msk_time()

        if time_until_next_feeding.total_seconds() > 0:
            reminder_hours = int(time_until_reminder.total_seconds() // 3600)
            reminder_minutes = int((time_until_reminder.total_seconds() % 3600) // 60)

            feeding_hours = int(time_until_next_feeding.total_seconds() // 3600)
            feeding_minutes = int((time_until_next_feeding.total_seconds() % 3600) // 60)

            message = (
                "⏰ <b>Расписание кормлений:</b>\n\n"
                f"• Последнее искусственное кормление: {last_bottle_time.strftime('%H:%M')}\n"
                f"• Следующее кормление: {next_feeding_time.strftime('%H:%M')}\n"
                f"• Напоминание: {reminder_time.strftime('%H:%M')}\n\n"
                f"• До напоминания: {reminder_hours}ч {reminder_minutes}м\n"
                f"• До кормления: {feeding_hours}ч {feeding_minutes}м\n\n"
                "Напоминание придет автоматически за 30 минут до кормления!"
            )
        else:
            message = (
                "⏰ <b>Время кормить!</b>\n\n"
                f"Последнее искусственное кормление было в {last_bottle_time.strftime('%H:%M')}.\n"
                "Уже прошло больше 3 часов! 🍼"
            )
    else:
        message = "Искусственных кормлений еще не было. Напоминания появятся после первого кормления."

    await update.message.reply_text(message, reply_markup=get_main_keyboard(), parse_mode='HTML')


async def show_weight_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать историю веса"""
    if not await check_access(update):
        return

    weight_history = tracker.get_weight_history(limit=10)

    if not weight_history:
        await update.message.reply_text(
            "История веса пока пуста. Добавьте первую запись с помощью кнопки '⚖️ Вес ребенка'.",
            reply_markup=get_main_keyboard()
        )
        return

    history_text = "📈 <b>История веса ребенка:</b>\n\n"

    for i, record in enumerate(weight_history, 1):
        weight_grams = record.get("Вес (г)", "?")
        timestamp = record.get("Временная метка", "")
        note = record.get("Примечание", "")

        try:
            weight_kg = float(weight_grams) / 1000
            dt = datetime.fromisoformat(timestamp).replace(tzinfo=MSK_TIMEZONE)
            date = dt.strftime('%d.%m.%Y %H:%M')
        except:
            date = "неизвестная дата"
            weight_kg = 0

        history_text += f"{i}. {weight_grams}г ({weight_kg:.3f}кг) - {date}"
        if note:
            history_text += f" ({note})"
        history_text += "\n"

    if len(weight_history) >= 2:
        current_weight = float(weight_history[0].get("Вес (г)", 0))
        previous_weight = float(weight_history[1].get("Вес (г)", 0))
        difference = current_weight - previous_weight

        history_text += f"\n📊 <b>Динамика:</b> "
        if difference > 0:
            history_text += f"+{difference}г"
        elif difference < 0:
            history_text += f"{difference}г"
        else:
            history_text += "без изменений"

    await update.message.reply_text(history_text, reply_markup=get_main_keyboard(), parse_mode='HTML')


def setup_command_handlers(application):
    """Регистрация обработчиков команд"""
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("start_sleep", start_sleep_cmd))
    application.add_handler(CommandHandler("end_sleep", end_sleep_cmd))
    application.add_handler(CommandHandler("breast_feeding", breastfeeding_cmd))
    application.add_handler(CommandHandler("stats", stats_cmd))
    application.add_handler(CommandHandler("next_feeding", next_feeding_cmd))
    application.add_handler(CommandHandler("weight_history", show_weight_history))