"""
Credit Logger Utility - Canonical v1.0
Explicit logging for all credit mutations
"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def log_credit_event(
    event_type: str,
    user_id: Optional[str],
    delta: int,
    new_balance: int,
    source: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log credit mutations with full context.
    
    Args:
        event_type: "GRANT", "DEDUCT", "WEBHOOK", "PENDING"
        user_id: User UUID (None for pending subscriptions)
        delta: Credit change amount (positive or negative)
        new_balance: Total credits after mutation
        source: "subscription", "credit_pack", "video_gen", "manual"
        metadata: Additional context (session_id, price_id, etc.)
    """
    user_display = user_id if user_id else "PENDING"
    meta_display = metadata if metadata else {}
    
    logger.info(
        f"[CREDITS] {event_type} | "
        f"User: {user_display} | "
        f"Δ{delta:+d} → Balance: {new_balance} | "
        f"Source: {source} | "
        f"Meta: {meta_display}"
    )


def log_checkout_event(
    checkout_type: str,
    user_id: Optional[str],
    price_id: str,
    session_id: str,
    success: bool,
    error: Optional[str] = None
):
    """
    Log checkout session creation.
    
    Args:
        checkout_type: "subscription" or "credit_pack"
        user_id: User UUID (None for subscription)
        price_id: Stripe price ID
        session_id: Stripe session ID
        success: Whether creation succeeded
        error: Error message if failed
    """
    status = "SUCCESS" if success else "FAILED"
    user_display = user_id if user_id else "UNAUTHENTICATED"
    
    logger.info(
        f"[CHECKOUT] {status} | "
        f"Type: {checkout_type} | "
        f"User: {user_display} | "
        f"PriceID: {price_id} | "
        f"SessionID: {session_id} | "
        f"Error: {error or 'None'}"
    )


def log_webhook_event(
    event_type: str,
    stripe_event_id: str,
    mode: Optional[str],
    customer_id: Optional[str],
    user_id: Optional[str],
    success: bool,
    error: Optional[str] = None
):
    """
    Log Stripe webhook processing.
    
    Args:
        event_type: "invoice.paid", "checkout.session.completed", etc.
        stripe_event_id: Stripe event ID
        mode: "subscription" or "payment" (for checkout.session.completed)
        customer_id: Stripe customer ID
        user_id: User UUID (if found)
        success: Whether processing succeeded
        error: Error message if failed
    """
    status = "SUCCESS" if success else "FAILED"
    user_display = user_id if user_id else "NOT_FOUND"
    
    logger.info(
        f"[WEBHOOK] {status} | "
        f"Event: {event_type} | "
        f"EventID: {stripe_event_id} | "
        f"Mode: {mode or 'N/A'} | "
        f"CustomerID: {customer_id} | "
        f"UserID: {user_display} | "
        f"Error: {error or 'None'}"
    )


def log_pending_subscription(
    action: str,
    customer_id: str,
    subscription_id: Optional[str],
    plan_name: str,
    credits: int,
    user_id: Optional[str] = None
):
    """
    Log pending subscription operations.
    
    Args:
        action: "CREATED", "CLAIMED", "EXPIRED"
        customer_id: Stripe customer ID
        subscription_id: Stripe subscription ID
        plan_name: Subscription plan name
        credits: Credits to award
        user_id: User UUID (for CLAIMED action)
    """
    user_display = user_id if user_id else "PENDING_REGISTRATION"
    
    logger.info(
        f"[PENDING_SUB] {action} | "
        f"CustomerID: {customer_id} | "
        f"SubscriptionID: {subscription_id} | "
        f"Plan: {plan_name} | "
        f"Credits: {credits} | "
        f"ClaimedBy: {user_display}"
    )
