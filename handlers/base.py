from telegram import Update
from telegram.ext import ContextTypes
from models.baby import Baby
from models.user import UserState
from utils.keyboards import main_menu_keyboard, gender_selection_keyboard
import logging

logger = logging.getLogger(__name__)


class BaseHandler:
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        from config import ADMIN_USER_IDS
        if user.id not in ADMIN_USER_IDS:
            await update.message.reply_text("❌ У вас нет доступа к этому боту.")
            return

        baby = Baby.get_current()
        if not baby:
            UserState.set_state(user.id, "awaiting_baby_name")
            await update.message.reply_text("👶 Привет! Давайте добавим ребенка. Введите имя:")
            return

        await BaseHandler.show_main_menu(update, context)

    @staticmethod
    async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = "Выберите действие:"

        if update.message:
            await update.message.reply_text(text, reply_markup=main_menu_keyboard())
        elif update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=main_menu_keyboard())
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=main_menu_keyboard()
            )

    @staticmethod
    async def handle_main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await BaseHandler.show_main_menu(update, context)

    @staticmethod
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = UserState.get_state(user_id)

        if not user_state:
            await update.message.reply_text("Пожалуйста, используйте кнопки меню.", reply_markup=main_menu_keyboard())
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

                UserState.set_state(user_id, "awaiting_baby_gender", {
                    "name": baby_name,
                    "birth_date": birth_date
                })
                await update.message.reply_text(
                    "Выберите пол ребенка:",
                    reply_markup=gender_selection_keyboard()
                )

            except ValueError:
                await update.message.reply_text("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ")

        elif state == "awaiting_baby_gender":
            await update.message.reply_text("Пожалуйста, выберите пол используя кнопки ниже")

        elif state == "awaiting_custom_time":
            from utils.time_utils import parse_custom_time

            custom_time = parse_custom_time(text)
            if not custom_time:
                await update.message.reply_text("❌ Неверный формат времени. Используйте ЧЧММ (например, 1430)")
                return

            state_data = user_state.get('data', {})
            action_type = state_data.get('action_type')
            baby_id = state_data.get('baby_id')
            user_name = update.effective_user.first_name

            if action_type == "bottle_feeding":
                from services.event_service import EventService
                UserState.clear_state(user_id)
                volume = state_data.get('volume')
                await EventService.add_bottle_feeding(context, baby_id, user_id, user_name, volume, custom_time)
                await update.message.reply_text(
                    "✅ Бутылочка записана!",
                    reply_markup=main_menu_keyboard()
                )
            elif action_type == "sleep_start":
                from services.event_service import EventService
                await EventService.start_sleep(context, baby_id, user_id, user_name, custom_time)
                await update.message.reply_text(
                    "✅ Начало сна записано! Выберите следующее действие:",
                    reply_markup=main_menu_keyboard()
                )
            elif action_type == "sleep_end":
                from services.event_service import EventService
                result = await EventService.end_sleep(context, baby_id, user_id, user_name, custom_time)
                if result:
                    await update.message.reply_text(
                        "✅ Конец сна записан! Выберите следующее действие:",
                        reply_markup=main_menu_keyboard()
                    )
                else:
                    await update.message.reply_text(
                        "❌ Не найдено активное начало сна. Выберите действие:",
                        reply_markup=main_menu_keyboard()
                    )
            elif action_type == "breast_start":
                from services.event_service import EventService
                await EventService.start_breast_feeding(context, baby_id, user_id, user_name, custom_time)
                await update.message.reply_text(
                    "✅ Начало кормления записано! Выберите следующее действие:",
                    reply_markup=main_menu_keyboard()
                )
            elif action_type == "breast_end":
                UserState.set_state(user_id, "awaiting_breast_side", {
                    "baby_id": baby_id,
                    "timestamp": custom_time
                })
                from utils.keyboards import breast_side_keyboard
                await update.message.reply_text("Выберите грудь:", reply_markup=breast_side_keyboard())

        elif state == "awaiting_bottle_volume":
            try:
                volume = int(text)
                await update.message.reply_text(
                    "Когда было кормление?",
                    reply_markup=time_selection_keyboard("bottle_feeding")
                )
                # context.user_data['bottle_volume'] = volume
                # state_data = user_state.get('data', {})
                # baby_id = state_data.get('baby_id')
                # timestamp = state_data.get('timestamp')
                # user_name = update.effective_user.first_name
                #
                # from services.event_service import EventService
                # await EventService.add_bottle_feeding(context, baby_id, user_id, user_name, volume, timestamp)
                # UserState.clear_state(user_id)
                #
                # await update.message.reply_text(
                #     f"✅ Кормление {volume}мл записано! Выберите следующее действие:",
                #     reply_markup=main_menu_keyboard()
                # )

            except ValueError:
                await update.message.reply_text("❌ Введите число (объем в мл)")

        elif state == "awaiting_weight":
            try:
                weight = int(text)
                baby = Baby.get_current()
                user_name = update.effective_user.first_name
                if baby:
                    from services.event_service import EventService
                    await EventService.add_weight(context, baby['id'], user_id, user_name, weight)
                    UserState.clear_state(user_id)
                    await update.message.reply_text(
                        f"✅ Вес {weight}г записан! Выберите следующее действие:",
                        reply_markup=main_menu_keyboard()
                    )
                else:
                    await update.message.reply_text("❌ Ошибка: ребенок не найден")
            except ValueError:
                await update.message.reply_text("❌ Введите число (вес в граммах)")

    @staticmethod
    async def handle_gender_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, gender: str):
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        user_state = UserState.get_state(user_id)

        if not user_state or user_state['state'] != "awaiting_baby_gender":
            await query.edit_message_text("❌ Ошибка: неверное состояние")
            return

        state_data = user_state.get('data', {})
        baby_name = state_data.get('name')
        birth_date = state_data.get('birth_date')

        if not baby_name or not birth_date:
            await query.edit_message_text("❌ Ошибка: данные ребенка не найдены")
            return

        baby_id = Baby.add(baby_name, birth_date, gender)
        UserState.clear_state(user_id)

        gender_text = "мальчик" if gender == "male" else "девочка"
        await query.edit_message_text(
            f"✅ Ребенок {baby_name} добавлен!\n"
            f"Дата рождения: {birth_date.strftime('%d.%m.%Y')}\n"
            f"Пол: {gender_text}\n\n"
            f"Выберите действие:",
            reply_markup=main_menu_keyboard()
        )