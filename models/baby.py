from services.database import db


class Baby:
    @staticmethod
    def create_table():
        query = """
        CREATE TABLE IF NOT EXISTS babies (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            birth_date DATE NOT NULL,
            gender VARCHAR(10) NOT NULL DEFAULT 'unknown',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        db.execute_query(query)

    @staticmethod
    def add(name, birth_date, gender='unknown'):
        query = "INSERT INTO babies (name, birth_date, gender) VALUES (%s, %s, %s) RETURNING id"
        result = db.fetch_one(query, (name, birth_date, gender))
        return result['id'] if result else None

    @staticmethod
    def get_all():
        query = "SELECT * FROM babies ORDER BY created_at DESC"
        return db.fetch_all(query)

    @staticmethod
    def get_by_id(baby_id):
        query = "SELECT * FROM babies WHERE id = %s"
        return db.fetch_one(query, (baby_id,))

    @staticmethod
    def get_current():
        # For now, assume one baby. Can be extended for multiple babies
        babies = Baby.get_all()
        return babies[0] if babies else None

    @staticmethod
    def update_gender(baby_id, gender):
        query = "UPDATE babies SET gender = %s WHERE id = %s"
        db.execute_query(query, (gender, baby_id))