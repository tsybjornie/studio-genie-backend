from pydantic import BaseModel, EmailStr

class User(BaseModel):
    id: str
    email: EmailStr
    credits: int = 0
    stripe_customer_id: str | None = None

    class Config:
        from_attributes = True
