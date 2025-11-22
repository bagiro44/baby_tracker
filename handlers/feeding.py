from telegram import Update
from telegram.ext import ContextTypes
from models.baby import Baby
from models.event import Event
from models.user import UserState
from services.event_service import EventService
from services.notification_service import NotificationService
from utils.keyboards import *
from utils.time_utils import get_time_with_offset
import logging

logger = logging.getLogger(__name__)


class FeedingHandler:
    @staticmethod
    async def handle_feeding(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        baby = Baby.get_current()

        if not baby:
            await query.edit_message_text("❌ Сначала добавьте ребенка")
            return

        if action == "breast_feeding":
            active_feeding = Event.get_active_breast_feeding(baby['id'])
            if active_feeding:
                # Show end feeding with time selection
                await query.edit_message_text(
                    "Завершить грудное кормление:",
                    reply_markup=time_selection_keyboard("breast_end")
                )
            else:
                # Show start feeding with time selection
                await query.edit_message_text(
                    "Начать грудное кормление:",
                    reply_markup=time_selection_keyboard("breast_start")
                )

        elif action == "bottle_feeding":
            await query.edit_message_text(
                "Выберите объем смеси:",
                reply_markup=bottle_volume_keyboard()
            )

        elif action == "next_feeding":
            next_time = EventService.get_next_feeding_time(baby['id'])
            if next_time:
                message = NotificationService.format_next_feeding(baby, next_time)
            else:
                message = "❌ Не найдено предыдущих кормлений"
            await query.edit_message_text(message, reply_markup=back_to_main_keyboard())

    @staticmethod
    async def handle_bottle_volume(update: Update, context: ContextTypes.DEFAULT_TYPE, volume_str: str):
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        baby = Baby.get_current()

        if volume_str == "custom":
            UserState.set_state(user_id, "awaiting_bottle_volume", {
                "baby_id": baby['id']
            })
            await query.edit_message_text("Введите объем смеси в мл:")
            return

        try:
            volume = int(volume_str)
            await query.edit_message_text(
                "Когда было кормление?",
                reply_markup=time_selection_keyboard("bottle_feeding")
            )
            # Store volume in context for time selection
            context.user_data['bottle_volume'] = volume
        except ValueError:
            await query.edit_message_text("❌ Ошибка выбора объема")

    @staticmethod
    async def handle_bottle_time(update: Update, context: ContextTypes.DEFAULT_TYPE, minutes_str: str):
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        baby = Baby.get_current()
        volume = context.user_data.get('bottle_volume')

        if not volume:
            await query.edit_message_text("❌ Ошибка: объем не выбран")
            return

        if minutes_str == "custom":
            UserState.set_state(user_id, "awaiting_custom_time", {
                "action_type": "bottle_feeding",
                "baby_id": baby['id']
            })
            await query.edit_message_text("Введите время в формате ЧЧММ (например, 1430):")
            return

        minutes = int(minutes_str)
        timestamp = get_time_with_offset(minutes) if minutes > 0 else None

        await EventService.add_bottle_feeding(context, baby['id'], user_id, volume, timestamp)
        await query.edit_message_text(f"✅ Кормление {volume}мл записано!", reply_markup=back_to_main_keyboard())

    @staticmethod
    async def handle_breast_time(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, minutes_str: str):
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        baby = Baby.get_current()

        if minutes_str == "custom":
            UserState.set_state(user_id, "awaiting_custom_time", {
                "action_type": f"breast_{action}",
                "baby_id": baby['id']
            })
            await query.edit_message_text("Введите время в формате ЧЧММ (например, 1430):")
            return

        minutes = int(minutes_str)
        timestamp = get_time_with_offset(minutes) if minutes > 0 else None

        if action == "start":
            await EventService.start_breast_feeding(context, baby['id'], user_id, timestamp)
            await query.edit_message_text("✅ Начало кормления записано!", reply_markup=back_to_main_keyboard())
        elif action == "end":
            # For breast end, we need to ask for breast side
            UserState.set_state(user_id, "awaiting_breast_side", {
                "baby_id": baby['id'],
                "timestamp": timestamp
            })
            await query.edit_message_text("Выберите грудь:", reply_markup=breast_side_keyboard())

    @staticmethod
    async def handle_breast_side(update: Update, context: ContextTypes.DEFAULT_TYPE, breast_side: str):
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        baby = Baby.get_current()
        user_state = UserState.get_state(user_id)
        state_data = user_state.get('data', {})
        timestamp = state_data.get('timestamp')

        result = await EventService.end_breast_feeding(context, baby['id'], user_id, breast_side, timestamp)
        UserState.clear_state(user_id)

        if result:
            await query.edit_message_text("✅ Конец кормления записан!", reply_markup=back_to_main_keyboard())
        else:
            await query.edit_message_text("❌ Не найдено активное начало кормления",
                                          reply_markup=back_to_main_keyboard())