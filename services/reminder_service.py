from models.event import Event
from services.notification_service import NotificationService
from datetime import datetime, timedelta
import pytz
from config import TIMEZONE, FEEDING_INTERVAL_HOURS, REMINDER_MINUTES_BEFORE


class ReminderService:
    @staticmethod
    async def check_reminders(context):
        """Check and send due reminders"""
        from models.baby import Baby
        babies = Baby.get_all()

        for baby in babies:
            next_feeding_reminder = ReminderService.schedule_next_feeding(baby['id'])
            if next_feeding_reminder and datetime.now(pytz.timezone(TIMEZONE)) >= next_feeding_reminder:
                await NotificationService.notify_group(
                    context,
                    f"⏰ Напоминание: через {REMINDER_MINUTES_BEFORE} минут кормление {baby['name']}!"
                )

    @staticmethod
    def schedule_next_feeding(baby_id, last_feeding_time=None):
        if last_feeding_time is None:
            last_feeding = Event.get_last_by_type(baby_id, Event.BOTTLE_FEEDING)
            if not last_feeding:
                return None
            last_feeding_time = last_feeding['timestamp']

        reminder_time = last_feeding_time + timedelta(hours=FEEDING_INTERVAL_HOURS) - timedelta(
            minutes=REMINDER_MINUTES_BEFORE)
        return reminder_time