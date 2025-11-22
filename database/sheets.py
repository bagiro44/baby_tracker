import os
import gspread
from google.oauth2.service_account import Credentials
import logging
from datetime import datetime, timezone, timedelta

# Создаем логгер для этого модуля
logger = logging.getLogger(__name__)

# Московский часовой пояс (UTC+3)
MSK_TIMEZONE = timezone(timedelta(hours=3))

def get_msk_time():
    """Получить текущее время в часовом поясе MSK (UTC+3)"""
    return datetime.now(MSK_TIMEZONE)

class GoogleSheetsBabyTracker:
    def __init__(self, credentials_file, spreadsheet_name):
        self.credentials_file = credentials_file
        self.spreadsheet_name = spreadsheet_name
        self.client = None
        self.spreadsheet = None
        self.sleep_sheet = None
        self.feeding_sheet = None
        self.weight_sheet = None
        self.connect_to_sheets()

    def connect_to_sheets(self):
        """Подключение к Google Sheets"""
        try:
            if not os.path.exists(self.credentials_file):
                raise FileNotFoundError(f"Файл {self.credentials_file} не найден")

            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]

            creds = Credentials.from_service_account_file(self.credentials_file, scopes=scope)
            self.client = gspread.authorize(creds)

            try:
                self.spreadsheet = self.client.open(self.spreadsheet_name)
                logger.info(f"Таблица '{self.spreadsheet_name}' найдена")
            except gspread.SpreadsheetNotFound:
                self.spreadsheet = self.client.create(self.spreadsheet_name)
                logger.info(f"Создана новая таблица '{self.spreadsheet_name}'")

            self.init_sheets()
            logger.info("Успешно подключено к Google Sheets")

        except Exception as e:
            logger.error(f"Ошибка подключения к Google Sheets: {e}")
            raise

    def init_sheets(self):
        """Инициализация листов таблицы"""
        # Лист для сна
        try:
            self.sleep_sheet = self.spreadsheet.worksheet("Сон")
        except gspread.WorksheetNotFound:
            self.sleep_sheet = self.spreadsheet.add_worksheet(title="Сон", rows="1000", cols="10")
            self.sleep_sheet.append_row([
                "ID", "Начало сна", "Конец сна", "Продолжительность (мин)",
                "Начал пользователь", "Завершил пользователь", "Дата создания", "Дата обновления"
            ])

        # Лист для кормлений
        try:
            self.feeding_sheet = self.spreadsheet.worksheet("Кормления")
        except gspread.WorksheetNotFound:
            self.feeding_sheet = self.spreadsheet.add_worksheet(title="Кормления", rows="1000", cols="10")
            self.feeding_sheet.append_row([
                "ID", "Тип кормления", "Количество (мл)", "Пользователь",
                "Временная метка", "Дата создания", "Напоминание отправлено", "Тип грудного", "Последняя грудь"
            ])

        # Лист для веса
        try:
            self.weight_sheet = self.spreadsheet.worksheet("Вес")
        except gspread.WorksheetNotFound:
            self.weight_sheet = self.spreadsheet.add_worksheet(title="Вес", rows="1000", cols="10")
            self.weight_sheet.append_row([
                "ID", "Вес (г)", "Пользователь", "Временная метка", "Дата создания", "Примечание"
            ])

    def get_next_id(self, sheet):
        """Получить следующий ID для записи"""
        try:
            ids = sheet.col_values(1)
            if len(ids) <= 1:
                return 1
            return max(int(id) for id in ids[1:] if id.isdigit()) + 1
        except Exception as e:
            logger.error(f"Ошибка получения следующего ID: {e}")
            return 1

    def start_sleep(self, user_id, custom_time=None):
        """Начать отслеживание сна"""
        try:
            active_sleep = self.get_active_sleep()
            if active_sleep:
                return "❌ Уже есть активный сеанс сна!"

            next_id = self.get_next_id(self.sleep_sheet)
            start_time = custom_time if custom_time else get_msk_time()

            self.sleep_sheet.append_row([
                next_id,
                start_time.isoformat(),
                "",
                0,
                user_id,
                "",
                get_msk_time().isoformat(),
                get_msk_time().isoformat()
            ])

            logger.info(f"Сеанс сна начат пользователем {user_id} в {start_time}")
            return f"✅ Сеанс сна начат в {start_time.strftime('%H:%M')}!"

        except Exception as e:
            logger.error(f"Ошибка при начале сна: {e}")
            return "❌ Ошибка при записи в таблицу"

    def end_sleep(self, user_id, custom_time=None):
        """Завершить отслеживание сна"""
        try:
            active_sleep = self.get_active_sleep()
            if not active_sleep:
                return "❌ Нет активных сеансов сна!"

            sleep_id = active_sleep[0]
            start_time = datetime.fromisoformat(active_sleep[1]).replace(tzinfo=MSK_TIMEZONE)
            end_time = custom_time if custom_time else get_msk_time()

            duration = int((end_time - start_time).total_seconds() / 60)

            sleep_records = self.sleep_sheet.get_all_records()
            for i, record in enumerate(sleep_records, start=2):
                if record.get("ID") == sleep_id and not record.get("Конец сна"):
                    self.sleep_sheet.update_cell(i, 3, end_time.isoformat())
                    self.sleep_sheet.update_cell(i, 4, duration)
                    self.sleep_sheet.update_cell(i, 6, user_id)
                    self.sleep_sheet.update_cell(i, 8, end_time.isoformat())

                    hours = duration // 60
                    minutes = duration % 60
                    logger.info(f"Сеанс сна завершен пользователем {user_id}, продолжительность: {hours}ч {minutes}м")
                    return f"✅ Сеанс сна завершен в {end_time.strftime('%H:%M')}!\nПродолжительность: {hours}ч {minutes}м"

            return "❌ Ошибка при завершении сна"

        except Exception as e:
            logger.error(f"Ошибка при завершении сна: {e}")
            return "❌ Ошибка при записи в таблицу"

    def get_active_sleep(self):
        """Получить активный сеанс сна"""
        try:
            sleep_records = self.sleep_sheet.get_all_records()
            for record in sleep_records:
                if record.get("Конец сна") == "" or not record.get("Конец сна"):
                    return [
                        record.get("ID"),
                        record.get("Начало сна"),
                        record.get("Конец сна"),
                        record.get("Продолжительность (мин)"),
                        record.get("Начал пользователь"),
                        record.get("Завершил пользователь")
                    ]
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении активного сна: {e}")
            return None

    def add_feeding(self, user_id, feeding_type="breast", amount=None, custom_time=None, breast_type=None, breast_side=None):
        """Добавить запись о кормлении"""
        try:
            next_id = self.get_next_id(self.feeding_sheet)
            timestamp = custom_time if custom_time else get_msk_time()

            feeding_data = [
                next_id,
                "Грудное" if feeding_type == "breast" else "Искусственное",
                amount if amount else "",
                user_id,
                timestamp.isoformat(),
                get_msk_time().isoformat(),
                "Нет",
                breast_type if breast_type else "",
                breast_side if breast_side else ""
            ]

            self.feeding_sheet.append_row(feeding_data)

            logger.info(f"Кормление записано пользователем {user_id}, тип: {feeding_type}, количество: {amount}, время: {timestamp}")

            if feeding_type == "breast":
                time_str = timestamp.strftime('%H:%M')
                breast_info = ""
                if breast_type:
                    breast_info = f" ({breast_type}"
                    if breast_side:
                        breast_info += f", {breast_side}"
                    breast_info += ")"
                return f"✅ Грудное кормление записано на {time_str}{breast_info}!"
            else:
                time_str = timestamp.strftime('%H:%M')
                return f"✅ Искусственное кормление записано: {amount} мл на {time_str}"

        except Exception as e:
            logger.error(f"Ошибка при добавлении кормления: {e}")
            return "❌ Ошибка при записи в таблицу"

    def add_weight(self, user_id, weight_grams, note=""):
        """Добавить запись о весе в граммах"""
        try:
            next_id = self.get_next_id(self.weight_sheet)
            now = get_msk_time()

            weight_data = [
                next_id,
                weight_grams,
                user_id,
                now.isoformat(),
                now.isoformat(),
                note
            ]

            self.weight_sheet.append_row(weight_data)

            weight_kg = weight_grams / 1000
            logger.info(f"Вес записан пользователем {user_id}: {weight_grams}г ({weight_kg:.3f}кг)")
            return f"✅ Вес записан: {weight_grams}г ({weight_kg:.3f}кг)"

        except Exception as e:
            logger.error(f"Ошибка при добавлении веса: {e}")
            return "❌ Ошибка при записи в таблицу"

    def get_last_weight(self):
        """Получить последнюю запись о весе"""
        try:
            weight_records = self.weight_sheet.get_all_records()
            if not weight_records:
                return None

            weight_records.sort(key=lambda x: x.get("Временная метка", ""), reverse=True)
            last_record = weight_records[0]

            weight_grams = last_record.get("Вес (г)")
            weight_kg = float(weight_grams) / 1000 if weight_grams else 0

            return {
                'weight_grams': weight_grams,
                'weight_kg': weight_kg,
                'timestamp': last_record.get("Временная метка"),
                'note': last_record.get("Примечание", "")
            }

        except Exception as e:
            logger.error(f"Ошибка при получении последнего веса: {e}")
            return None

    def get_weight_history(self, limit=10):
        """Получить историю веса"""
        try:
            weight_records = self.weight_sheet.get_all_records()
            if not weight_records:
                return []

            weight_records.sort(key=lambda x: x.get("Временная метка", ""), reverse=True)
            return weight_records[:limit]

        except Exception as e:
            logger.error(f"Ошибка при получении истории веса: {e}")
            return []

    def get_last_bottle_feeding_time(self):
        """Получить время последнего искусственного кормления"""
        try:
            feeding_records = self.feeding_sheet.get_all_records()
            bottle_feedings = [r for r in feeding_records if r.get("Тип кормления") == "Искусственное"]

            if not bottle_feedings:
                return None

            bottle_feedings.sort(key=lambda x: x.get("Временная метка", ""), reverse=True)
            last_feeding_time = bottle_feedings[0].get("Временная метка")

            return datetime.fromisoformat(last_feeding_time).replace(tzinfo=MSK_TIMEZONE) if last_feeding_time else None

        except Exception as e:
            logger.error(f"Ошибка при получении времени последнего кормления: {e}")
            return None

    def mark_reminder_sent(self, feeding_id):
        """Пометить, что напоминание отправлено"""
        try:
            feeding_records = self.feeding_sheet.get_all_records()
            for i, record in enumerate(feeding_records, start=2):
                if record.get("ID") == feeding_id:
                    self.feeding_sheet.update_cell(i, 7, "Да")
                    logger.info(f"Напоминание помечено как отправленное для кормления ID: {feeding_id}")
                    break
        except Exception as e:
            logger.error(f"Ошибка при отметке напоминания: {e}")

    def get_stats(self):
        """Получить статистику"""
        try:
            # Статистика сна
            sleep_records = self.sleep_sheet.get_all_records()
            total_sleep_sessions = len(sleep_records)
            completed_sleep_sessions = len([r for r in sleep_records if r.get("Конец сна")])
            active_sleep = any(not r.get("Конец сна") for r in sleep_records)

            # Средняя продолжительность сна
            completed_sessions = [r for r in sleep_records if r.get("Продолжительность (мин)")]
            if completed_sessions:
                avg_duration = sum(r.get("Продолжительность (мин)", 0) for r in completed_sessions) / len(completed_sessions)
                avg_hours = int(avg_duration // 60)
                avg_minutes = int(avg_duration % 60)
                avg_duration_str = f"{avg_hours}ч {avg_minutes}м"
            else:
                avg_duration_str = "нет данных"

            # Статистика кормлений
            feeding_records = self.feeding_sheet.get_all_records()
            total_feedings = len(feeding_records)

            # Сегодняшние кормления
            today = get_msk_time().date()
            today_feedings = 0
            today_bottle_feedings = 0
            total_bottle_amount = 0

            for record in feeding_records:
                feeding_date = datetime.fromisoformat(record.get("Временная метка", "")).date()
                if feeding_date == today:
                    today_feedings += 1
                    if record.get("Тип кормления") == "Искусственное":
                        today_bottle_feedings += 1
                        total_bottle_amount += int(record.get("Количество (мл)", 0))

            # Разделение по типам кормлений
            breast_feedings = len([r for r in feeding_records if r.get("Тип кормления") == "Грудное"])
            bottle_feedings = len([r for r in feeding_records if r.get("Тип кормления") == "Искусственное"])
            total_bottle_all_time = sum(
                int(r.get("Количество (мл)", 0)) for r in feeding_records if r.get("Тип кормления") == "Искусственное")

            # Время последнего искусственного кормления
            last_bottle_time = self.get_last_bottle_feeding_time()
            if last_bottle_time:
                time_since_last_bottle = get_msk_time() - last_bottle_time
                hours = int(time_since_last_bottle.total_seconds() // 3600)
                minutes = int((time_since_last_bottle.total_seconds() % 3600) // 60)
                last_bottle_str = f"{hours}ч {minutes}м назад"
            else:
                last_bottle_str = "еще не было"

            # Статистика веса
            last_weight = self.get_last_weight()
            if last_weight:
                weight_date = datetime.fromisoformat(last_weight['timestamp']).strftime('%d.%m.%Y')
                last_weight_str = f"{last_weight['weight_grams']}г ({last_weight['weight_kg']:.3f}кг) - {weight_date}"
                if last_weight['note']:
                    last_weight_str += f" - {last_weight['note']}"
            else:
                last_weight_str = "нет данных"

            # История веса (последние 5 записей)
            weight_history = self.get_weight_history(limit=5)
            weight_trend = ""
            if len(weight_history) >= 2:
                current_weight = float(weight_history[0].get("Вес (г)", 0))
                previous_weight = float(weight_history[1].get("Вес (г)", 0))
                difference = current_weight - previous_weight
                if difference > 0:
                    weight_trend = f"📈 +{difference}г"
                elif difference < 0:
                    weight_trend = f"📉 {difference}г"
                else:
                    weight_trend = "➡️ без изменений"

            return {
                "total_sleep_sessions": total_sleep_sessions,
                "completed_sleep_sessions": completed_sleep_sessions,
                "active_sleep": active_sleep,
                "avg_duration": avg_duration_str,
                "total_feedings": total_feedings,
                "breast_feedings": breast_feedings,
                "bottle_feedings": bottle_feedings,
                "today_feedings": today_feedings,
                "today_bottle_feedings": today_bottle_feedings,
                "total_bottle_amount": total_bottle_amount,
                "total_bottle_all_time": total_bottle_all_time,
                "last_bottle_feeding": last_bottle_str,
                "last_weight": last_weight_str,
                "weight_trend": weight_trend,
                "weight_records_count": len(weight_history)
            }

        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return {}