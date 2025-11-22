from telegram import Update
from telegram.ext import ContextTypes
from models.baby import Baby
from services.event_service import EventService
from utils.keyboards import diaper_type_keyboard, main_menu_keyboard
import logging

logger = logging.getLogger(__name__)


class DiaperHandler:
    @staticmethod
    async def handle_diaper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "Выберите тип подгузника:",
            reply_markup=diaper_type_keyboard()
        )

    @staticmethod
    async def handle_diaper_type(update: Update, context: ContextTypes.DEFAULT_TYPE, diaper_type: str):
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        baby = Baby.get_current()

        if not baby:
            await query.edit_message_text("❌ Сначала добавьте ребенка")
            return

        type_names = {
            'wet': 'мокрый',
            'dirty': 'грязный',
            'mixed': 'смешанный'
        }

        await EventService.add_diaper(context, baby['id'], user_id, user_name, type_names.get(diaper_type, diaper_type))
        await query.edit_message_text(
            f"✅ Подгузник записан! Выберите следующее действие:",
            reply_markup=main_menu_keyboard()
        )