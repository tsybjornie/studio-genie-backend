from supabase import create_client, Client
from app.core.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Wrapper for Supabase client."""

    def __init__(self):
        self._anon: Optional[Client] = None
        self._service: Optional[Client] = None

    @property
    def client(self) -> Client:
        """Anon client"""
        if not self._anon:
            self._anon = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
        return self._anon

    @property
    def service_client(self) -> Client:
        """Service role client"""
        if not self._service:
            self._service = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        return self._service

    # Utility method: safe select
    def get_user_by_email(self, email: str):
        response = self.service_client.table("users").select("*").eq("email", email).execute()
        return response.data

    # Utility method: safe insert
    def insert_user(self, user_data: dict):
        response = self.service_client.table("users").insert(user_data).execute()
        return response.data


# Global instance
db = SupabaseClient()


def get_db():
    return db
