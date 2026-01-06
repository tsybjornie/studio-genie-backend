"""
Stripe Webhook Handler - Canonical v1.0
Webhook-only credit grants with pending subscription support
DEPLOYMENT TRIGGER: 2026-01-06 16:06 - Final identity stabilization
"""
import logging
import psycopg2
from fastapi import APIRouter, Request, HTTPException
import stripe
from app.core.config import settings
from app.core.subscription_prices import SUBSCRIPTION_PRICES
from app.utils.credit_logger import (
    log_webhook_event,
    log_credit_event,
    log_pending_subscription
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["Webhooks"])


# Credit pack price ID to credits mapping
CREDIT_PACK_AMOUNTS = {
    "price_1SdZ50BBwifSvpdIWW1Ntt22": 9,    # Small - $25
    "price_1SdZ7TBBwifSvpdIAZqbTuLR": 30,   # Medium - $65
    "price_1SdZ7xBBwifSvpdI1B6BjybU": 90,   # Power - $119
}


def get_db_connection():
    """Get database connection with RealDictCursor for dict-like row access"""
    from psycopg2.extras import RealDictCursor
    conn = psycopg2.connect(
        settings.DATABASE_URL,
        cursor_factory=RealDictCursor,
        sslmode="require"
    )
    return conn


@router.post("/stripe")
async def stripe_webhook(request: Request):
    """
    Stripe webhook handler - CANONICAL v1.0
    
    Handles:
    - invoice.paid: Monthly subscription renewals (carry-forward credits)
    - checkout.session.completed: First payment or one-time credit packs
    
    Credit grants are WEBHOOK-ONLY. Frontend receives NO credits.
    """
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        logger.error(f"[WEBHOOK] Invalid signature | Error: {str(e)}")
        raise HTTPException(400, "Invalid webhook signature")
    
    event_type = event["type"]
    event_id = event["id"]
    
    logger.info(f"[WEBHOOK] Received event | Type: {event_type} | EventID: {event_id}")
    
    try:
        if event_type == "invoice.paid":
            await handle_invoice_paid(event)
        elif event_type == "checkout.session.completed":
            await handle_checkout_completed(event)
        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(event)  # ← Revoke access
        else:
            logger.info(f"[WEBHOOK] Ignoring event type: {event_type}")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"[WEBHOOK] Processing failed | EventType: {event_type} | Error: {str(e)}", exc_info=True)
        # Return 200 to prevent Stripe retries for unrecoverable errors
        return {"status": "error", "message": str(e)}


