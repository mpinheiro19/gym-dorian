"""
Unit tests for app.schemas.auth_schema module.

Tests cover:
- ForgotPasswordRequest — valid and invalid email
- ResetPasswordRequest — valid password, and each policy violation
- PasswordResetResponse model
"""
import pytest
from pydantic import ValidationError

from app.schemas.auth_schema import (
    ForgotPasswordRequest,
    PasswordResetResponse,
    ResetPasswordRequest,
)


@pytest.mark.unit
class TestForgotPasswordRequest:
    def test_forgot_password_request_valid_email(self):
        """Valid email address is accepted."""
        req = ForgotPasswordRequest(email="user@example.com")
        assert str(req.email) == "user@example.com"

    def test_forgot_password_request_invalid_email_rejected(self):
        """Non-email string is rejected by Pydantic EmailStr."""
        with pytest.raises(ValidationError):
            ForgotPasswordRequest(email="not-an-email")


@pytest.mark.unit
class TestResetPasswordRequest:
    def test_reset_password_request_valid(self):
        """Token + compliant password is accepted."""
        req = ResetPasswordRequest(token="sometoken123", new_password="Secure@1")
        assert req.token == "sometoken123"
        assert req.new_password == "Secure@1"

    def test_reset_password_request_short_password_rejected(self):
        """Password shorter than 8 chars is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ResetPasswordRequest(token="tok", new_password="Ab@1")
        assert "8 characters" in str(exc_info.value)

    def test_reset_password_request_missing_uppercase_rejected(self):
        """Password without an uppercase letter is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ResetPasswordRequest(token="tok", new_password="secure@123")
        assert "uppercase" in str(exc_info.value)

    def test_reset_password_request_missing_special_char_rejected(self):
        """Password without a special character is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ResetPasswordRequest(token="tok", new_password="Secure123")
        assert "special character" in str(exc_info.value)


@pytest.mark.unit
class TestPasswordResetResponse:
    def test_password_reset_response_model(self):
        """PasswordResetResponse holds the detail string."""
        resp = PasswordResetResponse(detail="Password reset successful.")
        assert resp.detail == "Password reset successful."
