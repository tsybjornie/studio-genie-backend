from fastapi import APIRouter, Response

router = APIRouter()

@router.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    return Response(status_code=200)
