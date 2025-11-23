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
    async def handle_sleep_start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        baby = Baby.get_current()
        if not baby:
            await query.edit_message_text("❌ Сначала добавьте ребенка")
            return

        active_sleep = Event.get_active_sleep(baby['id'])
        if active_sleep:
            start_time = active_sleep['timestamp'].astimezone(context.bot.defaults.tzinfo).strftime('%H:%M')
            await query.edit_message_text(
                f"❌ Уже есть активный сон, начатый в {start_time}. Завершите его сначала.",
                reply_markup=main_menu_keyboard()
            )
            return

        await query.edit_message_text(
            "Когда начался сон?",
            reply_markup=time_selection_keyboard("sleep_start")
        )

    @staticmethod
    async def handle_sleep_end_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        baby = Baby.get_current()
        if not baby:
            await query.edit_message_text("❌ Сначала добавьте ребенка")
            return

        active_sleep = Event.get_active_sleep(baby['id'])
        if not active_sleep:
            await query.edit_message_text(
                "❌ Нет активного сна для завершения.",
                reply_markup=main_menu_keyboard()
            )
            return

        start_time = active_sleep['timestamp'].astimezone(context.bot.defaults.tzinfo).strftime('%H:%M')
        await query.edit_message_text(
            f"Сон начат в {start_time}. Когда он закончился?",
            reply_markup=time_selection_keyboard("sleep_end")
        )

    @staticmethod
    async def handle_sleep_time(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, minutes_str: str):
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
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
            await EventService.start_sleep(context, baby['id'], user_id, user_name, timestamp)
            await query.edit_message_text(
                "✅ Начало сна записано! Выберите следующее действие:",
                reply_markup=main_menu_keyboard()
            )
        elif action == "end":
            result = await EventService.end_sleep(context, baby['id'], user_id, user_name, timestamp)
            if result:
                event_id, duration = result
                hours = duration // 60
                minutes = duration % 60
                duration_text = f"{hours}ч {minutes}м" if hours > 0 else f"{minutes}м"
                await query.edit_message_text(
                    f"✅ Конец сна записан! Продолжительность: {duration_text}. Выберите следующее действие:",
                    reply_markup=main_menu_keyboard()
                )
            else:
                await query.edit_message_text(
                    "❌ Не найдено активное начало сна. Выберите действие:",
                    reply_markup=main_menu_keyboard()
                )