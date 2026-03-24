"""
Integration tests for app.core.email module.

Tests the email module end-to-end using real Settings instances
and monkeypatching only the network layer (smtplib) when needed.
"""

import pytest

from app.core.email import SendEmailRequest, send_email


@pytest.mark.integration
class TestEmailEndToEnd:
    def test_send_email_end_to_end_dev_mode(self, monkeypatch, caplog):
        """In development mode with real Settings, email is printed to console."""
        import logging

        # Force dev mode regardless of local .env
        monkeypatch.setattr("app.core.email.settings.ENV_STATE", "development")

        request = SendEmailRequest(
            to="integration@example.com",
            subject="Integration test",
            html_body="<p>Integration body</p>",
        )

        with caplog.at_level(logging.INFO, logger="app.core.email"):
            result = send_email(request)

        assert result is True
        assert "DEV EMAIL" in caplog.text
        assert "integration@example.com" in caplog.text

    def test_send_email_unconfigured_smtp_is_safe(self, monkeypatch, caplog):
        """Production mode with no SMTP config gracefully falls back to console."""
        import logging

        monkeypatch.setattr("app.core.email.settings.ENV_STATE", "production")
        monkeypatch.setattr("app.core.email.settings.SMTP_HOST", None)
        monkeypatch.setattr("app.core.email.settings.SENDER_EMAIL", None)

        request = SendEmailRequest(
            to="safe@example.com",
            subject="Safe fallback",
            html_body="<p>No SMTP configured</p>",
        )

        with caplog.at_level(logging.INFO, logger="app.core.email"):
            result = send_email(request)

        # Must not raise and must return True (console fallback)
        assert result is True
        assert "DEV EMAIL" in caplog.text
