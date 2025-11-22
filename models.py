import json
import pytz
from datetime import datetime, date

from database import db

class Baby:
    @staticmethod
    def create_table():
        query = """
        CREATE TABLE IF NOT EXISTS babies (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            birth_date DATE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        db.execute_query(query)

    @staticmethod
    def add(name, birth_date):
        query = "INSERT INTO babies (name, birth_date) VALUES (%s, %s) RETURNING id"
        result = db.fetch_one(query, (name, birth_date))
        return result['id'] if result else None

    @staticmethod
    def get_all():
        query = "SELECT * FROM babies ORDER BY created_at DESC"
        return db.fetch_all(query)

    @staticmethod
    def get_by_id(baby_id):
        query = "SELECT * FROM babies WHERE id = %s"
        return db.fetch_one(query, (baby_id,))


class Event:
    @staticmethod
    def create_table():
        query = """
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            baby_id INTEGER REFERENCES babies(id) ON DELETE CASCADE,
            event_type VARCHAR(50) NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            amount INTEGER,
            notes TEXT,
            duration INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        db.execute_query(query)

        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_events_baby_id ON events(baby_id)",
            "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_events_baby_timestamp ON events(baby_id, timestamp)"
        ]

        for index_query in indexes:
            db.execute_query(index_query)

    @staticmethod
    def add(baby_id, event_type, amount=None, notes=None, duration=None):
        query = """
        INSERT INTO events (baby_id, event_type, amount, notes, duration)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
        """
        result = db.fetch_one(query, (baby_id, event_type, amount, notes, duration))
        return result['id'] if result else None

    @staticmethod
    def get_today_events(baby_id):
        query = """
        SELECT * FROM events 
        WHERE baby_id = %s AND DATE(timestamp AT TIME ZONE 'UTC') = CURRENT_DATE
        ORDER BY timestamp DESC
        """
        return db.fetch_all(query, (baby_id,))

    @staticmethod
    def get_stats(baby_id, days=7):
        query = """
        SELECT 
            event_type,
            COUNT(*) as count,
            AVG(amount) as avg_amount,
            AVG(duration) as avg_duration
        FROM events 
        WHERE baby_id = %s AND timestamp >= CURRENT_DATE - INTERVAL '%s days'
        GROUP BY event_type
        """
        return db.fetch_all(query, (baby_id, days))


class UserState:
    @staticmethod
    def create_table():
        query = """
        CREATE TABLE IF NOT EXISTS user_states (
            user_id BIGINT PRIMARY KEY,
            state VARCHAR(100),
            data JSONB,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        db.execute_query(query)

    @staticmethod
    def set_state(user_id, state, data=None):
        # Сериализуем словарь в JSON строку
        json_data = json.dumps(data) if data is not None else None

        query = """
        INSERT INTO user_states (user_id, state, data)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) 
        DO UPDATE SET state = EXCLUDED.state, data = EXCLUDED.data, updated_at = CURRENT_TIMESTAMP
        """
        db.execute_query(query, (user_id, state, json_data))

    @staticmethod
    def get_state(user_id):
        query = "SELECT state, data FROM user_states WHERE user_id = %s"
        result = db.fetch_one(query, (user_id,))

        if result and result['data']:
            # Десериализуем JSON строку обратно в словарь
            try:
                data_dict = json.loads(result['data'])
                return {'state': result['state'], 'data': data_dict}
            except (json.JSONDecodeError, TypeError):
                return {'state': result['state'], 'data': {}}
        elif result:
            return {'state': result['state'], 'data': {}}
        return None

    @staticmethod
    def clear_state(user_id):
        query = "DELETE FROM user_states WHERE user_id = %s"
        db.execute_query(query, (user_id,))


def init_database():
    """Initialize all database tables"""
    Baby.create_table()
    Event.create_table()
    UserState.create_table()