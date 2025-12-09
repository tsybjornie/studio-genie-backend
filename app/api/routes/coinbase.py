from fastapi import APIRouter

router = APIRouter(prefix="/coinbase", tags=["Coinbase"])

@router.get("")
async def disabled():
    return {"status": "coinbase_disabled"}
