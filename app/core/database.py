import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        if not settings.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set")

        self.conn = psycopg2.connect(
            settings.DATABASE_URL,
            cursor_factory=RealDictCursor,
            sslmode="require"
        )
        self.conn.autocommit = True
        logger.info("✅ Connected to Render PostgreSQL")

    def fetch_one(self, query: str, params: tuple = ()):
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()

    def fetch_all(self, query: str, params: tuple = ()):
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def execute(self, query: str, params: tuple = ()):
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.rowcount


# Global DB instance
db = Database()


def get_db():
    """Returns the global database instance"""
    return db
