from services.database import db
from datetime import datetime
import pytz
from config import TIMEZONE


class Reminder:
    @staticmethod
    def create_table():
        query = """
        CREATE TABLE IF NOT EXISTS reminders (
            id SERIAL PRIMARY KEY,
            baby_id INTEGER NOT NULL,
            reminder_type VARCHAR(50) NOT NULL,
            scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
            sent BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        db.execute_query(query)

        # Create index for performance
        db.execute_query(
            "CREATE INDEX IF NOT EXISTS idx_reminders_scheduled ON reminders(scheduled_time, sent)"
        )

    @staticmethod
    def add(baby_id, reminder_type, scheduled_time):
        query = """
        INSERT INTO reminders (baby_id, reminder_type, scheduled_time)
        VALUES (%s, %s, %s) RETURNING id
        """
        result = db.fetch_one(query, (baby_id, reminder_type, scheduled_time))
        return result['id'] if result else None

    @staticmethod
    def get_pending_reminders():
        """Get reminders that are due and not sent"""
        query = """
        SELECT * FROM reminders 
        WHERE scheduled_time <= NOW() AND sent = FALSE
        ORDER BY scheduled_time ASC
        """
        return db.fetch_all(query)

    @staticmethod
    def mark_as_sent(reminder_id):
        query = "UPDATE reminders SET sent = TRUE WHERE id = %s"
        db.execute_query(query, (reminder_id,))

    @staticmethod
    def delete_old_reminders(days=7):
        """Delete old sent reminders"""
        query = "DELETE FROM reminders WHERE sent = TRUE AND created_at < NOW() - INTERVAL '%s days'"
        db.execute_query(query, (days,))