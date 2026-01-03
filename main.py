import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, Defaults, MessageHandler, filters, JobQueue
import pytz
import sys
from systemd import journal

from config import BOT_TOKEN, TIMEZONE

# Импорты моделей
from models.baby import Baby
from models.event import Event
from models.user import UserState
from models.reminder import Reminder

# Импорты обработчиков
from handlers.base import BaseHandler
from handlers.feeding import FeedingHandler
from handlers.sleep import SleepHandler
from handlers.weight import WeightHandler
from handlers.diaper import DiaperHandler
from handlers.stats import StatsHandler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/home/bagiro44/bot.log'),
        journal.JournalHandler(SYSLOG_IDENTIFIER="logtest")
    ]
)

def init_database():
    """Initialize all database tables"""
    Baby.create_table()
    Event.create_table()
    UserState.create_table()
    Reminder.create_table()
    logger.info("Database tables initialized")


async def check_reminders(context):
    """Check and send reminders"""
    from services.reminder_service import ReminderService
    await ReminderService.check_and_send_reminders(context)


def setup_handlers(application):
    """Setup all bot handlers"""

    # Command handlers
    application.add_handler(CommandHandler("start", BaseHandler.start))

    # Callback query handlers
    application.add_handler(CallbackQueryHandler(
        BaseHandler.handle_main_menu_callback,
        pattern="^main_menu$"
    ))

    # Gender selection handler
    application.add_handler(CallbackQueryHandler(
        lambda update, context: BaseHandler.handle_gender_selection(update, context,
                                                                    update.callback_query.data.replace("gender_", "")),
        pattern="^gender_"
    ))

    # Sleep handlers
    application.add_handler(CallbackQueryHandler(
        lambda update, context: SleepHandler.handle_sleep_start_menu(update, context),
        pattern="^sleep_start_menu$"
    ))
    application.add_handler(CallbackQueryHandler(
        lambda update, context: SleepHandler.handle_sleep_end_menu(update, context),
        pattern="^sleep_end_menu$"
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

    # Breast feeding handlers
    application.add_handler(CallbackQueryHandler(
        lambda update, context: FeedingHandler.handle_breast_start_menu(update, context),
        pattern="^breast_start_menu$"
    ))
    application.add_handler(CallbackQueryHandler(
        lambda update, context: FeedingHandler.handle_breast_end_menu(update, context),
        pattern="^breast_end_menu$"
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

    # Bottle feeding handlers
    application.add_handler(CallbackQueryHandler(
        lambda update, context: FeedingHandler.handle_bottle_feeding(update, context),
        pattern="^bottle_feeding$"
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
        lambda update, context: FeedingHandler.handle_next_feeding(update, context),
        pattern="^next_feeding$"
    ))

    # Stats handlers
    application.add_handler(CallbackQueryHandler(
        lambda update, context: StatsHandler.handle_stats(update, context),
        pattern="^stats$"
    ))
    application.add_handler(CallbackQueryHandler(
        lambda update, context: StatsHandler.handle_stats_period(update, context,
                                                                 update.callback_query.data.replace("stats_", "")),
        pattern="^stats_"
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


def setup_job_queue(application):
    """Setup job queue for reminders"""
    job_queue = application.job_queue

    # Check reminders every minute
    job_queue.run_repeating(
        check_reminders,
        interval=60,  # 60 seconds = 1 minute
        first=10,  # Start after 10 seconds
        name="reminder_check"
    )

    logger.info("Job queue setup completed")


def main():
    # Initialize database
    logger.info("Initializing database...")
    init_database()

    TIMEZONE = 'Europe/Moscow'  # измените на нужную

    defaults = Defaults(tzinfo=pytz.timezone(TIMEZONE))

    # Create application with job queue
    application = Application.builder().token(BOT_TOKEN).defaults(defaults).build()

    # Setup handlers
    setup_handlers(application)

    # Setup job queue for reminders
    setup_job_queue(application)

    # Start the bot
    logger.info("Bot starting...")
    application.run_polling()


if __name__ == '__main__':
    main()