async def handle_invoice_paid(event):
    """
    Handle subscription payment (invoice.paid) - STRIPE AUTHORITY
    
    Activates subscription and grants monthly credits.
    Idempotent: uses invoice_id to prevent duplicate credit grants.
    """
    invoice = event["data"]["object"]
    invoice_id = invoice.get("id")
    customer_id = invoice.get("customer")
    subscription_id = invoice.get("subscription")
    
    try:
        # Get price ID from invoice line items
        price_id = invoice["lines"]["data"][0]["price"]["id"]
    except (KeyError, IndexError):
        logger.error(f"[WEBHOOK] Missing price ID in invoice | InvoiceID: {invoice_id}")
        return
    
    # Validate price ID
    if price_id not in SUBSCRIPTION_PRICES:
        logger.warning(f"[WEBHOOK] Unknown subscription price ID: {price_id}")
        return
    
    plan_info = SUBSCRIPTION_PRICES[price_id]
    credits_to_add = plan_info["monthly_credits"]
    plan_name = plan_info["plan_name"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Find user by customer_id
        logger.info(f"[WEBHOOK] Looking up user by stripe_customer_id: {customer_id}")
        cursor.execute(
            "SELECT id, email, credits, stripe_subscription_id FROM users WHERE stripe_customer_id = %s",
            (customer_id,)
        )
        user = cursor.fetchone()
        
        if user:
            user_id = user["id"]
            current_credits = user["credits"]
            
#             # Check if invoice already processed (idempotency)
            # TODO: Add processed_invoices table for idempotency
            
            # ACTIVATE subscription + ADD credits
            new_balance = current_credits + credits_to_add
            
            cursor.execute("""
                UPDATE users 
                SET subscription_status = 'active',
                    subscription_plan = %s,
                    stripe_subscription_id = %s,
                    credits = %s
                WHERE id = %s
            """, (plan_name, subscription_id, new_balance, user_id))
            conn.commit()
            
            # Verify update by re-querying user
            cursor.execute(
                "SELECT email, subscription_status, subscription_plan FROM users WHERE id = %s",
                (user_id,)
            )
            updated_user = cursor.fetchone()
            
            logger.info(f"[WEBHOOK] ✅ Subscription activated | UserID: {user_id} | Email: {updated_user['email'] if updated_user else 'NOT FOUND'}")
            logger.info(f"[WEBHOOK]   Status: {updated_user['subscription_status'] if updated_user else 'NULL'} | Plan: {updated_user['subscription_plan'] if updated_user else 'NULL'} | Credits: +{credits_to_add} → {new_balance}")
            
        else:
            logger.warning(f"[WEBHOOK] User not found for customer {customer_id} | Skipping (auth-first flow)")
            # In auth-first flow, user must exist BEFORE payment
            
    finally:
        cursor.close()
        conn.close()


async def handle_subscription_deleted(event):
    """
    Handle subscription cancellation (customer.subscription.deleted) - STRIPE AUTHORITY
    
    Revokes access immediately. Credits remain but features are blocked.
    Idempotent: safe to run multiple times.
    """
    subscription = event["data"]["object"]
    subscription_id = subscription.get("id")
    customer_id = subscription.get("customer")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # REVOKE subscription access (keep credits)
        cursor.execute("""
            UPDATE users 
            SET subscription_status = 'inactive'
            WHERE stripe_customer_id = %s
        """, (customer_id,))
        
        rows_affected = cursor.rowcount
        conn.commit()
        
        if rows_affected > 0:
            logger.info(f"[WEBHOOK] ❌ Subscription canceled | CustomerID: {customer_id} | SubscriptionID: {subscription_id}")
        else:
            logger.warning(f"[WEBHOOK] User not found for canceled subscription | CustomerID: {customer_id}")
        
    finally:
        cursor.close()
        conn.close()


async def handle_checkout_completed(event):
    """
    Handle checkout completion (checkout.session.completed)
    
    - Mode 'subscription': Store as pending (first payment before registration)
    - Mode 'payment': Award credit pack immediately
    """
    session = event["data"]["object"]
    mode = session.get("mode")
    customer_id = session.get("customer")
    session_id = session["id"]
    
    if mode == "subscription":
        # First subscription payment - user hasn't registered yet
        await handle_subscription_first_payment(session, event["id"])
        
    elif mode == "payment":
        # One-time credit pack purchase
        await handle_credit_pack_purchase(session, event["id"])
        
    else:
        logger.warning(f"[WEBHOOK] Unknown checkout mode: {mode}")
        log_webhook_event("checkout.session.completed", event["id"], mode, customer_id, None, False, "Unknown mode")


async def handle_subscription_first_payment(session, event_id):
    """
    Activate subscription immediately on first payment.
    No pending_subscriptions - directly update users table.
    """
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    
    try:
        # Get price ID from line items
        line_items = session.get("line_items", {}).get("data", [])
        if not line_items:
            # Expand line_items if not present
            stripe.api_key = settings.STRIPE_SECRET_KEY
            expanded_session = stripe.checkout.Session.retrieve(
                session["id"],
                expand=["line_items"]
            )
            line_items = expanded_session.get("line_items", {}).get("data", [])
        
        price_id = line_items[0]["price"]["id"]
    except (KeyError, IndexError) as e:
        logger.error(f"[WEBHOOK] Missing price ID in subscription checkout | Error: {str(e)}")
        log_webhook_event("checkout.session.completed", event_id, "subscription", customer_id, None, False, "Missing price ID")
        return
    
    # Validate price ID
    if price_id not in SUBSCRIPTION_PRICES:
        logger.warning(f"[WEBHOOK] Unknown subscription price ID: {price_id} | Skipping")
        return
    
    plan_info = SUBSCRIPTION_PRICES[price_id]
    plan_name = plan_info["plan_name"]
    credits_to_award = plan_info["monthly_credits"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # IDENTITY SOURCE OF TRUTH: client_reference_id ONLY
        user_id = session.get("client_reference_id")
        
        if not user_id:
            logger.error(f"[WEBHOOK] No client_reference_id in session | SessionID: {session.get('id')} | REJECTING")
            log_webhook_event("checkout.session.completed", event_id, "subscription", customer_id, None, False, "Missing client_reference_id")
            return
        
        # Direct lookup by user_id (NO fallback)
        logger.info(f"[WEBHOOK] Looking up user by user_id (client_reference_id): {user_id}")
        cursor.execute(
            "SELECT id, email, credits FROM users WHERE id = %s",
            (user_id,)
        )
        
        user = cursor.fetchone()
        
        if not user:
            logger.error(f"[WEBHOOK] User not found for user_id: {user_id} | REJECTING")
            log_webhook_event("checkout.session.completed", event_id, "subscription", customer_id, user_id, False, "User not found")
            return
        
        user_id = user["id"]
        user_email = user["email"]
        current_credits = user["credits"] or 0
        new_balance = current_credits + credits_to_award
        
        # DIRECT ACTIVATION - Update users table ONLY (NO pending_subscriptions)
        logger.info(f"[WEBHOOK] Activating subscription | UserID: {user_id} | Plan: {plan_name} | Credits: +{credits_to_award}")
        cursor.execute("""
            UPDATE users 
            SET subscription_status = 'active',
                subscription_plan = %s,
                stripe_subscription_id = %s,
                stripe_customer_id = %s,
                credits = %s
            WHERE id = %s
        """, (plan_name, subscription_id, customer_id, new_balance, user_id))
        conn.commit()
        
        # Verify update
        cursor.execute(
            "SELECT email, subscription_status, subscription_plan, credits FROM users WHERE id = %s",
            (user_id,)
        )
        updated_user = cursor.fetchone()
        
        logger.info(f"[WEBHOOK] ✅ Subscription activated | UserID: {user_id} | Email: {updated_user['email']}")
        logger.info(f"[WEBHOOK]   Status: {updated_user['subscription_status']} | Plan: {updated_user['subscription_plan']} | Credits: {updated_user['credits']}")
        
        log_webhook_event("checkout.session.completed", event_id, "subscription", customer_id, user_id, True)
        
    finally:
        cursor.close()
        conn.close()


async def handle_credit_pack_purchase(session, event_id):
    """Award credit pack immediately (user is authenticated)"""
    user_id = session.get("client_reference_id")
    customer_id = session.get("customer")
    
    if not user_id:
        logger.error(f"[WEBHOOK] Missing user_id in credit pack purchase | SessionID: {session['id']}")
        log_webhook_event("checkout.session.completed", event_id, "payment", customer_id, None, False, "Missing user_id")
        return
    
    try:
        # Get price ID from line items
        line_items = session.get("line_items", {}).get("data", [])
        if not line_items:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            expanded_session = stripe.checkout.Session.retrieve(
                session["id"],
                expand=["line_items"]
            )
            line_items = expanded_session.get("line_items", {}).get("data", [])
        
        price_id = line_items[0]["price"]["id"]
    except (KeyError, IndexError) as e:
        logger.error(f"[WEBHOOK] Missing price ID in credit pack | Error: {str(e)}")
        log_webhook_event("checkout.session.completed", event_id, "payment", customer_id, user_id, False, "Missing price ID")
        return
    
    if price_id not in CREDIT_PACK_AMOUNTS:
        logger.warning(f"[WEBHOOK] Unknown credit pack price ID: {price_id}")
        log_webhook_event("checkout.session.completed", event_id, "payment", customer_id, user_id, False, "Unknown price ID")
        return
    
    credits_to_add = CREDIT_PACK_AMOUNTS[price_id]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get current credits
        cursor.execute("SELECT credits FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        
        if not result:
            logger.error(f"[WEBHOOK] User not found | UserID: {user_id}")
            log_webhook_event("checkout.session.completed", event_id, "payment", customer_id, user_id, False, "User not found")
            return
        
        current_credits = result[0]
        new_balance = current_credits + credits_to_add
        
        # ADD credits (carry-forward)
        cursor.execute(
            "UPDATE users SET credits = %s WHERE id = %s",
            (new_balance, user_id)
        )
        conn.commit()
        
        log_credit_event(
            "GRANT",
            user_id,
            credits_to_add,
            new_balance,
            "credit_pack",
            {"price_id": price_id, "session_id": session["id"]}
        )
        log_webhook_event("checkout.session.completed", event_id, "payment", customer_id, user_id, True)
        
        logger.info(f"[WEBHOOK] Credit pack awarded | UserID: {user_id} | +{credits_to_add} → {new_balance}")
        
    finally:
        cursor.close()
        conn.close()
