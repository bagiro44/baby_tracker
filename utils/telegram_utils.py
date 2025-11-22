from telegram import Update
from telegram.ext import ContextTypes
from leo_bot.config import CHAT_ID, ADMIN_IDS, logger

async def send_to_chat(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Отправить сообщение в общий чат"""
    if CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text=message,
                parse_mode='HTML'
            )
            logger.info(f"Сообщение отправлено в общий чат: {message}")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в общий чат: {e}")
    else:
        logger.info("CHAT_ID не указан, сообщение не отправлено в общий чат")

async def get_user_display_name(update: Update):
    """Получить отображаемое имя пользователя"""
    user = update.effective_user
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    else:
        return "Пользователь"

async def check_access(update: Update):
    """Проверить доступ пользователя"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Доступ запрещен!")
        return False
    return True