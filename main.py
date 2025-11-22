import logging
from telegram.ext import Application
from leo_bot.config import BOT_TOKEN, logger
from leo_bot.handlers.base import setup_handlers
from leo_bot.handlers.conversations import setup_conversation_handlers
from leo_bot.handlers.commands import setup_command_handlers


async def setup_application():
    """Настройка и запуск приложения"""
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    setup_command_handlers(application)
    setup_conversation_handlers(application)
    setup_handlers(application)

    return application


def main():
    """Основная функция запуска бота"""
    try:
        logger.info("Запуск бота...")

        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()

        # Регистрируем обработчики
        setup_command_handlers(application)
        setup_conversation_handlers(application)
        setup_handlers(application)

        logger.info("Бот запущен в режиме polling")
        application.run_polling()

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise


if __name__ == "__main__":
    main()