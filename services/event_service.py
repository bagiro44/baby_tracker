from services.notification_service import NotificationService
from datetime import datetime, timedelta
import pytz
from config import TIMEZONE, FEEDING_INTERVAL_HOURS


class EventService:
    @staticmethod
    def get_gender_specific_text(baby, base_text_male, base_text_female, base_text_unknown=None):
        """Возвращает текст с учетом пола ребенка"""
        if base_text_unknown is None:
            base_text_unknown = base_text_male  # По умолчанию используем мужской род

        gender = baby.get('gender', 'unknown')
        if gender == 'male':
            return base_text_male
        elif gender == 'female':
            return base_text_female
        else:
            return base_text_unknown

    @staticmethod
    async def start_sleep(context, baby_id, user_id, user_name, timestamp=None):
        from models.event import Event
        from models.baby import Baby

        event_id = Event.add(baby_id, Event.SLEEP_START, user_id, timestamp=timestamp)
        baby = Baby.get_by_id(baby_id)

        sleep_text = EventService.get_gender_specific_text(
            baby,
            "начал спать",
            "начала спать",
            "начал(а) спать"
        )

        await NotificationService.notify_group(
            context,
            f"😴 {baby['name']} {sleep_text}",
            user_name,
            timestamp
        )
        return event_id

    @staticmethod
    async def end_sleep(context, baby_id, user_id, user_name, timestamp=None):
        from models.event import Event
        from models.baby import Baby

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

        wake_text = EventService.get_gender_specific_text(
            baby,
            "проснулся",
            "проснулась",
            "проснулся(ась)"
        )

        sleep_text = EventService.get_gender_specific_text(
            baby,
            "Спал",
            "Спала",
            "Спал(а)"
        )

        await NotificationService.notify_group(
            context,
            f"😴 {baby['name']} {wake_text}. {sleep_text}: {duration_text}",
            user_name,
            end_time
        )
        return event_id, duration

    @staticmethod
    async def start_breast_feeding(context, baby_id, user_id, user_name, timestamp=None):
        from models.event import Event
        from models.baby import Baby

        event_id = Event.add(baby_id, Event.BREAST_FEEDING_START, user_id, timestamp=timestamp)
        baby = Baby.get_by_id(baby_id)

        feeding_text = EventService.get_gender_specific_text(
            baby,
            "Начато грудное кормление",
            "Начато грудное кормление",  # Текст одинаковый
            "Начато грудное кормление"
        )

        await NotificationService.notify_group(
            context,
            f"🤱 {feeding_text} {baby['name']}",
            user_name,
            timestamp
        )
        return event_id

    @staticmethod
    async def end_breast_feeding(context, baby_id, user_id, user_name, breast_side, timestamp=None):
        from models.event import Event
        from models.baby import Baby

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

        feeding_text = EventService.get_gender_specific_text(
            baby,
            "Завершено грудное кормление",
            "Завершено грудное кормление",  # Текст одинаковый
            "Завершено грудное кормление"
        )

        await NotificationService.notify_group(
            context,
            f"🤱 {feeding_text} {baby['name']} ({breast_text} грудью, {duration}м)",
            user_name,
            end_time
        )
        return event_id, duration

    @staticmethod
    async def add_bottle_feeding(context, baby_id, user_id, user_name, amount, timestamp=None):
        from models.event import Event
        from models.baby import Baby

        event_id = Event.add(baby_id, Event.BOTTLE_FEEDING, user_id, amount=amount, timestamp=timestamp)
        baby = Baby.get_by_id(baby_id)

        feeding_text = EventService.get_gender_specific_text(
            baby,
            "покормлен смесью",
            "покормлена смесью",
            "покормлен(а) смесью"
        )

        await NotificationService.notify_group(
            context,
            f"🍼 {baby['name']} {feeding_text}: {amount}мл",
            user_name,
            timestamp
        )

        # Schedule next feeding reminder - ДОБАВЛЕНО
        from services.reminder_service import ReminderService
        ReminderService.schedule_feeding_reminder(baby_id, timestamp)

        return event_id

    @staticmethod
    async def add_weight(context, baby_id, user_id, user_name, weight, timestamp=None):
        from models.event import Event
        from models.baby import Baby

        event_id = Event.add(baby_id, Event.WEIGHT, user_id, amount=weight, timestamp=timestamp)
        baby = Baby.get_by_id(baby_id)

        await NotificationService.notify_group(
            context,
            f"⚖️ {baby['name']}: {weight}г",
            user_name,
            timestamp
        )
        return event_id

    @staticmethod
    async def add_diaper(context, baby_id, user_id, user_name, diaper_type, timestamp=None):
        from models.event import Event
        from models.baby import Baby

        event_id = Event.add(baby_id, Event.DIAPER, user_id, notes=diaper_type, timestamp=timestamp)
        baby = Baby.get_by_id(baby_id)

        type_emojis = {
            'wet': '💦',
            'dirty': '💩',
            'mixed': '💦💩'
        }

        type_names = {
            'wet': 'мокрый',
            'dirty': 'грязный',
            'mixed': 'смешанный'
        }

        diaper_text = EventService.get_gender_specific_text(
            baby,
            "Смена подгузника",
            "Смена подгузника",  # Текст одинаковый
            "Смена подгузника"
        )

        await NotificationService.notify_group(
            context,
            f"{type_emojis.get(diaper_type, '💩')} {diaper_text} {baby['name']} ({type_names.get(diaper_type, diaper_type)})",
            user_name,
            timestamp
        )
        return event_id

    @staticmethod
    def get_next_feeding_time(baby_id):
        from models.event import Event
        from services.notification_service import NotificationService

        last_feeding = Event.get_last_by_type(baby_id, Event.BOTTLE_FEEDING)
        if not last_feeding:
            return None

        next_time = last_feeding['timestamp'] + timedelta(hours=FEEDING_INTERVAL_HOURS)
        return next_time