import hmac
import hashlib
import logging
from typing import Dict, Any

import requests
from fastapi import HTTPException

from app.core.config import settings
from app.core.database import db
from app.services.credit_service import credit_service

logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# COINBASE CONFIG
# -------------------------------------------------------------
COINBASE_API_BASE = "https://api.commerce.coinbase.com/charges"
COINBASE_HEADERS = {
    "X-CC-Api-Key": settings.COINBASE_API_KEY,
    "X-CC-Version": "2018-03-22",
    "Content-Type": "application/json",
}

# REAL CREDIT PACKS (MATCHES YOUR UI)
# prices in USD, credits in internal units
COINBASE_PACKS: Dict[str, Dict[str, Any]] = {
    "30": {
        "name": "30 Credits Pack",
        "price": 9,
        "credits": 30,
    },
    "100": {
        "name": "100 Credits Pack",
        "price": 29,
        "credits": 100,
    },
    "300": {
        "name": "300 Credits Pack",
        "price": 79,
        "credits": 300,
    },
    "1000": {
        "name": "1000 Credits Pack",
        "price": 249,
        "credits": 1000,
    },
}

# BONUS % FOR COINBASE PAYMENTS
BONUS_RATE = 0.20  # 20%


class CoinbaseService:
    # ---------------------------------------------------------
    # CREATE CHARGE & RETURN HOSTED URL
    # ---------------------------------------------------------
    def generate_checkout_link(self, pack_key: str, user_id: str) -> str:
        """
        Create a Coinbase Commerce charge for a credit pack and return
        the hosted checkout URL.
        """
        if pack_key not in COINBASE_PACKS:
            raise HTTPException(status_code=400, detail="Invalid Coinbase credit pack")

        pack = COINBASE_PACKS[pack_key]

        payload = {
            "name": pack["name"],
            "description": f"{pack['credits']} credit top-up for user {user_id}",
            "local_price": {
                "amount": str(pack["price"]),
                "currency": "USD",
            },
            "pricing_type": "fixed_price",
            "metadata": {
                "user_id": user_id,
                "pack_key": pack_key,
            },
        }

        try:
            resp = requests.post(
                COINBASE_API_BASE, json=payload, headers=COINBASE_HEADERS, timeout=10
            )
        except Exception as e:
            logger.error(f"[COINBASE] HTTP error during charge creation: {str(e)}")
            raise HTTPException(status_code=502, detail="Coinbase API error")

        if resp.status_code != 201:
            logger.error(f"[COINBASE] Charge creation failed: {resp.text}")
            raise HTTPException(
                status_code=502, detail="Failed to create Coinbase charge"
            )

        data = resp.json().get("data", {})
        hosted_url = data.get("hosted_url")

        if not hosted_url:
            logger.error(f"[COINBASE] Missing hosted_url in response: {resp.text}")
            raise HTTPException(
                status_code=502, detail="Coinbase charge missing hosted URL"
            )

        logger.info(
            f"[COINBASE] Created charge for user={user_id}, pack={pack_key}, url={hosted_url}"
        )
        return hosted_url

    # ---------------------------------------------------------
    # VERIFY WEBHOOK SIGNATURE
    # ---------------------------------------------------------
    def verify_signature(self, body: bytes, signature: str) -> bool:
        """
        Validate Coinbase Commerce webhook HMAC signature.
        """
        if not signature:
            logger.warning("[COINBASE] Missing webhook signature")
            return False

        computed = hmac.new(
            key=settings.COINBASE_WEBHOOK_SECRET.encode(),
            msg=body,
            digestmod=hashlib.sha256,
        ).hexdigest()

        valid = hmac.compare_digest(computed, signature)
        if not valid:
            logger.warning("[COINBASE] Invalid webhook signature")

        return valid

    # ---------------------------------------------------------
    # PROCESS PAYMENT WEBHOOK
    # ---------------------------------------------------------
    def process_payment(self, payload: dict):
        """
        Convert a confirmed Coinbase charge into credits.
        - Only handles `charge:confirmed`
        - Uses metadata.user_id + metadata.pack_key
        - Adds 20% bonus credits
        - Logs to payments table
        """
        event = payload.get("event")
        if not event:
            raise HTTPException(status_code=400, detail="Invalid Coinbase payload")

        event_type = event.get("type")
        if event_type != "charge:confirmed":
            logger.info(f"[COINBASE] Ignored event type: {event_type}")
            return

        data = event.get("data", {})
        metadata = data.get("metadata", {}) or {}

        user_id = metadata.get("user_id")
        pack_key = metadata.get("pack_key")

        if not user_id or not pack_key:
            logger.error("[COINBASE] Missing metadata (user_id / pack_key)")
            raise HTTPException(
                status_code=400, detail="Coinbase metadata incomplete"
            )

        if pack_key not in COINBASE_PACKS:
            logger.error(f"[COINBASE] Unknown pack_key: {pack_key}")
            raise HTTPException(status_code=400, detail="Invalid Coinbase credit pack")

        base_credits = COINBASE_PACKS[pack_key]["credits"]
        bonus_credits = int(base_credits * BONUS_RATE)
        total_credits = base_credits + bonus_credits

        # Stack credits onto user
        new_balance = credit_service.add_credits(
            user_id=user_id,
            amount=total_credits,
            reason="coinbase_topup",
        )

        # Log in payments table (optional but recommended)
        try:
            db.service_client.table("payments").insert(
                {
                    "user_id": user_id,
                    "provider": "coinbase",
                    "amount": base_credits,
                    "bonus": bonus_credits,
                    "total_credits": total_credits,
                    "status": "confirmed",
                }
            ).execute()
        except Exception as e:
            # Don't murder the webhook if logging fails
            logger.error(f"[COINBASE] Failed to log payment: {str(e)}")

        logger.info(
            f"[COINBASE] User={user_id} bought {base_credits} + {bonus_credits} bonus → "
            f"{total_credits} credits (new balance {new_balance})"
        )

        return new_balance


coinbase_service = CoinbaseService()
