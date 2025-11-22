from datetime import datetime, timedelta
from leo_bot.config import MSK_TIMEZONE


def get_msk_time():
    """Получить текущее время в часовом поясе MSK (UTC+3)"""
    return datetime.now(MSK_TIMEZONE)


def parse_custom_time(time_str, time_format="%H%M"):
    """Парсинг кастомного времени с учетом MSK часового пояса"""
    try:
        time_obj = datetime.strptime(time_str, time_format).time()
        now_msk = get_msk_time()
        custom_dt = datetime.combine(now_msk.date(), time_obj).replace(tzinfo=MSK_TIMEZONE)

        if custom_dt > now_msk:
            custom_dt = custom_dt - timedelta(days=1)

        return custom_dt
    except ValueError as e:
        raise ValueError(f"Неверный формат времени {time_str}: {e}")