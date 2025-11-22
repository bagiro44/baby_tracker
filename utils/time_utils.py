from datetime import datetime, timedelta
import pytz
from config import TIMEZONE


def parse_custom_time(time_str):
    """Parse time string in HHMM format"""
    try:
        if len(time_str) == 4 and time_str.isdigit():
            hours = int(time_str[:2])
            minutes = int(time_str[2:])
            now = datetime.now(pytz.timezone(TIMEZONE))
            custom_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)

            # If time is in future, assume it's yesterday
            if custom_time > now:
                custom_time = custom_time - timedelta(days=1)

            return custom_time
    except:
        pass
    return None


def get_time_with_offset(minutes_ago):
    """Get datetime with minutes offset"""
    return datetime.now(pytz.timezone(TIMEZONE)) - timedelta(minutes=minutes_ago)


def format_duration(minutes):
    """Format duration in minutes to human readable"""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}ч {mins}м"
    return f"{mins}м"


def format_time_with_offset(minutes_ago):
    """Format time with offset for display in buttons"""
    target_time = get_time_with_offset(minutes_ago)
    time_str = target_time.strftime('%H:%M')

    if minutes_ago == 0:
        return f"Сейчас ({time_str})"
    else:
        return f"{minutes_ago} мин ({time_str})"