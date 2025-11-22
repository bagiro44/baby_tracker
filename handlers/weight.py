from telegram import Update
from telegram.ext import ContextTypes
from models.baby import Baby
from models.user import UserState
from services.event_service import EventService
from utils.keyboards import main_menu_keyboard
import logging

logger = logging.getLogger(__name__)


class WeightHandler:
    @staticmethod
    async def handle_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        baby = Baby.get_current()

        if not baby:
            await query.edit_message_text("❌ Сначала добавьте ребенка")
            return

        UserState.set_state(user_id, "awaiting_weight")
        await query.edit_message_text("Введите вес ребенка в граммах:")