from datetime import datetime, timedelta
import pytz
from config import TIMEZONE
from services.database import db


class StatsService:
    @staticmethod
    def get_stats(baby_id, period_hours=None):
        """Получить статистику за указанный период"""
        from models.baby import Baby
        from models.event import Event

        baby = Baby.get_by_id(baby_id)
        if not baby:
            return None

        # Определяем временной диапазон
        if period_hours:
            start_time = datetime.now(pytz.timezone(TIMEZONE)) - timedelta(hours=period_hours)
        else:
            # По умолчанию - сегодня с 00:00
            today = datetime.now(pytz.timezone(TIMEZONE)).date()
            start_time = pytz.timezone(TIMEZONE).localize(datetime.combine(today, datetime.min.time()))

        # Получаем события за период
        query = """
        SELECT * FROM events 
        WHERE baby_id = %s AND timestamp >= %s 
        ORDER BY timestamp DESC
        """
        events = db.fetch_all(query, (baby_id, start_time))

        # Анализируем события
        stats = {
            'baby': baby,
            'period_start': start_time,
            'total_bottle_ml': 0,
            'bottle_feedings': 0,
            'sleep_sessions': 0,
            'total_sleep_minutes': 0,
            'last_sleep_end': None,
            'last_bottle_feeding': None,
            'breast_feeding_sessions': 0,
            'total_breast_feeding_minutes': 0,
            'diaper_changes': 0,
            'weight_entries': []
        }

        # Обрабатываем события
        sleep_sessions = []
        breast_sessions = []
        current_sleep_start = None
        current_breast_start = None

        for event in events:
            event_type = event['event_type']
            timestamp = event['timestamp']

            if event_type == Event.BOTTLE_FEEDING:
                stats['bottle_feedings'] += 1
                stats['total_bottle_ml'] += event['amount'] or 0
                if not stats['last_bottle_feeding']:
                    stats['last_bottle_feeding'] = event

            elif event_type == Event.SLEEP_START:
                current_sleep_start = event

            elif event_type == Event.SLEEP_END:
                if current_sleep_start:
                    stats['sleep_sessions'] += 1
                    sleep_duration = event['duration'] or 0
                    stats['total_sleep_minutes'] += sleep_duration
                    sleep_sessions.append({
                        'start': current_sleep_start['timestamp'],
                        'end': event['timestamp'],
                        'duration': sleep_duration
                    })
                    if not stats['last_sleep_end']:
                        stats['last_sleep_end'] = event
                    current_sleep_start = None

            elif event_type == Event.BREAST_FEEDING_START:
                current_breast_start = event

            elif event_type == Event.BREAST_FEEDING_END:
                if current_breast_start:
                    stats['breast_feeding_sessions'] += 1
                    breast_duration = event['duration'] or 0
                    stats['total_breast_feeding_minutes'] += breast_duration
                    breast_sessions.append({
                        'start': current_breast_start['timestamp'],
                        'end': event['timestamp'],
                        'duration': breast_duration,
                        'breast_side': event['notes']
                    })
                    current_breast_start = None

            elif event_type == Event.DIAPER:
                stats['diaper_changes'] += 1

            elif event_type == Event.WEIGHT:
                stats['weight_entries'].append(event)

        # Если есть активный сон, добавляем его как незавершенный
        if current_sleep_start:
            active_sleep_duration = int(
                (datetime.now(pytz.timezone(TIMEZONE)) - current_sleep_start['timestamp']).total_seconds() / 60)
            stats['sleep_sessions'] += 1
            stats['total_sleep_minutes'] += active_sleep_duration
            stats['active_sleep'] = current_sleep_start

        # Если есть активное грудное кормление, добавляем его как незавершенное
        if current_breast_start:
            active_breast_duration = int(
                (datetime.now(pytz.timezone(TIMEZONE)) - current_breast_start['timestamp']).total_seconds() / 60)
            stats['breast_feeding_sessions'] += 1
            stats['total_breast_feeding_minutes'] += active_breast_duration
            stats['active_breast_feeding'] = current_breast_start

        # Сортируем сессии по времени окончания
        sleep_sessions.sort(key=lambda x: x['end'], reverse=True)
        breast_sessions.sort(key=lambda x: x['end'], reverse=True)

        stats['sleep_sessions_list'] = sleep_sessions
        stats['breast_sessions_list'] = breast_sessions

        return stats

    @staticmethod
    def format_stats(stats):
        """Форматировать статистику в читаемый текст"""
        from services.event_service import EventService
        from models.event import Event

        if not stats:
            return "❌ Не удалось получить статистику"

        baby = stats['baby']
        text = f"📊 Статистика для {baby['name']}\n\n"

        # Период
        period_start = stats['period_start']
        now = datetime.now(pytz.timezone(TIMEZONE))
        if (now - period_start).days > 0:
            period_text = f"с {period_start.strftime('%d.%m.%Y %H:%M')}"
        else:
            period_text = f"за последние {int((now - period_start).total_seconds() / 3600)} часов"

        text += f"📅 Период: {period_text}\n\n"

        # Кормление из бутылочки
        text += "🍼 Кормление из бутылочки:\n"
        if stats['bottle_feedings'] > 0:
            text += f"  • Количество: {stats['bottle_feedings']}\n"
            text += f"  • Общий объем: {stats['total_bottle_ml']} мл\n"
            if stats['bottle_feedings'] > 0:
                text += f"  • Средний объем: {stats['total_bottle_ml'] // stats['bottle_feedings']} мл\n"

            last_bottle = stats['last_bottle_feeding']
            if last_bottle:
                last_time = last_bottle['timestamp'].astimezone(pytz.timezone(TIMEZONE)).strftime('%H:%M')
                text += f"  • Последнее: {last_time} ({last_bottle['amount']} мл)\n"

            # Следующее кормление
            next_time = EventService.get_next_feeding_time(baby['id'])
            if next_time:
                time_left = next_time - datetime.now(pytz.timezone(TIMEZONE))
                if time_left.total_seconds() > 0:
                    hours = int(time_left.total_seconds() // 3600)
                    minutes = int((time_left.total_seconds() % 3600) // 60)
                    if hours > 0:
                        text += f"  • Следующее через: {hours}ч {minutes}м\n"
                    else:
                        text += f"  • Следующее через: {minutes}м\n"
                else:
                    text += f"  • Следующее: пора кормить!\n"
        else:
            text += "  • Не было кормлений\n"

        text += "\n"

        # Сон
        text += "😴 Сон:\n"
        if stats['sleep_sessions'] > 0:
            total_hours = stats['total_sleep_minutes'] // 60
            total_minutes = stats['total_sleep_minutes'] % 60

            text += f"  • Количество снов: {stats['sleep_sessions']}\n"
            text += f"  • Общее время: {total_hours}ч {total_minutes}м\n"
            if stats['sleep_sessions'] > 0:
                text += f"  • Средняя продолжительность: {stats['total_sleep_minutes'] // stats['sleep_sessions']}м\n"

            if stats['last_sleep_end']:
                last_sleep_time = stats['last_sleep_end']['timestamp'].astimezone(pytz.timezone(TIMEZONE)).strftime(
                    '%H:%M')
                last_duration = stats['last_sleep_end']['duration'] or 0
                last_hours = last_duration // 60
                last_minutes = last_duration % 60
                duration_text = f"{last_hours}ч {last_minutes}м" if last_hours > 0 else f"{last_minutes}м"
                text += f"  • Последний сон: {last_sleep_time} ({duration_text})\n"

            if stats.get('active_sleep'):
                active_start = stats['active_sleep']['timestamp'].astimezone(pytz.timezone(TIMEZONE)).strftime('%H:%M')
                active_duration = int(
                    (datetime.now(pytz.timezone(TIMEZONE)) - stats['active_sleep']['timestamp']).total_seconds() / 60)
                active_hours = active_duration // 60
                active_minutes = active_duration % 60
                active_duration_text = f"{active_hours}ч {active_minutes}м" if active_hours > 0 else f"{active_minutes}м"
                text += f"  • Спит сейчас: с {active_start} ({active_duration_text})\n"
        else:
            text += "  • Не было сна\n"

        text += "\n"

        # Грудное кормление
        text += "🤱 Грудное кормление:\n"
        if stats['breast_feeding_sessions'] > 0:
            breast_hours = stats['total_breast_feeding_minutes'] // 60
            breast_minutes = stats['total_breast_feeding_minutes'] % 60

            text += f"  • Количество: {stats['breast_feeding_sessions']}\n"
            text += f"  • Общее время: {breast_hours}ч {breast_minutes}м\n"
            if stats['breast_feeding_sessions'] > 0:
                text += f"  • Средняя продолжительность: {stats['total_breast_feeding_minutes'] // stats['breast_feeding_sessions']}м\n"

            # Анализ по грудям
            left_breast_count = sum(
                1 for session in stats['breast_sessions_list'] if session.get('breast_side') == 'left')
            right_breast_count = sum(
                1 for session in stats['breast_sessions_list'] if session.get('breast_side') == 'right')

            if left_breast_count > 0 or right_breast_count > 0:
                text += f"  • Левая грудь: {left_breast_count} раз\n"
                text += f"  • Правая грудь: {right_breast_count} раз\n"

            if stats.get('active_breast_feeding'):
                active_start = stats['active_breast_feeding']['timestamp'].astimezone(pytz.timezone(TIMEZONE)).strftime(
                    '%H:%M')
                active_duration = int((datetime.now(pytz.timezone(TIMEZONE)) - stats['active_breast_feeding'][
                    'timestamp']).total_seconds() / 60)
                text += f"  • Кормит сейчас: с {active_start} ({active_duration}м)\n"
        else:
            text += "  • Не было кормлений\n"

        text += "\n"

        # Подгузники
        text += f"💩 Подгузники: {stats['diaper_changes']} смен\n"

        # Вес
        if stats['weight_entries']:
            latest_weight = max(stats['weight_entries'], key=lambda x: x['timestamp'])
            text += f"⚖️ Последний вес: {latest_weight['amount']}г\n"

        return text