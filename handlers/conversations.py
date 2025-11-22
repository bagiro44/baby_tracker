from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
import re
from leo_bot.config import (
    SELECTING_AMOUNT, CUSTOM_AMOUNT, ENTERING_WEIGHT, SELECTING_TIME,
    ENTERING_CUSTOM_TIME, SELECTING_SLEEP_TIME, BREAST_FEEDING_TYPE, BREAST_FEEDING_SIDE,
    logger
)
from leo_bot.utils.telegram_utils import check_access, get_user_display_name, send_to_chat
from leo_bot.utils.time_utils import get_msk_time, parse_custom_time
from leo_bot.utils.reminders import schedule_feeding_reminder, send_feeding_reminder
from leo_bot.keyboards.menus import (
    get_main_keyboard, get_amount_keyboard, get_time_keyboard,
    get_breast_feeding_type_keyboard, get_breast_side_keyboard
)

# Импортируем tracker из модуля tracker, чтобы избежать циклических импортов
from leo_bot.tracker import tracker


# === ИСКУССТВЕННОЕ КОРМЛЕНИЕ ===
async def start_bottle_feeding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        return ConversationHandler.END

    await update.message.reply_text(
        "🥛 Выберите количество смеси или введите свое значение:",
        reply_markup=get_amount_keyboard()
    )
    return SELECTING_AMOUNT


async def select_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📝 Свое значение":
        await update.message.reply_text("📝 Введите количество смеси в мл:", reply_markup=ReplyKeyboardRemove())
        return CUSTOM_AMOUNT

    if text.endswith(" мл"):
        try:
            amount = int(text.replace(" мл", ""))
            if 10 <= amount <= 300:
                context.user_data['amount'] = amount
                await update.message.reply_text("⏰ Выберите время кормления:", reply_markup=get_time_keyboard())
                return SELECTING_TIME
            else:
                await update.message.reply_text(
                    "❌ Пожалуйста, введите значение от 10 до 300 мл",
                    reply_markup=get_amount_keyboard()
                )
                return SELECTING_AMOUNT
        except ValueError:
            await update.message.reply_text(
                "❌ Пожалуйста, выберите количество из предложенных вариантов или введите число",
                reply_markup=get_amount_keyboard()
            )
            return SELECTING_AMOUNT

    await update.message.reply_text(
        "❌ Пожалуйста, выберите количество из предложенных вариантов",
        reply_markup=get_amount_keyboard()
    )
    return SELECTING_AMOUNT


async def custom_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    try:
        amount = int(text)
        if 10 <= amount <= 300:
            context.user_data['amount'] = amount
            await update.message.reply_text("⏰ Выберите время кормления:", reply_markup=get_time_keyboard())
            return SELECTING_TIME
        else:
            await update.message.reply_text("❌ Пожалуйста, введите значение от 10 до 300 мл:")
            return CUSTOM_AMOUNT
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите число (например: 45):")
        return CUSTOM_AMOUNT


