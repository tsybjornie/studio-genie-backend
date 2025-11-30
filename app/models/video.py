from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Video(BaseModel):
    """Video model"""
    id: str
    user_id: str
    prompt: str
    style: str
    image_url: Optional[str] = None
    status: str = "queued"  # queued, processing, done, failed
    video_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class VideoCreate(BaseModel):
    """Schema for creating a new video"""
    prompt: str
    style: str
    image_url: Optional[str] = None


class VideoResponse(BaseModel):
    """Schema for video response"""
    id: str
    user_id: str
    prompt: str
    style: str
    image_url: Optional[str] = None
    status: str
    video_url: Optional[str] = None
    created_at: datetime
