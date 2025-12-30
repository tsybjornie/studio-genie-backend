"""
Stripe Price Validator - Startup Validation
Validates all subscription prices on application startup
"""
import stripe
import logging
from app.core.config import settings
from app.core.subscription_prices import SUBSCRIPTION_PRICES, get_all_price_ids

logger = logging.getLogger(__name__)



def validate_stripe_configuration():
    """
    Validate Stripe configuration on startup.
    
    Checks:
    1. API key is LIVE mode
    2. All subscription prices exist
    3. All prices are recurring monthly
    4. All prices are active
    
    Raises:
        RuntimeError: If any validation fails
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    logger.info("=" * 80)
    logger.info("[STRIPE VALIDATOR] Starting Stripe configuration validation")
    logger.info("=" * 80)
    
    # 1. Validate API Key Mode
    api_key = stripe.api_key
    is_live = api_key.startswith("sk_live_") if api_key else False
    is_test = api_key.startswith("sk_test_") if api_key else False
    
    logger.info(f"[STRIPE VALIDATOR] API Key Prefix: {api_key[:10]}...")
    logger.info(f"[STRIPE VALIDATOR] API Key Mode: {'LIVE' if is_live else 'TEST' if is_test else 'UNKNOWN'}")
    logger.info(f"[STRIPE VALIDATOR] STRIPE_SECRET_KEY starts with: {api_key[:8]}...")
    logger.info(f"[STRIPE VALIDATOR] STRIPE_PUBLISHABLE_KEY: {settings.STRIPE_PUBLISHABLE_KEY[:8]}...")
    
    if not is_live:
        error_msg = f"❌ STRIPE API KEY IS NOT LIVE MODE! Key starts with: {api_key[:8]}"
        logger.error(f"[STRIPE VALIDATOR] {error_msg}")
        raise RuntimeError(error_msg)
    
    logger.info("[STRIPE VALIDATOR] ✅ Stripe API key is in LIVE mode")
    
    # 2. Validate Each Subscription Price
    all_price_ids = get_all_price_ids()
    logger.info(f"[STRIPE VALIDATOR] Validating {len(all_price_ids)} subscription prices...")
    
    all_valid = True
    for price_id in all_price_ids:
        plan_info = SUBSCRIPTION_PRICES[price_id]
        plan_name = plan_info["plan_name"]
        logger.info("-" * 80)
        logger.info(f"[STRIPE VALIDATOR] Validating {plan_name.upper()} plan: {price_id}")
        
        try:
            # Retrieve price from Stripe
            price = stripe.Price.retrieve(price_id)
            
            # Log price details
            logger.info(f"[STRIPE VALIDATOR]   price.id: {price.id}")
            logger.info(f"[STRIPE VALIDATOR]   price.type: {price.type}")
            logger.info(f"[STRIPE VALIDATOR]   price.active: {price.active}")
            
            if hasattr(price, 'recurring') and price.recurring:
                logger.info(f"[STRIPE VALIDATOR]   price.recurring.interval: {price.recurring.interval}")
                logger.info(f"[STRIPE VALIDATOR]   price.recurring.interval_count: {price.recurring.get('interval_count', 1)}")
            else:
                logger.info(f"[STRIPE VALIDATOR]   price.recurring: None (NOT A RECURRING PRICE)")
            
            # Validate: must be recurring
            if price.type != "recurring":
                error_msg = f"❌ {plan_name.upper()} price is NOT recurring! Type: {price.type}"
                logger.error(f"[STRIPE VALIDATOR]   {error_msg}")
                all_valid = False
                continue
            
            # Validate: must be monthly interval
            if not hasattr(price, 'recurring') or price.recurring.interval != "month":
                interval = price.recurring.interval if hasattr(price, 'recurring') else "N/A"
                error_msg = f"❌ {plan_name.upper()} price is NOT monthly! Interval: {interval}"
                logger.error(f"[STRIPE VALIDATOR]   {error_msg}")
                all_valid = False
                continue
            
            # Validate: must be active
            if not price.active:
                error_msg = f"❌ {plan_name.upper()} price is NOT active!"
                logger.error(f"[STRIPE VALIDATOR]   {error_msg}")
                all_valid = False
                continue
            
            logger.info(f"[STRIPE VALIDATOR]   ✅ {plan_name.upper()} price is valid (recurring monthly, active)")
            
        except stripe.error.InvalidRequestError as e:
            error_msg = f"❌ {plan_name.upper()} price NOT FOUND in Stripe: {str(e)}"
            logger.error(f"[STRIPE VALIDATOR]   {error_msg}")
            all_valid = False
        except Exception as e:
            error_msg = f"❌ {plan_name.upper()} validation error: {str(e)}"
            logger.error(f"[STRIPE VALIDATOR]   {error_msg}")
            all_valid = False
    
    logger.info("=" * 80)
    
    if not all_valid:
        error_msg = "❌ STRIPE VALIDATION FAILED! One or more prices are invalid."
        logger.error(f"[STRIPE VALIDATOR] {error_msg}")
        raise RuntimeError(error_msg)
    
    logger.info("[STRIPE VALIDATOR] ✅ ALL SUBSCRIPTION PRICES ARE VALID")
    logger.info("[STRIPE VALIDATOR] ✅ Stripe configuration validation PASSED")
    logger.info("=" * 80)


def preflight_check_price(price_id: str) -> dict:
    """
    Pre-flight check: Retrieve price from Stripe before creating checkout session.
    
    Args:
        price_id: Stripe price ID to validate
        
    Returns:
        dict: Price object details
        
    Raises:
        RuntimeError: If price cannot be retrieved or is invalid
    """
    logger.info(f"[STRIPE PREFLIGHT] Checking price: {price_id}")
    
    try:
        price = stripe.Price.retrieve(price_id)
        
        logger.info(f"[STRIPE PREFLIGHT]   ✅ Price found: {price.id}")
        logger.info(f"[STRIPE PREFLIGHT]   Type: {price.type}")
        logger.info(f"[STRIPE PREFLIGHT]   Active: {price.active}")
        
        if price.type == "recurring":
            logger.info(f"[STRIPE PREFLIGHT]   Interval: {price.recurring.interval}")
        
        if not price.active:
            raise RuntimeError(f"Price {price_id} is not active")
        
        return {
            "id": price.id,
            "type": price.type,
            "active": price.active,
            "recurring": price.recurring if hasattr(price, "recurring") else None
        }
        
    except stripe.error.InvalidRequestError as e:
        error_msg = f"Price {price_id} NOT FOUND in Stripe: {str(e)}"
        logger.error(f"[STRIPE PREFLIGHT]   ❌ {error_msg}")
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Failed to retrieve price {price_id}: {str(e)}"
        logger.error(f"[STRIPE PREFLIGHT]   ❌ {error_msg}")
        raise RuntimeError(error_msg)
