from app.core.database import db
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class CreditService:

    def get_balance(self, user_id):
        result = (
            db.service_client
            .table("users")
            .select("credits_remaining")
            .eq("id", user_id)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(404, "User not found")

        return result.data["credits_remaining"]

    def add_credits(self, user_id, amount, reason="topup"):
        if amount <= 0:
            raise HTTPException(400, "Invalid credit amount")

        update = (
            db.service_client.rpc("increment_credits", {"uid": user_id, "amount": amount})
            .execute()
        )

        logger.info(f"[CREDITS] Added {amount} credits to {user_id} — reason={reason}")
        return self.get_balance(user_id)

    def deduct_credits(self, user_id, amount):
        balance = self.get_balance(user_id)

        if balance < amount:
            raise HTTPException(402, "Not enough credits")

        update = (
            db.service_client.rpc("decrement_credits", {"uid": user_id, "amount": amount})
            .execute()
        )

        logger.info(f"[CREDITS] Deducted {amount} credits from {user_id}")
        return self.get_balance(user_id)

    def use_trial(self, user_id):
        update = (
            db.service_client
            .table("users")
            .update({"has_trial_used": True})
            .eq("id", user_id)
            .execute()
        )

credit_service = CreditService()
