from fastapi import APIRouter, HTTPException, Depends
from app.core.security import get_current_user
from app.core.database import get_db, SupabaseClient
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("")
async def get_user_subscriptions(
    current_user: dict = Depends(get_current_user),
    db: SupabaseClient = Depends(get_db)
):
    """
    Get user's subscriptions
    
    Returns all subscriptions associated with the user.
    """
    try:
        response = db.service_client.table('subscriptions').select('*').eq(
            'user_id', current_user['id']
        ).order('created_at', desc=True).execute()
        
        return response.data
    
    except Exception as e:
        logger.error(f"Error fetching subscriptions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch subscriptions")


@router.get("/{subscription_id}")
async def get_subscription(
    subscription_id: str,
    current_user: dict = Depends(get_current_user),
    db: SupabaseClient = Depends(get_db)
):
    """
    Get subscription details
    
    Returns detailed information about a specific subscription.
    """
    try:
        response = db.service_client.table('subscriptions').select('*').eq(
            'id', subscription_id
        ).eq('user_id', current_user['id']).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        return response.data[0]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch subscription")
