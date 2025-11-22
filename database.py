import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from config import DB_CONFIG
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.db_config = DB_CONFIG
        # self.db_config.update({
        #     'sslmode': 'verify-full',
        #     'sslrootcert': 'root.crt'  # убедитесь что файл существует
        # })

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = psycopg2.connect(
                **self.db_config,
                cursor_factory=psycopg2.extras.DictCursor
            )
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    @contextmanager
    def get_cursor(self, conn):
        cur = None
        try:
            cur = conn.cursor()
            yield cur
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database cursor error: {e}")
            raise
        finally:
            if cur:
                cur.close()

    def execute_query(self, query, params=None):
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(query, params)
                return cur.rowcount

    def fetch_one(self, query, params=None):
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(query, params)
                return cur.fetchone()

    def fetch_all(self, query, params=None):
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(query, params)
                return cur.fetchall()


# Initialize database
db = Database()