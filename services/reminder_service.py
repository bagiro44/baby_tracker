from models.reminder import Reminder
from models.baby import Baby
from services.notification_service import NotificationService
from services.database import db  # ДОБАВЛЕНО
from datetime import datetime, timedelta
import pytz
from config import TIMEZONE, FEEDING_INTERVAL_HOURS, REMINDER_MINUTES_BEFORE


class ReminderService:
    @staticmethod
    def schedule_feeding_reminder(baby_id, feeding_time=None):
        """Schedule next feeding reminder"""
        if feeding_time is None:
            from models.event import Event
            last_feeding = Event.get_last_by_type(baby_id, Event.BOTTLE_FEEDING)
            if not last_feeding:
                return None
            feeding_time = last_feeding['timestamp']

        reminder_time = feeding_time + timedelta(hours=FEEDING_INTERVAL_HOURS) - timedelta(
            minutes=REMINDER_MINUTES_BEFORE)

        # Remove any existing pending reminders for this baby
        ReminderService.cancel_pending_reminders(baby_id, 'feeding')

        # Add new reminder
        reminder_id = Reminder.add(baby_id, 'feeding', reminder_time)
        return reminder_id

    @staticmethod
    def cancel_pending_reminders(baby_id, reminder_type=None):
        """Cancel pending reminders for a baby"""
        if reminder_type:
            query = "DELETE FROM reminders WHERE baby_id = %s AND reminder_type = %s AND sent = FALSE"
            db.execute_query(query, (baby_id, reminder_type))
        else:
            query = "DELETE FROM reminders WHERE baby_id = %s AND sent = FALSE"
            db.execute_query(query, (baby_id,))

    @staticmethod
    async def check_and_send_reminders(context):
        """Check and send due reminders"""
        try:
            pending_reminders = Reminder.get_pending_reminders()

            for reminder in pending_reminders:
                baby = Baby.get_by_id(reminder['baby_id'])
                if not baby:
                    continue

                if reminder['reminder_type'] == 'feeding':
                    await ReminderService.send_feeding_reminder(context, baby, reminder)

                # Mark reminder as sent
                Reminder.mark_as_sent(reminder['id'])

            # Clean up old reminders once a day (check if it's a new hour)
            now = datetime.now(pytz.timezone(TIMEZONE))
            if now.minute == 0:  # Run cleanup at the start of each hour
                Reminder.delete_old_reminders(7)

        except Exception as e:
            print(f"Error in check_and_send_reminders: {e}")

    @staticmethod
    async def send_feeding_reminder(context, baby, reminder):
        """Send feeding reminder"""
        message = f"⏰ Напоминание: через {REMINDER_MINUTES_BEFORE} минут кормление {baby['name']}!"

        await NotificationService.notify_group(
            context,
            message
        )

        # Also send to all admin users
        from config import ADMIN_USER_IDS
        for user_id in ADMIN_USER_IDS:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message
                )
            except Exception as e:
                print(f"Failed to send reminder to user {user_id}: {e}")