async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    amount = context.user_data.get('amount')

    if text == "⏰ Сейчас":
        custom_time = None
    elif text == "📝 Свое время":
        await update.message.reply_text("📝 Введите время в формате HHMM (4 цифры, например 1430):",
                                        reply_markup=ReplyKeyboardRemove())
        return ENTERING_CUSTOM_TIME
    else:
        try:
            time_match = re.match(r'(\d{1,2}):(\d{2})', text)
            if time_match:
                hours, minutes = map(int, time_match.groups())
                custom_time = parse_custom_time(f"{hours:02d}{minutes:02d}")
            else:
                await update.message.reply_text(
                    "❌ Неверный формат времени. Выберите время из предложенных вариантов:",
                    reply_markup=get_time_keyboard()
                )
                return SELECTING_TIME
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат времени. Выберите время из предложенных вариантов:",
                reply_markup=get_time_keyboard()
            )
            return SELECTING_TIME

    result = tracker.add_feeding(user_id, "bottle", amount, custom_time)

    user_name = await get_user_display_name(update)
    time_str = custom_time.strftime('%H:%M') if custom_time else get_msk_time().strftime('%H:%M')
    chat_message = (
        f"🥛 <b>Искусственное кормление</b>\n\n"
        f"• Количество: {amount} мл\n"
        f"• Время: {time_str}\n"
        f"• Внес: {user_name}"
    )
    await send_to_chat(context, chat_message)

    if custom_time:
        reminder_delay = 150 * 60
        time_since_feeding = (get_msk_time() - custom_time).total_seconds()

        if time_since_feeding < reminder_delay:
            remaining_time = reminder_delay - time_since_feeding
            context.job_queue.run_once(
                send_feeding_reminder,
                remaining_time,
                data={
                    'user_id': user_id,
                    'amount': amount,
                    'feeding_id': tracker.get_next_id(tracker.feeding_sheet) - 1
                }
            )
    else:
        await schedule_feeding_reminder(context, user_id, amount)

    time_str = custom_time.strftime('%H:%M') if custom_time else "сейчас"
    await update.message.reply_text(f"{result}\n\n⏰ Напоминание установлено на 2.5 часа",
                                    reply_markup=get_main_keyboard())

    if 'amount' in context.user_data:
        del context.user_data['amount']

    return ConversationHandler.END


async def custom_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    amount = context.user_data.get('amount')

    try:
        custom_time = parse_custom_time(text)
        result = tracker.add_feeding(user_id, "bottle", amount, custom_time)

        user_name = await get_user_display_name(update)
        time_str = custom_time.strftime('%H:%M')
        chat_message = (
            f"🥛 <b>Искусственное кормление</b>\n\n"
            f"• Количество: {amount} мл\n"
            f"• Время: {time_str}\n"
            f"• Внес: {user_name}"
        )
        await send_to_chat(context, chat_message)

        reminder_delay = 150 * 60
        time_since_feeding = (get_msk_time() - custom_time).total_seconds()

        if time_since_feeding < reminder_delay:
            remaining_time = reminder_delay - time_since_feeding
            context.job_queue.run_once(
                send_feeding_reminder,
                remaining_time,
                data={
                    'user_id': user_id,
                    'amount': amount,
                    'feeding_id': tracker.get_next_id(tracker.feeding_sheet) - 1
                }
            )

        await update.message.reply_text(f"{result}\n\n⏰ Напоминание установлено на 2.5 часа",
                                        reply_markup=get_main_keyboard())

        if 'amount' in context.user_data:
            del context.user_data['amount']

        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("❌ Неверный формат. Введите время в формате HHMM (4 цифры, например 1430):")
        return ENTERING_CUSTOM_TIME


# === ВВОД ВЕСА ===
async def start_weight_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        return ConversationHandler.END

    await update.message.reply_text("⚖️ Введите вес ребенка в граммах (например: 4250):",
                                    reply_markup=ReplyKeyboardRemove())
    return ENTERING_WEIGHT


async def process_weight_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    try:
        weight_grams = int(text)
        if 1000 <= weight_grams <= 20000:
            context.user_data['weight_grams'] = weight_grams
            await update.message.reply_text(
                "💡 Добавьте примечание (например: 'утреннее взвешивание', 'перед кормлением' или оставьте пустым):",
                reply_markup=ReplyKeyboardMarkup([["Пропустить"]], resize_keyboard=True)
            )
            return ENTERING_WEIGHT + 1
        else:
            await update.message.reply_text("❌ Пожалуйста, введите вес от 1000 до 20000 грамм:")
            return ENTERING_WEIGHT
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите целое число (например: 4250):")
        return ENTERING_WEIGHT


