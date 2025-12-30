import stripe
import logging
import json
from fastapi import HTTPException
from app.core.config import settings
from app.services.billing_service import billing_service
from app.services.stripe_validator import preflight_check_price
from app.core.subscription_prices import SUBSCRIPTION_PRICES, get_all_price_ids

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY




class StripeService:
    # CREATE CHECKOUT SESSION
    def create_checkout_session(self, price_id, customer_email, user_id, success_url, cancel_url, mode):
        # ========================================
        # 🔍 DEBUG: Log Stripe configuration BEFORE API call
        # ========================================
        logger.info("=" * 80)
        logger.info("[STRIPE CHECKOUT] Creating session")
        logger.info(f"[STRIPE CHECKOUT] Mode: {mode}")
        logger.info(f"[STRIPE CHECKOUT] Price ID: {price_id}")
        logger.info(f"[STRIPE CHECKOUT] Customer Email: {customer_email}")
        logger.info(f"[STRIPE CHECKOUT] User ID: {user_id}")
        logger.info(f"[STRIPE CHECKOUT] Success URL: {success_url}")
        logger.info(f"[STRIPE CHECKOUT] Cancel URL: {cancel_url}")
        logger.info(f"[STRIPE CHECKOUT] Stripe API Key (first 10 chars): {stripe.api_key[:10]}...")
        logger.info(f"[STRIPE CHECKOUT] Stripe API Key Mode: {'TEST' if 'test' in stripe.api_key else 'LIVE'}")
        logger.info("=" * 80)
        
        try:
            # Log subscription price validation for subscription mode
            if mode == "subscription":
                valid_subscription_prices = get_all_price_ids()
                logger.info(f"[STRIPE CHECKOUT] Valid LIVE subscription price IDs: {valid_subscription_prices}")
                logger.info(f"[STRIPE CHECKOUT] Received price_id: {price_id}")
                logger.info(f"[STRIPE CHECKOUT] Price ID validation: {'✅ VALID' if price_id in valid_subscription_prices else '⚠️ NOT IN LIST (will let Stripe validate)'}")
            
            # ========================================
            # PREFLIGHT CHECK: Verify price exists in Stripe
            # ========================================
            logger.info("[STRIPE CHECKOUT] 🔍 Running preflight check...")
            try:
                price_info = preflight_check_price(price_id)
                logger.info(f"[STRIPE CHECKOUT] ✅ Preflight check PASSED")
                logger.info(f"[STRIPE CHECKOUT]   Price Type: {price_info['type']}")
                logger.info(f"[STRIPE CHECKOUT]   Price Active: {price_info['active']}")
                if price_info['recurring']:
                    logger.info(f"[STRIPE CHECKOUT]   Recurring Interval: {price_info['recurring']['interval']}")
            except RuntimeError as e:
                logger.error(f"[STRIPE CHECKOUT] ❌ PREFLIGHT CHECK FAILED: {str(e)}")
                raise HTTPException(400, f"Invalid price ID: {str(e)}")
            
            # ========================================
            # Log exact payload being sent to Stripe
            # ========================================
            payload = {
                "mode": mode,
                "customer_email": customer_email,
                "client_reference_id": user_id,
                "line_items": [{"price": price_id, "quantity": 1}],
                "success_url": success_url,
                "cancel_url": cancel_url,
                "expand": ["line_items"],
            }
            
            logger.info("[STRIPE CHECKOUT] 📦 CHECKOUT PAYLOAD:")
            logger.info(f"[STRIPE CHECKOUT]   mode: {payload['mode']}")
            logger.info(f"[STRIPE CHECKOUT]   line_items: {json.dumps(payload['line_items'])}")
            logger.info(f"[STRIPE CHECKOUT]   customer_email: {payload['customer_email']}")
            logger.info(f"[STRIPE CHECKOUT]   client_reference_id: {payload['client_reference_id']}")
            logger.info(f"[STRIPE CHECKOUT]   success_url: {payload['success_url']}")
            logger.info(f"[STRIPE CHECKOUT]   cancel_url: {payload['cancel_url']}")
            
            # Create Stripe checkout session
            logger.info("[STRIPE CHECKOUT] 🚀 Calling Stripe API: stripe.checkout.Session.create()")
            
            session = stripe.checkout.Session.create(**payload)
            
            logger.info("[STRIPE CHECKOUT] ✅ SUCCESS! Stripe session created")
            logger.info(f"[STRIPE CHECKOUT] Session ID: {session.id}")
            logger.info(f"[STRIPE CHECKOUT] Checkout URL: {session.url}")
            logger.info("=" * 80)

            return {"session_id": session.id, "url": session.url}

        except stripe.error.InvalidRequestError as e:
            # Stripe API errors (invalid price ID, wrong mode, etc.)
            logger.error("=" * 80)
            logger.error("[STRIPE CHECKOUT] ❌ STRIPE INVALID REQUEST ERROR")
            logger.error(f"[STRIPE CHECKOUT] Error Type: InvalidRequestError")
            logger.error(f"[STRIPE CHECKOUT] Error Code: {e.code if hasattr(e, 'code') else 'N/A'}")
            logger.error(f"[STRIPE CHECKOUT] Error Message: {str(e)}")
            logger.error(f"[STRIPE CHECKOUT] Error Param: {e.param if hasattr(e, 'param') else 'N/A'}")
            logger.error(f"[STRIPE CHECKOUT] Full Error: {repr(e)}")
            logger.error(f"[STRIPE CHECKOUT] Price ID attempted: {price_id}")
            logger.error(f"[STRIPE CHECKOUT] Mode attempted: {mode}")
            logger.error("=" * 80)
            # Return full error details to help debug
            error_detail = f"Stripe InvalidRequestError: {str(e)}"
            if hasattr(e, 'code'):
                error_detail = f"[{e.code}] {str(e)}"
            raise HTTPException(400, error_detail)
            
        except stripe.error.AuthenticationError as e:
            # Authentication errors (wrong API key)
            logger.error("=" * 80)
            logger.error("[STRIPE CHECKOUT] ❌ STRIPE AUTHENTICATION ERROR")
            logger.error(f"[STRIPE CHECKOUT] Error Code: {e.code if hasattr(e, 'code') else 'N/A'}")
            logger.error(f"[STRIPE CHECKOUT] Error Message: {str(e)}")
            logger.error(f"[STRIPE CHECKOUT] Full Error: {repr(e)}")
            logger.error(f"[STRIPE CHECKOUT] Check STRIPE_SECRET_KEY in environment")
            logger.error(f"[STRIPE CHECKOUT] API Key Mode: {'TEST' if 'test' in stripe.api_key else 'LIVE'}")
            logger.error(f"[STRIPE CHECKOUT] API Key (first 10 chars): {stripe.api_key[:10]}...")
            logger.error("=" * 80)
            error_detail = f"Stripe AuthenticationError: {str(e)}"
            if hasattr(e, 'code'):
                error_detail = f"[{e.code}] {str(e)}"
            raise HTTPException(401, error_detail)
            
        except stripe.error.StripeError as e:
            # Other Stripe errors
            logger.error("=" * 80)
            logger.error("[STRIPE CHECKOUT] ❌ STRIPE ERROR")
            logger.error(f"[STRIPE CHECKOUT] Error Type: {type(e).__name__}")
            logger.error(f"[STRIPE CHECKOUT] Error Code: {e.code if hasattr(e, 'code') else 'N/A'}")
            logger.error(f"[STRIPE CHECKOUT] Error Message: {str(e)}")
            logger.error(f"[STRIPE CHECKOUT] Full Error: {repr(e)}")
            logger.error(f"[STRIPE CHECKOUT] Price ID attempted: {price_id}")
            logger.error(f"[STRIPE CHECKOUT] Mode attempted: {mode}")
            logger.error("=" * 80)
            error_detail = f"Stripe Error: {str(e)}"
            if hasattr(e, 'code'):
                error_detail = f"[{e.code}] {str(e)}"
            raise HTTPException(500, error_detail)
            
        except HTTPException:
            # Re-raise HTTPException (already handled above)
            raise
            
        except Exception as e:
            # Unexpected errors
            logger.error("=" * 80)
            logger.error("[STRIPE CHECKOUT] ❌ UNEXPECTED ERROR")
            logger.error(f"[STRIPE CHECKOUT] Error Type: {type(e).__name__}")
            logger.error(f"[STRIPE CHECKOUT] Error Message: {str(e)}")
            logger.error(f"[STRIPE CHECKOUT] Full Error: {repr(e)}")
            logger.error(f"[STRIPE CHECKOUT] Price ID attempted: {price_id}")
            logger.error(f"[STRIPE CHECKOUT] Mode attempted: {mode}")
            logger.error("=" * 80)
            raise HTTPException(500, f"Unexpected error: {str(e)}")

    # VALIDATE WEBHOOK SIGNATURE
    def construct_webhook_event(self, payload, signature):
        try:
            return stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=settings.STRIPE_WEBHOOK_SECRET,
            )
        except Exception:
            raise HTTPException(400, "Invalid Stripe webhook signature")

    # CHECKOUT COMPLETED
    def handle_checkout_completed(self, session):
        """Handle successful checkout - route to appropriate service."""
        user_id = session.get("client_reference_id")

        try:
            price_id = session["line_items"]["data"][0]["price"]["id"]
        except Exception:
            logger.error("[STRIPE] Missing line_items in checkout.session.completed")
            return

        # Subscription
        if price_id in SUBSCRIPTION_PRICES:
            billing_service.activate_subscription(user_id, price_id)
            return

        # Credit pack (delegated to CreditService via BillingService)
        billing_service.apply_credit_pack(user_id, price_id)

    # RENEWAL
    def handle_subscription_renewal(self, invoice):
        try:
            price_id = invoice["lines"]["data"][0]["price"]["id"]
        except:
            return

        customer_email = invoice.get("customer_email")

        billing_service.apply_subscription_by_email(customer_email, price_id)


stripe_service = StripeService()
