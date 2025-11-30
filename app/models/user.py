from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class User(BaseModel):
    """User model"""
    id: str
    email: EmailStr
    has_trial_used: bool = False
    credits_remaining: int = 0
    plan: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    email: EmailStr
    password: str


class UserInDB(User):
    """User model with hashed password"""
    hashed_password: str