async def process_weight_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    note = "" if text == "Пропустить" else text
    weight_grams = context.user_data.get('weight_grams')

    if weight_grams:
        result = tracker.add_weight(user_id, weight_grams, note)

        user_name = await get_user_display_name(update)
        weight_kg = weight_grams / 1000
        chat_message = (
            f"⚖️ <b>Новый вес ребенка</b>\n\n"
            f"• Вес: {weight_grams}г ({weight_kg:.3f}кг)\n"
            f"• Внес: {user_name}\n"
        )
        if note:
            chat_message += f"• Примечание: {note}"

        await send_to_chat(context, chat_message)
        await update.message.reply_text(result, reply_markup=get_main_keyboard())

    if 'weight_grams' in context.user_data:
        del context.user_data['weight_grams']

    return ConversationHandler.END


# === ГРУДНОЕ КОРМЛЕНИЕ ===
async def start_breast_feeding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        return ConversationHandler.END

    await update.message.reply_text("🍼 Выберите время кормления:", reply_markup=get_time_keyboard())
    return SELECTING_TIME


async def select_breast_feeding_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "⏰ Сейчас":
        custom_time = None
    elif text == "📝 Свое время":
        await update.message.reply_text("📝 Введите время в формате HHMM (4 цифры, например 1430):",
                                        reply_markup=ReplyKeyboardRemove())
        return ENTERING_CUSTOM_TIME + 1
    else:
        try:
            time_match = re.match(r'(\d{1,2}):(\d{2})', text)
            if time_match:
                hours, minutes = map(int, time_match.groups())
                custom_time = parse_custom_time(f"{hours:02d}{minutes:02d}")
            else:
                await update.message.reply_text(
                    "❌ Неверный формат времени. Выберите время из предложенных вариантов:",
                    reply_markup=get_time_keyboard()
                )
                return SELECTING_TIME
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат времени. Выберите время из предложенных вариантов:",
                reply_markup=get_time_keyboard()
            )
            return SELECTING_TIME

    context.user_data['breast_feeding_time'] = custom_time
    await update.message.reply_text("🤱 Это начало или конец кормления?",
                                    reply_markup=get_breast_feeding_type_keyboard())
    return BREAST_FEEDING_TYPE


async def select_breast_feeding_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "Пропустить":
        breast_type = None
    elif text in ["Начало кормления", "Конец кормления"]:
        breast_type = text
    else:
        await update.message.reply_text("❌ Пожалуйста, выберите вариант из предложенных:",
                                        reply_markup=get_breast_feeding_type_keyboard())
        return BREAST_FEEDING_TYPE

    context.user_data['breast_type'] = breast_type
    await update.message.reply_text("🤱 Какая грудь последняя?", reply_markup=get_breast_side_keyboard())
    return BREAST_FEEDING_SIDE


