"""
User schemas — Pydantic models for auth request/response validation.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: str
    password: str
    role: str = "viewer"  # default role is viewer


class UserRead(BaseModel):
    """Schema for user response (no password)."""
    id: int
    email: str
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Schema for login request."""
    email: str
    password: str
