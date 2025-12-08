from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class User(BaseModel):
    """
    Mock User Model that mimics an ORM for the provided snippets.
    """
    id: str = "mock_user_id"
    email: EmailStr
    credits: int = 0
    
    # Validation / Schema compatible fields
    credits_remaining: int = 0  # Alias for backward compatibility if needed behaviorally

    class Config:
        from_attributes = True

    @classmethod
    def get_by_email(cls, email: str):
        """Mock DB lookup"""
        logger.info(f"[MOCK DB] User.get_by_email({email})")
        # Return a dummy user for the webhook to work on
        return cls(email=email, credits=0, credits_remaining=0)

    def save(self):
        """Mock DB save"""
        logger.info(f"[MOCK DB] User.save() -> ID: {self.id}, Email: {self.email}, Credits: {self.credits}")
        # In a real app, this would update the DB
        return True

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserInDB(User):
    hashed_password: str
