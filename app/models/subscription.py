from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Subscription(BaseModel):
    """Subscription model"""
    id: str
    user_id: str
    stripe_sub_id: str
    plan: str  # starter, creator, pro
    status: str  # active, canceled, past_due
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SubscriptionCreate(BaseModel):
    """Schema for creating a subscription record"""
    user_id: str
    stripe_sub_id: str
    plan: str
    status: str = "active"
