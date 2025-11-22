from telegram import Update
from telegram.ext import ContextTypes
from models.baby import Baby
from models.user import UserState
from utils.keyboards import main_menu_keyboard
import logging

logger = logging.getLogger(__name__)


class BaseHandler:
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        # Check if user is authorized
        from config import ADMIN_USER_IDS
        if user.id not in ADMIN_USER_IDS:
            await update.message.reply_text("❌ У вас нет доступа к этому боту.")
            return

        # Check if baby exists
        baby = Baby.get_current()
        if not baby:
            UserState.set_state(user.id, "awaiting_baby_name")
            await update.message.reply_text("👶 Привет! Давайте добавим ребенка. Введите имя:")
            return

        await BaseHandler.show_main_menu(update, context)

    @staticmethod
    async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = "Выберите действие:"

        # Проверяем тип update и соответствующим образом отвечаем
        if update.message:
            # Если это обычное сообщение
            await update.message.reply_text(text, reply_markup=main_menu_keyboard())
        elif update.callback_query:
            # Если это callback от кнопки
            await update.callback_query.edit_message_text(text, reply_markup=main_menu_keyboard())
        else:
            # Fallback - отправляем новое сообщение
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=main_menu_keyboard()
            )

    @staticmethod
    async def handle_main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик для кнопки главного меню"""
        query = update.callback_query
        await query.answer()
        await BaseHandler.show_main_menu(update, context)

    @staticmethod
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = UserState.get_state(user_id)

        if not user_state:
            await update.message.reply_text("Пожалуйста, используйте кнопки меню.")
            return

        state = user_state['state']
        text = update.message.text.strip()

        if state == "awaiting_baby_name":
            UserState.set_state(user_id, "awaiting_baby_birthdate", {"name": text})
            await update.message.reply_text("Введите дату рождения ребенка (ДД.ММ.ГГГГ):")

        elif state == "awaiting_baby_birthdate":
            from datetime import datetime
            try:
                birth_date = datetime.strptime(text, "%d.%m.%Y").date()
                state_data = user_state.get('data', {})
                baby_name = state_data.get('name', '')

                baby_id = Baby.add(baby_name, birth_date)
                UserState.clear_state(user_id)

                await update.message.reply_text(
                    f"✅ Ребенок {baby_name} добавлен!\n"
                    f"Дата рождения: {birth_date.strftime('%d.%m.%Y')}"
                )
                await BaseHandler.show_main_menu(update, context)

            except ValueError:
                await update.message.reply_text("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ")


        elif state == "awaiting_custom_time":

            from utils.time_utils import parse_custom_time

            custom_time = parse_custom_time(text)

            if not custom_time:
                await update.message.reply_text("❌ Неверный формат времени. Используйте ЧЧММ (например, 1430)")

                return

            state_data = user_state.get('data', {})

            action_type = state_data.get('action_type')

            baby_id = state_data.get('baby_id')

            if action_type == "bottle_feeding":

                UserState.set_state(user_id, "awaiting_bottle_volume", {

                    "baby_id": baby_id,

                    "timestamp": custom_time

                })

                await update.message.reply_text("Введите объем смеси в мл:")

            elif action_type == "sleep_start":

                await EventService.start_sleep(context, baby_id, user_id, custom_time)

                await update.message.reply_text("✅ Начало сна записано!")

                await BaseHandler.show_main_menu(update, context)

            elif action_type == "sleep_end":

                result = await EventService.end_sleep(context, baby_id, user_id, custom_time)

                if result:

                    await update.message.reply_text("✅ Конец сна записан!")

                else:

                    await update.message.reply_text("❌ Не найдено активное начало сна")

                await BaseHandler.show_main_menu(update, context)

            elif action_type == "breast_start":

                await EventService.start_breast_feeding(context, baby_id, user_id, custom_time)

                await update.message.reply_text("✅ Начало кормления записано!")

                await BaseHandler.show_main_menu(update, context)

            elif action_type == "breast_end":

                UserState.set_state(user_id, "awaiting_breast_side", {

                    "baby_id": baby_id,

                    "timestamp": custom_time

                })

                from utils.keyboards import breast_side_keyboard

                await update.message.reply_text("Выберите грудь:", reply_markup=breast_side_keyboard())


        # В обработке awaiting_bottle_volume:

        elif state == "awaiting_bottle_volume":

            try:

                volume = int(text)

                state_data = user_state.get('data', {})

                baby_id = state_data.get('baby_id')

                timestamp = state_data.get('timestamp')

                await EventService.add_bottle_feeding(context, baby_id, user_id, volume, timestamp)

                UserState.clear_state(user_id)

                await update.message.reply_text(f"✅ Кормление {volume}мл записано!")

                await BaseHandler.show_main_menu(update, context)


            except ValueError:

                await update.message.reply_text("❌ Введите число (объем в мл)")


        # В обработке awaiting_weight:

        elif state == "awaiting_weight":

            try:

                weight = int(text)

                baby = Baby.get_current()

                if baby:

                    await EventService.add_weight(context, baby['id'], user_id, weight)

                    UserState.clear_state(user_id)

                    await update.message.reply_text(f"✅ Вес {weight}г записан!")

                    await BaseHandler.show_main_menu(update, context)

                else:

                    await update.message.reply_text("❌ Ошибка: ребенок не найден")

            except ValueError:

                await update.message.reply_text("❌ Введите число (вес в граммах)")