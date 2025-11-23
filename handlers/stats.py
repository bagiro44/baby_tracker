from telegram import Update
from telegram.ext import ContextTypes
from models.baby import Baby
from services.stats_service import StatsService
from utils.keyboards import stats_period_keyboard, main_menu_keyboard
import logging

logger = logging.getLogger(__name__)


class StatsHandler:
    @staticmethod
    async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        try:
            baby = Baby.get_current()
            if not baby:
                await query.edit_message_text("❌ Сначала добавьте ребенка")
                return

            await query.edit_message_text(
                "📊 Выберите период для статистики:",
                reply_markup=stats_period_keyboard()
            )
        except Exception as e:
            logger.error(f"Error in handle_stats: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при получении статистики",
                reply_markup=main_menu_keyboard()
            )

    @staticmethod
    async def handle_stats_period(update: Update, context: ContextTypes.DEFAULT_TYPE, period: str):
        query = update.callback_query
        await query.answer()

        try:
            baby = Baby.get_current()
            if not baby:
                await query.edit_message_text("❌ Сначала добавьте ребенка")
                return

            # Определяем период в часах
            if period == "today":
                period_hours = None  # Сегодня с 00:00
                period_name = "сегодня"
            elif period == "24h":
                period_hours = 24
                period_name = "последние 24 часа"
            elif period == "3days":
                period_hours = 72
                period_name = "последние 3 дня"
            else:
                period_hours = 24
                period_name = "последние 24 часа"

            # Получаем статистику
            stats = StatsService.get_stats(baby['id'], period_hours)

            if stats:
                stats_text = StatsService.format_stats(stats)
                await query.edit_message_text(
                    stats_text,
                    reply_markup=main_menu_keyboard()
                )
            else:
                await query.edit_message_text(
                    "❌ Не удалось получить статистику",
                    reply_markup=main_menu_keyboard()
                )
        except Exception as e:
            logger.error(f"Error in handle_stats_period: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при получении статистики",
                reply_markup=main_menu_keyboard()
            )