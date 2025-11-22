from models.event import Event
from models.baby import Baby
from services.notification_service import NotificationService
from datetime import datetime, timedelta
import pytz
from config import TIMEZONE, FEEDING_INTERVAL_HOURS


class EventService:
    @staticmethod
    async def start_sleep(context, baby_id, user_id, timestamp=None):
        event_id = Event.add(baby_id, Event.SLEEP_START, user_id, timestamp=timestamp)
        baby = Baby.get_by_id(baby_id)
        await NotificationService.notify_group(
            context,
            f"😴 {baby['name']} начал(а) спать",
            timestamp
        )
        return event_id

    @staticmethod
    async def end_sleep(context, baby_id, user_id, timestamp=None):
        sleep_start = Event.get_active_sleep(baby_id)
        if not sleep_start:
            return None

        start_time = sleep_start['timestamp']
        end_time = timestamp or datetime.now(pytz.timezone(TIMEZONE))
        duration = int((end_time - start_time).total_seconds() / 60)  # minutes

        event_id = Event.add(baby_id, Event.SLEEP_END, user_id, duration=duration, timestamp=end_time)
        baby = Baby.get_by_id(baby_id)

        hours = duration // 60
        minutes = duration % 60
        duration_text = f"{hours}ч {minutes}м" if hours > 0 else f"{minutes}м"

        await NotificationService.notify_group(
            context,
            f"😴 {baby['name']} проснулся(ась). Спал(а): {duration_text}",
            end_time
        )
        return event_id, duration

    @staticmethod
    async def start_breast_feeding(context, baby_id, user_id, timestamp=None):
        event_id = Event.add(baby_id, Event.BREAST_FEEDING_START, user_id, timestamp=timestamp)
        baby = Baby.get_by_id(baby_id)
        await NotificationService.notify_group(
            context,
            f"🤱 Начато грудное кормление {baby['name']}",
            timestamp
        )
        return event_id

    @staticmethod
    async def end_breast_feeding(context, baby_id, user_id, breast_side, timestamp=None):
        feeding_start = Event.get_active_breast_feeding(baby_id)
        if not feeding_start:
            return None

        start_time = feeding_start['timestamp']
        end_time = timestamp or datetime.now(pytz.timezone(TIMEZONE))
        duration = int((end_time - start_time).total_seconds() / 60)  # minutes

        breast_text = "левой" if breast_side == "left" else "правой"
        event_id = Event.add(baby_id, Event.BREAST_FEEDING_END, user_id,
                             duration=duration, notes=breast_side, timestamp=end_time)
        baby = Baby.get_by_id(baby_id)

        await NotificationService.notify_group(
            context,
            f"🤱 Завершено грудное кормление {baby['name']} ({breast_text} грудью, {duration}м)",
            end_time
        )
        return event_id, duration

    @staticmethod
    async def add_bottle_feeding(context, baby_id, user_id, amount, timestamp=None):
        event_id = Event.add(baby_id, Event.BOTTLE_FEEDING, user_id, amount=amount, timestamp=timestamp)
        baby = Baby.get_by_id(baby_id)

        await NotificationService.notify_group(
            context,
            f"🍼 {baby['name']} покормлен(а) смесью: {amount}мл",
            timestamp
        )

        # Schedule next feeding reminder
        from services.reminder_service import ReminderService
        ReminderService.schedule_next_feeding(baby_id, timestamp)

        return event_id

    @staticmethod
    async def add_weight(context, baby_id, user_id, weight, timestamp=None):
        event_id = Event.add(baby_id, Event.WEIGHT, user_id, amount=weight, timestamp=timestamp)
        baby = Baby.get_by_id(baby_id)

        await NotificationService.notify_text(
            context,
            f"⚖️ {baby['name']}: {weight}г",
            timestamp
        )
        return event_id

    @staticmethod
    async def add_diaper(context, baby_id, user_id, diaper_type, timestamp=None):
        event_id = Event.add(baby_id, Event.DIAPER, user_id, notes=diaper_type, timestamp=timestamp)
        baby = Baby.get_by_id(baby_id)

        type_emojis = {
            'wet': '💦',
            'dirty': '💩',
            'mixed': '💦💩'
        }

        await NotificationService.notify_group(
            context,
            f"{type_emojis.get(diaper_type, '💩')} Смена подгузника {baby['name']} ({diaper_type})",
            timestamp
        )
        return event_id

    @staticmethod
    def get_next_feeding_time(baby_id):
        last_feeding = Event.get_last_by_type(baby_id, Event.BOTTLE_FEEDING)
        if not last_feeding:
            return None

        next_time = last_feeding['timestamp'] + timedelta(hours=FEEDING_INTERVAL_HOURS)
        return next_time

    # Добавим отдельный метод для отправки текстовых уведомлений
    @staticmethod
    async def notify_text(context, message, timestamp=None):
        """Send text notification to group"""
        await NotificationService.notify_group(context, message, timestamp)