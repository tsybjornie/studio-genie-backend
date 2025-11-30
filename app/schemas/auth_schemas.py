from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class UserResponse(BaseModel):
    """Schema for user information response"""
    id: str
    email: EmailStr
    has_trial_used: bool
    credits_remaining: int
    plan: str | None = None