async def select_breast_side(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "Пропустить":
        breast_side = None
    elif text in ["Левая", "Правая"]:
        breast_side = text
    else:
        await update.message.reply_text("❌ Пожалуйста, выберите вариант из предложенных:",
                                        reply_markup=get_breast_side_keyboard())
        return BREAST_FEEDING_SIDE

    custom_time = context.user_data.get('breast_feeding_time')
    breast_type = context.user_data.get('breast_type')

    result = tracker.add_feeding(user_id, "breast", None, custom_time, breast_type, breast_side)

    user_name = await get_user_display_name(update)
    time_str = custom_time.strftime('%H:%M') if custom_time else get_msk_time().strftime('%H:%M')

    breast_info = ""
    if breast_type:
        breast_info = f" ({breast_type}"
        if breast_side:
            breast_info += f", {breast_side}"
        breast_info += ")"

    chat_message = (
        f"🍼 <b>Грудное кормление</b>\n\n"
        f"• Время: {time_str}{breast_info}\n"
        f"• Внес: {user_name}"
    )
    await send_to_chat(context, chat_message)
    await update.message.reply_text(result, reply_markup=get_main_keyboard())

    for key in ['breast_feeding_time', 'breast_type']:
        if key in context.user_data:
            del context.user_data[key]

    return ConversationHandler.END


async def custom_breast_feeding_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    try:
        custom_time = parse_custom_time(text)
        context.user_data['breast_feeding_time'] = custom_time
        await update.message.reply_text("🤱 Это начало или конец кормления?",
                                        reply_markup=get_breast_feeding_type_keyboard())
        return BREAST_FEEDING_TYPE
    except ValueError:
        await update.message.reply_text("❌ Неверный формат. Введите время в формате HHMM (4 цифры, например 1430):")
        return ENTERING_CUSTOM_TIME + 1


# === СОН ===
async def start_sleep_with_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        return ConversationHandler.END

    await update.message.reply_text("👶 Выберите время начала сна:", reply_markup=get_time_keyboard())
    return SELECTING_SLEEP_TIME


async def select_sleep_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "⏰ Сейчас":
        custom_time = None
    elif text == "📝 Свое время":
        await update.message.reply_text("📝 Введите время начала сна в формате HHMM (4 цифры, например 1430):",
                                        reply_markup=ReplyKeyboardRemove())
        return ENTERING_CUSTOM_TIME + 2
    else:
        try:
            time_match = re.match(r'(\d{1,2}):(\d{2})', text)
            if time_match:
                hours, minutes = map(int, time_match.groups())
                custom_time = parse_custom_time(f"{hours:02d}{minutes:02d}")
            else:
                await update.message.reply_text(
                    "❌ Неверный формат времени. Выберите время из предложенных вариантов:",
                    reply_markup=get_time_keyboard()
                )
                return SELECTING_SLEEP_TIME
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат времени. Выберите время из предложенных вариантов:",
                reply_markup=get_time_keyboard()
            )
            return SELECTING_SLEEP_TIME

    result = tracker.start_sleep(user_id, custom_time)

    user_name = await get_user_display_name(update)
    time_str = custom_time.strftime('%H:%M') if custom_time else get_msk_time().strftime('%H:%M')
    chat_message = (
        f"😴 <b>Малыш уснул</b>\n\n"
        f"• Время: {time_str}\n"
        f"• Внес: {user_name}"
    )
    await send_to_chat(context, chat_message)
    await update.message.reply_text(result, reply_markup=get_main_keyboard())
    return ConversationHandler.END


async def custom_sleep_start_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    try:
        custom_time = parse_custom_time(text)
        result = tracker.start_sleep(user_id, custom_time)

        user_name = await get_user_display_name(update)
        time_str = custom_time.strftime('%H:%M')
        chat_message = (
            f"😴 <b>Малыш уснул</b>\n\n"
            f"• Время: {time_str}\n"
            f"• Внес: {user_name}"
        )
        await send_to_chat(context, chat_message)
        await update.message.reply_text(result, reply_markup=get_main_keyboard())
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Неверный формат. Введите время в формате HHMM (4 цифры, например 1430):")
        return ENTERING_CUSTOM_TIME + 2


async def end_sleep_with_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        return ConversationHandler.END

    await update.message.reply_text("🛏️ Выберите время окончания сна:", reply_markup=get_time_keyboard())
    return SELECTING_SLEEP_TIME + 1


async def select_sleep_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "⏰ Сейчас":
        custom_time = None
    elif text == "📝 Свое время":
        await update.message.reply_text("📝 Введите время окончания сна в формате HHMM (4 цифры, например 1430):",
                                        reply_markup=ReplyKeyboardRemove())
        return ENTERING_CUSTOM_TIME + 3
    else:
        try:
            time_match = re.match(r'(\d{1,2}):(\d{2})', text)
            if time_match:
                hours, minutes = map(int, time_match.groups())
                custom_time = parse_custom_time(f"{hours:02d}{minutes:02d}")
            else:
                await update.message.reply_text(
                    "❌ Неверный формат времени. Выберите время из предложенных вариантов:",
                    reply_markup=get_time_keyboard()
                )
                return SELECTING_SLEEP_TIME + 1
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат времени. Выберите время из предложенных вариантов:",
                reply_markup=get_time_keyboard()
            )
            return SELECTING_SLEEP_TIME + 1

    result = tracker.end_sleep(user_id, custom_time)

    duration_match = re.search(r'Продолжительность: (\d+)ч (\d+)м', result)
    if duration_match:
        hours = duration_match.group(1)
        minutes = duration_match.group(2)

        user_name = await get_user_display_name(update)
        time_str = custom_time.strftime('%H:%M') if custom_time else get_msk_time().strftime('%H:%M')
        chat_message = (
            f"🛌 <b>Малыш проснулся</b>\n\n"
            f"• Время: {time_str}\n"
            f"• Продолжительность сна: {hours}ч {minutes}м\n"
            f"• Внес: {user_name}"
        )
        await send_to_chat(context, chat_message)

    await update.message.reply_text(result, reply_markup=get_main_keyboard())
    return ConversationHandler.END


