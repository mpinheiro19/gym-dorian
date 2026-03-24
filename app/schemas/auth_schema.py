"""
Authentication schemas for the application.

Defines Pydantic models for the Password Reset Flow feature.
These schemas are stubs — the endpoints consuming them will be implemented
in the Password Reset Flow feature (spec: password-reset-flow).
"""
import re

from pydantic import BaseModel, EmailStr, field_validator


class ForgotPasswordRequest(BaseModel):
    """Request payload for initiating a password reset."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request payload for completing a password reset with token."""

    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_policy(cls, v: str) -> str:
        """Enforce: min 8 chars, at least 1 uppercase letter, at least 1 special char."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("Password must contain at least one special character.")
        return v


class PasswordResetResponse(BaseModel):
    """Generic response for password reset operations."""

    detail: str
