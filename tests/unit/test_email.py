"""
Unit tests for app.core.email module.

Tests cover:
- Dev mode console fallback
- Unconfigured SMTP fallback
- Production SMTP send (TLS and SSL paths)
- SMTP failure handling (returns False, logs error)
- build_password_reset_email template helper
- EmailConfig construction from settings
- SendEmailRequest validation
"""

import smtplib
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.core.email import (
    EmailConfig,
    SendEmailRequest,
    build_password_reset_email,
    send_email,
)


@pytest.mark.unit
class TestSendEmailDevMode:
    def test_send_email_dev_mode_prints_to_console(self, monkeypatch, caplog):
        """In development mode, send_email logs to console and returns True."""
        import logging

        monkeypatch.setattr("app.core.email.settings.ENV_STATE", "development")
        monkeypatch.setattr("app.core.email.settings.SMTP_HOST", None)
        monkeypatch.setattr("app.core.email.settings.SENDER_EMAIL", None)

        request = SendEmailRequest(
            to="user@example.com",
            subject="Hello",
            html_body="<p>Test</p>",
        )

        with caplog.at_level(logging.INFO, logger="app.core.email"):
            result = send_email(request)

        assert result is True
        assert "DEV EMAIL" in caplog.text
        assert "user@example.com" in caplog.text

    def test_send_email_no_smtp_configured_uses_fallback(self, monkeypatch, caplog):
        """When SMTP is not configured, even in production, fallback to console."""
        import logging

        monkeypatch.setattr("app.core.email.settings.ENV_STATE", "production")
        monkeypatch.setattr("app.core.email.settings.SMTP_HOST", None)
        monkeypatch.setattr("app.core.email.settings.SENDER_EMAIL", None)

        request = SendEmailRequest(
            to="user@example.com",
            subject="No SMTP",
            html_body="<p>body</p>",
        )

        with caplog.at_level(logging.INFO, logger="app.core.email"):
            result = send_email(request)

        assert result is True
        assert "DEV EMAIL" in caplog.text


@pytest.mark.unit
class TestSendEmailProduction:
    def test_send_email_production_success(self, monkeypatch):
        """Production TLS path: SMTP is called with correct sequence."""
        monkeypatch.setattr("app.core.email.settings.ENV_STATE", "production")
        monkeypatch.setattr("app.core.email.settings.SMTP_HOST", "smtp.gmail.com")
        monkeypatch.setattr("app.core.email.settings.SMTP_PORT", 587)
        monkeypatch.setattr("app.core.email.settings.SMTP_USER", "user@gmail.com")
        monkeypatch.setattr("app.core.email.settings.SMTP_PASSWORD", "app-password")
        monkeypatch.setattr("app.core.email.settings.SMTP_USE_TLS", True)
        monkeypatch.setattr("app.core.email.settings.SMTP_USE_SSL", False)
        monkeypatch.setattr(
            "app.core.email.settings.SENDER_EMAIL", "noreply@gymdorian.com"
        )
        monkeypatch.setattr("app.core.email.settings.SENDER_NAME", "Gym Dorian")

        request = SendEmailRequest(
            to="recipient@example.com",
            subject="Test",
            html_body="<p>Hello</p>",
        )

        mock_smtp_instance = MagicMock()
        mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
        mock_smtp_instance.__exit__ = MagicMock(return_value=False)

        with patch("smtplib.SMTP", return_value=mock_smtp_instance) as mock_smtp_cls:
            result = send_email(request)

        assert result is True
        mock_smtp_cls.assert_called_once_with("smtp.gmail.com", 587)
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with(
            "user@gmail.com", "app-password"
        )
        mock_smtp_instance.sendmail.assert_called_once()

    def test_send_email_production_ssl_success(self, monkeypatch):
        """Production SSL path: SMTP_SSL is called instead of SMTP."""
        monkeypatch.setattr("app.core.email.settings.ENV_STATE", "production")
        monkeypatch.setattr("app.core.email.settings.SMTP_HOST", "smtp.gmail.com")
        monkeypatch.setattr("app.core.email.settings.SMTP_PORT", 465)
        monkeypatch.setattr("app.core.email.settings.SMTP_USER", "user@gmail.com")
        monkeypatch.setattr("app.core.email.settings.SMTP_PASSWORD", "app-password")
        monkeypatch.setattr("app.core.email.settings.SMTP_USE_TLS", False)
        monkeypatch.setattr("app.core.email.settings.SMTP_USE_SSL", True)
        monkeypatch.setattr(
            "app.core.email.settings.SENDER_EMAIL", "noreply@gymdorian.com"
        )
        monkeypatch.setattr("app.core.email.settings.SENDER_NAME", "Gym Dorian")

        request = SendEmailRequest(
            to="recipient@example.com",
            subject="SSL Test",
            html_body="<p>SSL</p>",
        )

        mock_smtp_instance = MagicMock()
        mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
        mock_smtp_instance.__exit__ = MagicMock(return_value=False)

        with patch("smtplib.SMTP_SSL", return_value=mock_smtp_instance) as mock_ssl_cls:
            result = send_email(request)

        assert result is True
        mock_ssl_cls.assert_called_once_with("smtp.gmail.com", 465)
        mock_smtp_instance.starttls.assert_not_called()
        mock_smtp_instance.login.assert_called_once_with(
            "user@gmail.com", "app-password"
        )
        mock_smtp_instance.sendmail.assert_called_once()

    def test_send_email_smtp_failure_returns_false(self, monkeypatch):
        """SMTPException during send returns False without raising."""
        monkeypatch.setattr("app.core.email.settings.ENV_STATE", "production")
        monkeypatch.setattr("app.core.email.settings.SMTP_HOST", "smtp.gmail.com")
        monkeypatch.setattr("app.core.email.settings.SMTP_PORT", 587)
        monkeypatch.setattr("app.core.email.settings.SMTP_USER", "user@gmail.com")
        monkeypatch.setattr("app.core.email.settings.SMTP_PASSWORD", "bad-pass")
        monkeypatch.setattr("app.core.email.settings.SMTP_USE_TLS", True)
        monkeypatch.setattr("app.core.email.settings.SMTP_USE_SSL", False)
        monkeypatch.setattr(
            "app.core.email.settings.SENDER_EMAIL", "noreply@gymdorian.com"
        )
        monkeypatch.setattr("app.core.email.settings.SENDER_NAME", "Gym Dorian")

        request = SendEmailRequest(
            to="recipient@example.com",
            subject="Fail",
            html_body="<p>Fail</p>",
        )

        with patch(
            "smtplib.SMTP", side_effect=smtplib.SMTPException("connection refused")
        ):
            result = send_email(request)

        assert result is False

    def test_send_email_logs_error_on_failure(self, monkeypatch, caplog):
        """An SMTP error is logged at ERROR level."""
        import logging

        monkeypatch.setattr("app.core.email.settings.ENV_STATE", "production")
        monkeypatch.setattr("app.core.email.settings.SMTP_HOST", "smtp.example.com")
        monkeypatch.setattr("app.core.email.settings.SMTP_PORT", 587)
        monkeypatch.setattr("app.core.email.settings.SMTP_USER", None)
        monkeypatch.setattr("app.core.email.settings.SMTP_PASSWORD", None)
        monkeypatch.setattr("app.core.email.settings.SMTP_USE_TLS", True)
        monkeypatch.setattr("app.core.email.settings.SMTP_USE_SSL", False)
        monkeypatch.setattr(
            "app.core.email.settings.SENDER_EMAIL", "noreply@example.com"
        )
        monkeypatch.setattr("app.core.email.settings.SENDER_NAME", "Test")

        request = SendEmailRequest(
            to="user@example.com",
            subject="Err",
            html_body="<p>x</p>",
        )

        with patch("smtplib.SMTP", side_effect=smtplib.SMTPException("timeout")):
            with caplog.at_level(logging.ERROR, logger="app.core.email"):
                send_email(request)

        assert "Failed to send email" in caplog.text
        assert "user@example.com" in caplog.text

    def test_send_email_smtp_auth_failure_returns_false(self, monkeypatch):
        """SMTPAuthenticationError (subclass of SMTPException) also returns False."""
        monkeypatch.setattr("app.core.email.settings.ENV_STATE", "production")
        monkeypatch.setattr("app.core.email.settings.SMTP_HOST", "smtp.gmail.com")
        monkeypatch.setattr("app.core.email.settings.SMTP_PORT", 587)
        monkeypatch.setattr("app.core.email.settings.SMTP_USER", "user@gmail.com")
        monkeypatch.setattr("app.core.email.settings.SMTP_PASSWORD", "wrong")
        monkeypatch.setattr("app.core.email.settings.SMTP_USE_TLS", True)
        monkeypatch.setattr("app.core.email.settings.SMTP_USE_SSL", False)
        monkeypatch.setattr(
            "app.core.email.settings.SENDER_EMAIL", "noreply@gymdorian.com"
        )
        monkeypatch.setattr("app.core.email.settings.SENDER_NAME", "Gym Dorian")

        request = SendEmailRequest(
            to="user@example.com",
            subject="Auth Fail",
            html_body="<p>x</p>",
        )

        with patch(
            "smtplib.SMTP",
            side_effect=smtplib.SMTPAuthenticationError(535, b"Bad credentials"),
        ):
            result = send_email(request)

        assert result is False


