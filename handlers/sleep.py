from telegram import Update
from telegram.ext import ContextTypes
from models.baby import Baby
from models.event import Event
from models.user import UserState
from services.event_service import EventService
from utils.keyboards import *
from utils.time_utils import get_time_with_offset
import logging

logger = logging.getLogger(__name__)


class SleepHandler:
    @staticmethod
    async def handle_sleep(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        baby = Baby.get_current()
        if not baby:
            await query.edit_message_text("❌ Сначала добавьте ребенка")
            return

        active_sleep = Event.get_active_sleep(baby['id'])

        if active_sleep:
            await query.edit_message_text(
                "Завершить сон:",
                reply_markup=time_selection_keyboard("sleep_end")
            )
        else:
            await query.edit_message_text(
                "Начать сон:",
                reply_markup=time_selection_keyboard("sleep_start")
            )

    @staticmethod
    async def handle_sleep_time(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, minutes_str: str):
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        baby = Baby.get_current()

        if minutes_str == "custom":
            UserState.set_state(user_id, "awaiting_custom_time", {
                "action_type": f"sleep_{action}",
                "baby_id": baby['id']
            })
            await query.edit_message_text("Введите время в формате ЧЧММ (например, 1430):")
            return

        minutes = int(minutes_str)
        timestamp = get_time_with_offset(minutes) if minutes > 0 else None

        if action == "start":
            await EventService.start_sleep(context, baby['id'], user_id, timestamp)
            await query.edit_message_text("✅ Начало сна записано!", reply_markup=back_to_main_keyboard())
        elif action == "end":
            result = await EventService.end_sleep(context, baby['id'], user_id, timestamp)
            if result:
                await query.edit_message_text("✅ Конец сна записан!", reply_markup=back_to_main_keyboard())
            else:
                await query.edit_message_text("❌ Не найдено активное начало сна", reply_markup=back_to_main_keyboard())