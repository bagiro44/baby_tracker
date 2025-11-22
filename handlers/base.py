from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from leo_bot.config import logger
from leo_bot.utils.telegram_utils import check_access
from leo_bot.keyboards.menus import get_main_keyboard

async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    if not await check_access(update):
        return

    text = update.message.text

    # Импортируем функции напрямую здесь, чтобы избежать циклических импортов
    from leo_bot.handlers.conversations import (
        start_sleep_with_time, end_sleep_with_time,
        start_breast_feeding, start_bottle_feeding, start_weight_input
    )
    from leo_bot.handlers.commands import (
        next_feeding_cmd, show_weight_history, stats_cmd
    )

    if text == "👶 Начать сон":
        return await start_sleep_with_time(update, context)
    elif text == "🛏️ Закончить сон":
        return await end_sleep_with_time(update, context)
    elif text == "🍼 Грудное кормление":
        return await start_breast_feeding(update, context)
    elif text == "🥛 Искусственное кормление":
        return await start_bottle_feeding(update, context)
    elif text == "⚖️ Вес ребенка":
        return await start_weight_input(update, context)
    elif text == "📊 Статистика":
        await stats_cmd(update, context)
    elif text == "⏰ Следующее кормление":
        await next_feeding_cmd(update, context)
    elif text == "📈 История веса":
        await show_weight_history(update, context)
    else:
        await update.message.reply_text(
            "Используйте кнопки ниже для управления ботом",
            reply_markup=get_main_keyboard()
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка при обработке update {update}: {context.error}")

def setup_handlers(application):
    """Регистрация базовых обработчиков"""
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_click))
    application.add_error_handler(error_handler)