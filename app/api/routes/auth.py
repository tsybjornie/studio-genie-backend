from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.core.database import get_connection
from app.core.security import hash_password, verify_password, create_access_token
import traceback
import logging

logging.basicConfig(level=logging.INFO)

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(data: RegisterRequest, session_id: str = None):
    """
    Register new user - Canonical v1.0
    
    If session_id provided (from Stripe redirect):
    - Retrieve Stripe session
    - Link customer_id to user
    - Check for pending subscription
    - Award initial credits if subscription exists
    """
    try:
        from datetime import datetime
        import stripe
        from app.core.config import settings
        from app.utils.credit_logger import log_credit_event, log_pending_subscription
        
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe_customer_id = None
        
        # If session_id provided, retrieve Stripe session
        if session_id:
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                stripe_customer_id = session.get("customer")
                logging.info(f"[REGISTER] Stripe session found | SessionID: {session_id} | CustomerID: {stripe_customer_id}")
            except Exception as e:
                logging.warning(f"[REGISTER] Failed to retrieve Stripe session | Error: {str(e)}")

        hashed_password = hash_password(data.password)

        conn = get_connection()
        cur = conn.cursor()

        # Create user with Stripe customer ID if available
        cur.execute(
            """
            INSERT INTO users (email, password_hash, credits, stripe_customer_id, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (data.email, hashed_password, 0, stripe_customer_id, datetime.utcnow())
        )

        user_id = cur.fetchone()["id"]
        
        # Check for pending subscription
        if stripe_customer_id:
            cur.execute(
                """
                SELECT id, credits_to_award, plan_name, stripe_subscription_id
                FROM pending_subscriptions
                WHERE stripe_customer_id = %s AND claimed_at IS NULL
                """,
                (stripe_customer_id,)
            )
            pending_sub = cur.fetchone()
            
            if pending_sub:
                # Award pending credits
                credits_to_award = pending_sub["credits_to_award"]
                plan_name = pending_sub["plan_name"]
                subscription_id = pending_sub["stripe_subscription_id"]
                
                cur.execute(
                    "UPDATE users SET credits = %s WHERE id = %s",
                    (credits_to_award, user_id)
                )
                
                # Mark pending subscription as claimed
                cur.execute(
                    """
                    UPDATE pending_subscriptions 
                    SET claimed_at = NOW(), claimed_by_user_id = %s
                    WHERE id = %s
                    """,
                    (user_id, pending_sub["id"])
                )
                
                log_credit_event(
                    "GRANT",
                    user_id,
                    credits_to_award,
                    credits_to_award,
                    "subscription",
                    {"plan": plan_name, "subscription_id": subscription_id, "source": "pending_claim"}
                )
                log_pending_subscription("CLAIMED", stripe_customer_id, subscription_id, plan_name, credits_to_award, user_id)
                
                logging.info(f"[REGISTER] Pending subscription claimed | UserID: {user_id} | Credits: {credits_to_award}")
        
        conn.commit()
        cur.close()
        conn.close()

        token = create_access_token({"user_id": user_id, "email": data.email})
        return {"access_token": token, "token_type": "bearer"}

    except Exception as e:
        logging.error("REGISTER ERROR")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
def login(data: LoginRequest):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, email, password_hash FROM users WHERE email = %s",
            (data.email,)
        )
        user = cur.fetchone()

        if not user:
            cur.close()
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not verify_password(data.password, user["password_hash"]):
            cur.close()
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid credentials")

        cur.close()
        conn.close()

        token = create_access_token({"user_id": user["id"], "email": user["email"]})
        return {"access_token": token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error("LOGIN ERROR")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