@pytest.mark.unit
class TestBuildPasswordResetEmail:
    def test_build_password_reset_email_contains_link(self):
        """The reset link appears in the HTML body."""
        link = "https://app.gymdorian.com/reset?token=abc123"
        result = build_password_reset_email("user@example.com", link)
        assert link in result.html_body

    def test_build_password_reset_email_correct_recipient(self):
        """The email is addressed to the supplied user_email."""
        result = build_password_reset_email(
            "athlete@example.com", "https://example.com/reset"
        )
        assert result.to == "athlete@example.com"

    def test_build_password_reset_email_subject(self):
        """Subject line is set correctly."""
        result = build_password_reset_email("u@e.com", "https://x.com")
        assert "Gym Dorian" in result.subject or "password" in result.subject.lower()

    def test_build_password_reset_email_html_structure(self):
        """HTML body contains essential structural elements."""
        result = build_password_reset_email(
            "u@example.com", "https://example.com/reset"
        )
        assert "<!DOCTYPE html>" in result.html_body
        assert "1 hour" in result.html_body


@pytest.mark.unit
class TestEmailConfig:
    def test_email_config_from_settings(self):
        """EmailConfig can be constructed with explicit values."""
        config = EmailConfig(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="user@gmail.com",
            smtp_password="secret",
            sender_email="noreply@gymdorian.com",
            sender_name="Gym Dorian",
            use_tls=True,
            use_ssl=False,
        )
        assert config.smtp_host == "smtp.gmail.com"
        assert config.use_tls is True
        assert config.use_ssl is False


@pytest.mark.unit
class TestSendEmailRequestValidation:
    def test_send_email_request_valid(self):
        """SendEmailRequest accepts valid fields."""
        req = SendEmailRequest(
            to="user@example.com",
            subject="Hello",
            html_body="<p>body</p>",
        )
        assert req.to == "user@example.com"

    def test_send_email_request_invalid_email(self):
        """SendEmailRequest rejects an invalid email address."""
        with pytest.raises(ValidationError):
            SendEmailRequest(to="not-an-email", subject="Hi", html_body="<p>x</p>")
