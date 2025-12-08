# Stub user service
import logging

logger = logging.getLogger(__name__)

async def get_user_by_stripe_customer_id(customer_id: str):
    logger.info(f"[USER SERVICE] Mock fetch user by strip_id: {customer_id}")
    # Return a mock user object/dict that behaves like the system expects
    return {"id": "mock_user_id", "email": "mock@example.com", "credits_remaining": 0}
