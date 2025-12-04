from config import GROUP_CHAT_ID
from datetime import datetime
import pytz
from config import TIMEZONE
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    async def notify_group(context, message, user_name=None, timestamp=None):
        """Send notification to group chat"""
        if not GROUP_CHAT_ID:
            logger.warning("GROUP_CHAT_ID not configured")
            return

        try:
            # Добавляем информацию о пользователе
            if user_name:
                message = f"{message} \n👤 {user_name}"

            if timestamp:
                time_str = timestamp.astimezone(pytz.timezone(TIMEZONE)).strftime('%H:%M')
                message = f"{message} в {time_str}"

            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=message
            )
            logger.info(f"Message sent to group: {message}")
        except Exception as e:
            logger.error(f"Failed to send message to group: {e}")

    @staticmethod
    def format_next_feeding(baby, next_time):
        from datetime import datetime

        now = datetime.now(pytz.timezone(TIMEZONE))
        time_left = next_time - now

        if time_left.total_seconds() <= 0:
            return f"🍼 {baby['name']} - пора кормить!"

        hours = int(time_left.total_seconds() // 3600)
        minutes = int((time_left.total_seconds() % 3600) // 60)

        if hours > 0:
            return f"🍼 {baby['name']} - следующее кормление через {hours}ч {minutes}м"
        else:
            return f"🍼 {baby['name']} - следующее кормление через {minutes}м"