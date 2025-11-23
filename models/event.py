from services.database import db
from datetime import datetime
import pytz
from config import TIMEZONE


class Event:
    # Event types
    SLEEP_START = 'sleep_start'
    SLEEP_END = 'sleep_end'
    BREAST_FEEDING_START = 'breast_feeding_start'
    BREAST_FEEDING_END = 'breast_feeding_end'
    BOTTLE_FEEDING = 'bottle_feeding'
    WEIGHT = 'weight'
    DIAPER = 'diaper'

    @staticmethod
    def create_table():
        query = """
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            baby_id INTEGER NOT NULL,
            event_type VARCHAR(50) NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            amount INTEGER,
            notes TEXT,
            duration INTEGER,
            created_by BIGINT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        db.execute_query(query)

        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_events_baby_id ON events(baby_id)",
            "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_events_baby_type ON events(baby_id, event_type)"
        ]
        for index_query in indexes:
            db.execute_query(index_query)

    @staticmethod
    def add(baby_id, event_type, created_by, amount=None, notes=None, duration=None, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now(pytz.timezone(TIMEZONE))

        query = """
        INSERT INTO events (baby_id, event_type, timestamp, amount, notes, duration, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """
        result = db.fetch_one(query, (baby_id, event_type, timestamp, amount, notes, duration, created_by))
        return result['id'] if result else None

    @staticmethod
    def get_last_by_type(baby_id, event_type):
        query = """
        SELECT * FROM events 
        WHERE baby_id = %s AND event_type = %s 
        ORDER BY timestamp DESC 
        LIMIT 1
        """
        return db.fetch_one(query, (baby_id, event_type))

    @staticmethod
    def get_events_by_period(baby_id, event_type, hours=24):
        query = """
        SELECT * FROM events 
        WHERE baby_id = %s AND event_type = %s 
        AND timestamp >= NOW() - INTERVAL '%s hours'
        ORDER BY timestamp DESC
        """
        return db.fetch_all(query, (baby_id, event_type, hours))

    @staticmethod
    def get_active_sleep(baby_id):
        """Get active sleep session (started but not ended)"""
        query = """
        SELECT * FROM events 
        WHERE baby_id = %s AND event_type = %s 
        AND NOT EXISTS (
            SELECT 1 FROM events e2 
            WHERE e2.baby_id = events.baby_id 
            AND e2.event_type = %s 
            AND e2.timestamp > events.timestamp
        )
        ORDER BY timestamp DESC 
        LIMIT 1
        """
        return db.fetch_one(query, (baby_id, Event.SLEEP_START, Event.SLEEP_END))

    @staticmethod
    def get_active_breast_feeding(baby_id):
        """Get active breast feeding session"""
        query = """
        SELECT * FROM events 
        WHERE baby_id = %s AND event_type = %s 
        AND NOT EXISTS (
            SELECT 1 FROM events e2 
            WHERE e2.baby_id = events.baby_id 
            AND e2.event_type = %s 
            AND e2.timestamp > events.timestamp
        )
        ORDER BY timestamp DESC 
        LIMIT 1
        """
        return db.fetch_one(query, (baby_id, Event.BREAST_FEEDING_START, Event.BREAST_FEEDING_END))