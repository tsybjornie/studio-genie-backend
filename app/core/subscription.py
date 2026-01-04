"""
Subscription Middleware - Centralized subscription gating
Enforces active subscription requirement for paid features
"""
from fastapi import HTTPException, Depends
from app.core.security import get_current_user
from app.core.database import get_connection
import logging

logger = logging.getLogger(__name__)


def require_active_subscription(current_user: dict = Depends(get_current_user)):
    """
    Subscription gate middleware.
    
    Checks if authenticated user has active subscription.
    Returns 403 if subscription is not active.
    
    Usage:
        @router.get("/api/protected")
        async def protected_route(user=Depends(require_active_subscription)):
            # Only users with active subscription reach here
    
    Args:
        current_user: Authenticated user from JWT token
        
    Returns:
        dict: Current user info if subscription is active
        
    Raises:
        HTTPException: 403 if no active subscription
    """
    user_id = current_user["user_id"]
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            "SELECT has_active_subscription FROM users WHERE id = %s",
            (user_id,)
        )
        user = cur.fetchone()
        
        if not user:
            logger.error(f"[SUBSCRIPTION GATE] User {user_id} not found in database")
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user["has_active_subscription"]:
            logger.warning(f"[SUBSCRIPTION GATE] Access denied for user {user_id} - no active subscription")
            raise HTTPException(
                status_code=403,
                detail="Active subscription required. Subscribe at /pricing"
            )
        
        logger.info(f"[SUBSCRIPTION GATE] Access granted for user {user_id}")
        return current_user
        
    finally:
        cur.close()
        conn.close()
