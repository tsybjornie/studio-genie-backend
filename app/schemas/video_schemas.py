from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VideoGenerateRequest(BaseModel):
    """Schema for video generation request"""
    prompt: str
    style: str
    image_url: Optional[str] = None


class VideoGenerateResponse(BaseModel):
    """Schema for video generation response"""
    job_id: str
    video_id: str
    status: str
    message: str
    credits_used: int
    credits_remaining: int


class VideoListResponse(BaseModel):
    """Schema for video list item"""
    id: str
    prompt: str
    style: str
    status: str
    video_url: Optional[str] = None
    created_at: datetime


class VideoDetailResponse(BaseModel):
    """Schema for detailed video response"""
    id: str
    user_id: str
    prompt: str
    style: str
    image_url: Optional[str] = None
    status: str
    video_url: Optional[str] = None
    created_at: datetime
