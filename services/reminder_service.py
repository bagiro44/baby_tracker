from services.database import db
from services.notification_service import NotificationService
from datetime import datetime, timedelta
import pytz
from config import TIMEZONE, FEEDING_INTERVAL_HOURS, REMINDER_MINUTES_BEFORE
import logging

logger = logging.getLogger(__name__)


class ReminderService:
    @staticmethod
    def schedule_feeding_reminder(baby_id, feeding_time=None):
        from models.event import Event
        from models.reminder import Reminder

        if feeding_time is None:
            last_feeding = Event.get_last_by_type(baby_id, Event.BOTTLE_FEEDING)
            if not last_feeding:
                logger.info(f"No previous feeding found for baby {baby_id}")
                return None
            feeding_time = last_feeding['timestamp']

        reminder_time = feeding_time + timedelta(hours=FEEDING_INTERVAL_HOURS) - timedelta(
            minutes=REMINDER_MINUTES_BEFORE)
        reminder_now_time = feeding_time + timedelta(hours=FEEDING_INTERVAL_HOURS)

        ReminderService.cancel_pending_reminders(baby_id, 'feeding')
        ReminderService.cancel_pending_reminders(baby_id, 'feeding_now')

        reminder_id = Reminder.add(baby_id, 'feeding', reminder_time)
        logger.info(f"Scheduled feeding reminder for baby {baby_id} at {reminder_time}")

        Reminder.add(baby_id, 'feeding_now', reminder_now_time)
        logger.info(f"Scheduled feeding now reminder for baby {baby_id} at {reminder_now_time}")
        return reminder_id

    @staticmethod
    def cancel_pending_reminders(baby_id, reminder_type=None):
        from models.reminder import Reminder

        if reminder_type:
            query = "DELETE FROM reminders WHERE baby_id = %s AND reminder_type = %s AND sent = FALSE"
            db.execute_query(query, (baby_id, reminder_type))
        else:
            query = "DELETE FROM reminders WHERE baby_id = %s AND sent = FALSE"
            db.execute_query(query, (baby_id,))

    @staticmethod
    async def check_and_send_reminders(context):
        from models.reminder import Reminder
        from models.baby import Baby

        try:
            pending_reminders = Reminder.get_pending_reminders()
            logger.info(f"Found {len(pending_reminders)} pending reminders")

            for reminder in pending_reminders:
                baby = Baby.get_by_id(reminder['baby_id'])
                if not baby:
                    logger.warning(f"Baby {reminder['baby_id']} not found for reminder {reminder['id']}")
                    continue

                if reminder['reminder_type'] == 'feeding':
                    await ReminderService.send_feeding_reminder(context, baby, reminder)
                if reminder['reminder_type'] == 'feeding_now':
                    await ReminderService.send_feeding_now_reminder(context, baby, reminder)

                Reminder.mark_as_sent(reminder['id'])
                logger.info(f"Sent and marked reminder {reminder['id']} as sent")

            # Clean up old reminders once a day (check if it's a new hour)
            now = datetime.now(pytz.timezone(TIMEZONE))
            if now.minute == 0:
                deleted_count = Reminder.delete_old_reminders(7)
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old reminders")

        except Exception as e:
            logger.error(f"Error in check_and_send_reminders: {e}")

    @staticmethod
    async def send_feeding_reminder(context, baby, reminder):
        message = f"⏰ Напоминание: через {REMINDER_MINUTES_BEFORE} минут кормление {baby['name']}!"

        logger.info(f"Sending feeding reminder for {baby['name']}")

        await NotificationService.notify_group(
            context,
            message
        )

    @staticmethod
    async def send_feeding_now_reminder(context, baby, reminder):
        message = f"⏰⏰⏰ Пора кормить смесью! ⏰⏰⏰"

        logger.info(f"Sending feeding now reminder for {baby['name']}")

        await NotificationService.notify_group(
            context,
            message
        )