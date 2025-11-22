import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import BOT_TOKEN
from models.baby import Baby
from models.event import Event
from models.user import UserState
from services.reminder_service import ReminderService
from services.notification_service import NotificationService

from handlers.base import BaseHandler
from handlers.feeding import FeedingHandler
from handlers.sleep import SleepHandler
from handlers.weight import WeightHandler
from handlers.diaper import DiaperHandler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize all database tables"""
    Baby.create_table()
    Event.create_table()
    UserState.create_table()
    logger.info("Database tables initialized")


async def send_group_message(context, message):
    """Send message to group chat"""
    from config import GROUP_CHAT_ID
    if GROUP_CHAT_ID:
        try:
            await context.bot.send_message(GROUP_CHAT_ID, message)
        except Exception as e:
            logger.error(f"Failed to send group message: {e}")


async def check_reminders(context):
    """Check and send reminders"""
    from services.reminder_service import ReminderService
    await ReminderService.check_reminders(context)


def setup_handlers(application):
    """Setup all bot handlers"""

    # Command handlers
    application.add_handler(CommandHandler("start", BaseHandler.start))

    # Callback query handlers - ОБНОВЛЕННЫЙ ОБРАБОТЧИК
    application.add_handler(CallbackQueryHandler(
        BaseHandler.handle_main_menu_callback,
        pattern="^main_menu$"
    ))

    # Feeding handlers
    application.add_handler(CallbackQueryHandler(
        lambda update, context: FeedingHandler.handle_feeding(update, context, "breast_feeding"),
        pattern="^breast_feeding$"
    ))
    application.add_handler(CallbackQueryHandler(
        lambda update, context: FeedingHandler.handle_feeding(update, context, "bottle_feeding"),
        pattern="^bottle_feeding$"
    ))
    application.add_handler(CallbackQueryHandler(
        lambda update, context: FeedingHandler.handle_feeding(update, context, "next_feeding"),
        pattern="^next_feeding$"
    ))
    application.add_handler(CallbackQueryHandler(
        lambda update, context: FeedingHandler.handle_bottle_volume(update, context,
                                                                    update.callback_query.data.replace("volume_", "")),
        pattern="^volume_"
    ))
    application.add_handler(CallbackQueryHandler(
        lambda update, context: FeedingHandler.handle_bottle_time(update, context, update.callback_query.data.replace(
            "time_bottle_feeding_", "")),
        pattern="^time_bottle_feeding_"
    ))
    application.add_handler(CallbackQueryHandler(
        lambda update, context: FeedingHandler.handle_breast_time(update, context, "start",
                                                                  update.callback_query.data.replace(
                                                                      "time_breast_start_", "")),
        pattern="^time_breast_start_"
    ))
    application.add_handler(CallbackQueryHandler(
        lambda update, context: FeedingHandler.handle_breast_time(update, context, "end",
                                                                  update.callback_query.data.replace("time_breast_end_",
                                                                                                     "")),
        pattern="^time_breast_end_"
    ))
    application.add_handler(CallbackQueryHandler(
        lambda update, context: FeedingHandler.handle_breast_side(update, context,
                                                                  update.callback_query.data.replace("breast_", "")),
        pattern="^breast_"
    ))

    # Sleep handlers
    application.add_handler(CallbackQueryHandler(
        lambda update, context: SleepHandler.handle_sleep(update, context),
        pattern="^sleep$"
    ))
    application.add_handler(CallbackQueryHandler(
        lambda update, context: SleepHandler.handle_sleep_time(update, context, "start",
                                                               update.callback_query.data.replace("time_sleep_start_",
                                                                                                  "")),
        pattern="^time_sleep_start_"
    ))
    application.add_handler(CallbackQueryHandler(
        lambda update, context: SleepHandler.handle_sleep_time(update, context, "end",
                                                               update.callback_query.data.replace("time_sleep_end_",
                                                                                                  "")),
        pattern="^time_sleep_end_"
    ))

    # Weight handler
    application.add_handler(CallbackQueryHandler(
        lambda update, context: WeightHandler.handle_weight(update, context),
        pattern="^weight$"
    ))

    # Diaper handlers
    application.add_handler(CallbackQueryHandler(
        lambda update, context: DiaperHandler.handle_diaper(update, context),
        pattern="^diaper$"
    ))
    application.add_handler(CallbackQueryHandler(
        lambda update, context: DiaperHandler.handle_diaper_type(update, context,
                                                                 update.callback_query.data.replace("diaper_", "")),
        pattern="^diaper_"
    ))

    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, BaseHandler.handle_message))


def main():
    # Initialize database
    logger.info("Initializing database...")
    init_database()

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Setup handlers
    setup_handlers(application)

    # Setup scheduler for reminders
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        check_reminders,
        trigger=IntervalTrigger(minutes=5),
        args=[Application.builder().token(BOT_TOKEN).build()],
        id='reminder_check',
        replace_existing=True
    )
    scheduler.start()

    # Start the bot
    logger.info("Bot starting...")
    application.run_polling()

    # Shutdown scheduler when bot stops
    scheduler.shutdown()


if __name__ == '__main__':
    main()