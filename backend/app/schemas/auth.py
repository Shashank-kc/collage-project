"""
CodeGuard AI - Authentication Request & Response Schemas
========================================================
Validates user registration, login payloads, and returns sanitized user identities.
"""

import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserRegisterRequest(BaseModel):
    """Payload for user account creation."""
    full_name: str = Field(..., min_length=2, max_length=100, description="User's real or display name")
    email: str = Field(..., description="Valid personal or work email address")
    password: str = Field(..., min_length=8, max_length=128, description="Strong password (at least 8 chars)")

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Full name cannot be empty or whitespace.")
        return trimmed

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not clean or not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format.")
        return clean

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if v.isdigit() or v.isalpha():
            raise ValueError("Password must contain both letters and numbers/symbols.")
        return v


class UserLoginRequest(BaseModel):
    """Payload for account credential authentication."""
    email: str = Field(..., description="Registered email address")
    password: str = Field(..., min_length=1, max_length=128, description="Account password")
    remember_me: bool = Field(default=False, description="Persist session for extended period")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not clean or not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format.")
        return clean


class UserResponse(BaseModel):
    """Sanitized public user profile. Password hash is never exposed."""
    id: int
    email: str
    full_name: str
    created_at: str


class AuthSuccessResponse(BaseModel):
    """Successful authentication response payload."""
    user: UserResponse
    message: str
    token: str
