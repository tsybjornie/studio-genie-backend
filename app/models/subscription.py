from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Subscription(BaseModel):
    """
    Mock Subscription Model
    """
    id: str = "mock_sub_id"
    user_id: str
    stripe_subscription_id: str
    stripe_item_id: str = "mock_item_id"
    plan: str
    price_id: str
    status: str = "active"
    created_at: datetime = datetime.utcnow()
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def get_by_user_id(cls, user_id: str):
        """Mock DB lookup by user_id"""
        logger.info(f"[MOCK DB] Subscription.get_by_user_id({user_id})")
        # Return a dummy subscription
        return cls(
            user_id=user_id, 
            stripe_subscription_id="sub_mock_123",
            price_id="price_mock_starter", 
            plan="starter"
        )
    
    @classmethod
    def get(cls, sub_id: str):
        """Mock DB lookup by ID"""
        logger.info(f"[MOCK DB] Subscription.get({sub_id})")
        return cls(
            user_id="mock_user_id",
            stripe_subscription_id="sub_mock_123",
            price_id="price_mock_starter",
            plan="starter"
        )

    def save(self):
        """Mock DB save"""
        logger.info(f"[MOCK DB] Subscription.save() -> ID: {self.id}, Plan: {self.plan}, Price: {self.price_id}")
        return True

class SubscriptionCreate(BaseModel):
    user_id: str
    stripe_subscription_id: str
    plan: str
    status: str = "active"
