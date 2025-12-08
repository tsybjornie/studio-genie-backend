import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class MockTable:
    def __init__(self, table_name):
        self.table_name = table_name

    def select(self, *args, **kwargs):
        return self

    def insert(self, *args, **kwargs):
        return self

    def update(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def single(self):
        return self

    def execute(self):
        logger.info(f"[DB MOCK] Executed query on table '{self.table_name}'")
        # Return a mock response object with .data
        class MockResponse:
            data = {"id": "mock_id", "email": "mock@example.com", "credits_remaining": 100}
        return MockResponse()

class MockClient:
    def table(self, name: str):
        return MockTable(name)

class Database:
    """
    Placeholder for Custom Database Layer.
    Currently mocks Supabase-style calls to prevent runtime errors during migration.
    """
    def __init__(self):
        logger.info(f"Initializing Custom Database with URL: {settings.DATABASE_URL}")
        self.client = MockClient()
        self.service_client = MockClient()

# Global instance
db = Database()

def get_db():
    return db
