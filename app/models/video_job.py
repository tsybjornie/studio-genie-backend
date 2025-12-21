from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class VideoJob(BaseModel):
    id: str
    user_id: str

    prompt: str
    duration_seconds: int

    status: str  # queued | processing | completed | failed

    provider: str  # mock | heygen (future)
    video_url: Optional[str] = None
    error: Optional[str] = None

    created_at: datetime
    updated_at: datetime
