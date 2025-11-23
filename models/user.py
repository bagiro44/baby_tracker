import json
from services.database import db


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
            try:
                data_dict = json.loads(result['data'])
                return {'state': result['state'], 'data': data_dict}
            except (json.JSONDecodeError, TypeError):
                return {'state': result['state'], 'data': result['data']}
        elif result:
            return {'state': result['state'], 'data': {}}
        return None

    @staticmethod
    def clear_state(user_id):
        query = "DELETE FROM user_states WHERE user_id = %s"
        db.execute_query(query, (user_id,))