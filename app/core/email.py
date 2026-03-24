"""
Email delivery module for the application.

Provides a simple, reusable API for sending HTML emails via SMTP.
In development mode (or when SMTP is not configured), emails are printed
to stdout for easy inspection without any external dependencies.

Usage:
    from app.core.email import send_email, build_password_reset_email, SendEmailRequest

    request = build_password_reset_email(user_email="user@example.com", reset_link="https://...")
    success = send_email(request)
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pydantic import BaseModel, EmailStr

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailConfig(BaseModel):
    """SMTP connection configuration derived from application settings."""

    smtp_host: str
    smtp_port: int
    smtp_user: str | None
    smtp_password: str | None
    sender_email: str
    sender_name: str
    use_tls: bool
    use_ssl: bool


class SendEmailRequest(BaseModel):
    """Payload for a single outgoing email."""

    to: EmailStr
    subject: str
    html_body: str


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _log_email_to_console(request: SendEmailRequest) -> None:
    """Print email contents to stdout/log — used in development."""
    truncated_body = request.html_body[:500] + ("..." if len(request.html_body) > 500 else "")
    output = (
        "\n===== DEV EMAIL =====\n"
        f"To:      {request.to}\n"
        f"Subject: {request.subject}\n"
        f"Body:\n{truncated_body}\n"
        "===== END DEV EMAIL =====\n"
    )
    logger.info(output)


def _send_smtp_email(config: EmailConfig, request: SendEmailRequest) -> None:
    """Send an HTML email over SMTP.

    Raises:
        smtplib.SMTPException: On any SMTP-level error. The caller is responsible
            for catching this and deciding how to handle it.
    """
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{config.sender_name} <{config.sender_email}>"
    msg["To"] = request.to
    msg["Subject"] = request.subject
    msg.attach(MIMEText(request.html_body, "html"))

    if config.use_ssl:
        with smtplib.SMTP_SSL(config.smtp_host, config.smtp_port) as smtp:
            if config.smtp_user and config.smtp_password:
                smtp.login(config.smtp_user, config.smtp_password)
            smtp.sendmail(config.sender_email, request.to, msg.as_string())
    else:
        with smtplib.SMTP(config.smtp_host, config.smtp_port) as smtp:
            if config.use_tls:
                smtp.starttls()
            if config.smtp_user and config.smtp_password:
                smtp.login(config.smtp_user, config.smtp_password)
            smtp.sendmail(config.sender_email, request.to, msg.as_string())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def send_email(request: SendEmailRequest) -> bool:
    """Send an email, falling back to console output in development.

    Never raises — callers receive a boolean indicating success or failure.

    Returns:
        True  — email was sent (or printed to console in dev mode).
        False — SMTP error occurred in production (error is logged).
    """
    use_fallback = (
        settings.ENV_STATE == "development"
        or not settings.smtp_configured
    )

    if use_fallback:
        _log_email_to_console(request)
        return True

    config = EmailConfig(
        smtp_host=settings.SMTP_HOST,  # type: ignore[arg-type]
        smtp_port=settings.SMTP_PORT,
        smtp_user=settings.SMTP_USER,
        smtp_password=settings.SMTP_PASSWORD,
        sender_email=settings.SENDER_EMAIL,  # type: ignore[arg-type]
        sender_name=settings.SENDER_NAME,
        use_tls=settings.SMTP_USE_TLS,
        use_ssl=settings.SMTP_USE_SSL,
    )

    try:
        _send_smtp_email(config, request)
        return True
    except smtplib.SMTPException as exc:
        logger.error("Failed to send email to %s: %s", request.to, exc)
        return False


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------


def build_password_reset_email(user_email: str, reset_link: str) -> SendEmailRequest:
    """Build a password-reset HTML email for the given user.

    This is a template utility consumed by the Password Reset Flow feature.
    """
    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Reset your Gym Dorian password</title>
  <style>
    body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
    .header {{ background-color: #2563eb; padding: 24px 32px; }}
    .header h1 {{ color: #ffffff; margin: 0; font-size: 22px; }}
    .body {{ padding: 32px; color: #374151; }}
    .body p {{ line-height: 1.6; margin: 0 0 16px; }}
    .cta {{ text-align: center; margin: 32px 0; }}
    .cta a {{ background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 6px; font-weight: bold; font-size: 16px; display: inline-block; }}
    .footer {{ padding: 24px 32px; border-top: 1px solid #e5e7eb; font-size: 13px; color: #9ca3af; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Gym Dorian</h1>
    </div>
    <div class="body">
      <p>You requested a password reset for your Gym Dorian account (<strong>{user_email}</strong>).</p>
      <p>Click the button below to set a new password. This link expires in <strong>1 hour</strong>.</p>
      <div class="cta">
        <a href="{reset_link}">Reset my password</a>
      </div>
      <p>If you didn't request this, you can safely ignore this email — your password will not change.</p>
    </div>
    <div class="footer">
      <p>This email was sent by Gym Dorian. Do not reply to this email.</p>
    </div>
  </div>
</body>
</html>"""

    return SendEmailRequest(
        to=user_email,
        subject="Reset your Gym Dorian password",
        html_body=html_body,
    )
