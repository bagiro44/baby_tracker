import logging
from telegram.ext import ContextTypes
from leo_bot.config import ADMIN_IDS, logger
from leo_bot.utils.telegram_utils import send_to_chat
from leo_bot.keyboards.menus import get_main_keyboard

# Импортируем tracker из модуля tracker, чтобы избежать циклических импортов
from leo_bot.tracker import tracker

async def schedule_feeding_reminder(context: ContextTypes.DEFAULT_TYPE, user_id: int, amount: int):
    """Запланировать напоминание о кормлении через 2.5 часа"""
    try:
        # 2.5 часа = 150 минут
        reminder_time = 150 * 60  # в секундах

        # Получаем ID последнего кормления для отметки
        feeding_records = tracker.feeding_sheet.get_all_records()
        bottle_feedings = [r for r in feeding_records if r.get("Тип кормления") == "Искусственное"]
        if bottle_feedings:
            last_feeding_id = max(r.get("ID") for r in bottle_feedings)
        else:
            last_feeding_id = None

        # Запланировать задачу
        context.job_queue.run_once(
            send_feeding_reminder,
            reminder_time,
            data={
                'user_id': user_id,
                'amount': amount,
                'feeding_id': last_feeding_id
            },
            name=f"feeding_reminder_{user_id}"
        )

        logger.info(f"Напоминание запланировано для пользователя {user_id} через 2.5 часа")

    except Exception as e:
        logger.error(f"Ошибка при планировании напоминания: {e}")

async def send_feeding_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Отправить напоминание о кормлении"""
    job = context.job
    user_id = job.data['user_id']
    amount = job.data['amount']
    feeding_id = job.data.get('feeding_id')

    try:
        # Отмечаем в таблице, что напоминание отправлено
        if feeding_id:
            tracker.mark_reminder_sent(feeding_id)

        reminder_text = (
            "⏰ <b>Напоминание о кормлении!</b>\n\n"
            f"Прошло 2.5 часа с последнего искусственного кормления ({amount} мл).\n"
            "Следующее кормление через 30 минут (через 3 часа от прошлого кормления). 🍼"
        )

        # Отправляем напоминание всем администраторам
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=reminder_text,
                    reply_markup=get_main_keyboard(),
                    parse_mode='HTML'
                )
                logger.info(f"Напоминание отправлено пользователю {admin_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке напоминания пользователю {admin_id}: {e}")

        # Отправляем напоминание в общий чат
        await send_to_chat(context, reminder_text)

    except Exception as e:
        logger.error(f"Ошибка в send_feeding_reminder: {e}")