async def custom_sleep_end_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    try:
        custom_time = parse_custom_time(text)
        result = tracker.end_sleep(user_id, custom_time)

        duration_match = re.search(r'Продолжительность: (\d+)ч (\d+)м', result)
        if duration_match:
            hours_duration = duration_match.group(1)
            minutes_duration = duration_match.group(2)

            user_name = await get_user_display_name(update)
            time_str = custom_time.strftime('%H:%M')
            chat_message = (
                f"🛌 <b>Малыш проснулся</b>\n\n"
                f"• Время: {time_str}\n"
                f"• Продолжительность сна: {hours_duration}ч {minutes_duration}м\n"
                f"• Внес: {user_name}"
            )
            await send_to_chat(context, chat_message)

        await update.message.reply_text(result, reply_markup=get_main_keyboard())
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Неверный формат. Введите время в формате HHMM (4 цифры, например 1430):")
        return ENTERING_CUSTOM_TIME + 3


# === ОБЩИЕ ФУНКЦИИ ===
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена операции"""
    for key in ['weight_grams', 'amount', 'breast_feeding_time', 'breast_type']:
        if key in context.user_data:
            del context.user_data[key]

    await update.message.reply_text("Операция отменена", reply_markup=get_main_keyboard())
    return ConversationHandler.END


def setup_conversation_handlers(application):
    """Регистрация ConversationHandler"""

    # Искусственное кормление
    bottle_feeding_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^(🥛 Искусственное кормление)$"), start_bottle_feeding),
        ],
        states={
            SELECTING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_amount)],
            CUSTOM_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_amount)],
            SELECTING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_time)],
            ENTERING_CUSTOM_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_time_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Ввод веса
    weight_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^(⚖️ Вес ребенка)$"), start_weight_input),
        ],
        states={
            ENTERING_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_weight_input)],
            ENTERING_WEIGHT + 1: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_weight_note)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Грудное кормление
    breast_feeding_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^(🍼 Грудное кормление)$"), start_breast_feeding)],
        states={
            SELECTING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_breast_feeding_time)],
            ENTERING_CUSTOM_TIME + 1: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, custom_breast_feeding_time_input)],
            BREAST_FEEDING_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_breast_feeding_type)],
            BREAST_FEEDING_SIDE: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_breast_side)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Начало сна
    start_sleep_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^(👶 Начать сон)$"), start_sleep_with_time)],
        states={
            SELECTING_SLEEP_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_sleep_start_time)],
            ENTERING_CUSTOM_TIME + 2: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_sleep_start_time_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Окончание сна
    end_sleep_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^(🛏️ Закончить сон)$"), end_sleep_with_time)],
        states={
            SELECTING_SLEEP_TIME + 1: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_sleep_end_time)],
            ENTERING_CUSTOM_TIME + 3: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_sleep_end_time_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Регистрация всех ConversationHandler
    application.add_handler(bottle_feeding_conv_handler)
    application.add_handler(weight_conv_handler)
    application.add_handler(breast_feeding_conv_handler)
    application.add_handler(start_sleep_conv_handler)
    application.add_handler(end_sleep_conv_handler)