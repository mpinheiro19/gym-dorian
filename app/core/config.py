"""
Core configuration module for the application.

This module defines the Settings class that manages application configuration
through environment variables and .env files. The configuration follows a priority:
1. Environment variables (highest priority - used by Docker Compose)
2. .env file (fallback for local development)
3. Default values (lowest priority)
"""
from typing import Literal, Optional
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.

    Attributes:
        DATABASE_URL: PostgreSQL connection string. Must be a valid PostgreSQL DSN.
        ENV_STATE: Application environment state (development, staging, production).
        SECRET_KEY: Secret key for JWT token signing. Must be set in production.
        ALGORITHM: JWT algorithm to use for token signing.
        ACCESS_TOKEN_EXPIRE_MINUTES: JWT token expiration time in minutes.
        SMTP_HOST: SMTP server hostname (e.g., smtp.gmail.com).
        SMTP_PORT: SMTP server port (587 for STARTTLS, 465 for SSL).
        SMTP_USER: SMTP authentication username or email address.
        SMTP_PASSWORD: SMTP authentication password or app password.
        SMTP_USE_TLS: Use STARTTLS for the SMTP connection (port 587).
        SMTP_USE_SSL: Use SSL for the SMTP connection (port 465).
        SENDER_EMAIL: The "From" email address for outgoing emails.
        SENDER_NAME: The display name shown in the "From" field.

    Note:
        Do not hardcode credentials in source. `DATABASE_URL` and `SECRET_KEY`
        should be provided via environment variables or a local `.env` file.
    """

    DATABASE_URL: Optional[PostgresDsn] = Field(
        default=None,
        description=(
            "PostgreSQL database connection URL. Must be provided via environment "
            "variables or a local .env file. Avoid hardcoding credentials in source."
        ),
    )

    ENV_STATE: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment state.",
    )

    # JWT Authentication settings
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description=(
            "Secret key for JWT token signing. MUST be changed in production. "
            "Generate with: openssl rand -hex 32"
        ),
    )

    ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm for token signing.",
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="JWT access token expiration time in minutes.",
    )

    # SMTP / Email settings
    SMTP_HOST: Optional[str] = Field(
        default=None,
        description="SMTP server hostname (e.g., smtp.gmail.com).",
    )

    SMTP_PORT: int = Field(
        default=587,
        description="SMTP server port. 587 for STARTTLS, 465 for SSL.",
    )

    SMTP_USER: Optional[str] = Field(
        default=None,
        description="SMTP authentication username or email address.",
    )

    SMTP_PASSWORD: Optional[str] = Field(
        default=None,
        description="SMTP authentication password or app password.",
    )

    SMTP_USE_TLS: bool = Field(
        default=True,
        description="Use STARTTLS for the SMTP connection (recommended for port 587).",
    )

    SMTP_USE_SSL: bool = Field(
        default=False,
        description="Use SSL for the SMTP connection (for port 465).",
    )

    SENDER_EMAIL: Optional[str] = Field(
        default=None,
        description='The "From" email address for outgoing emails.',
    )

    SENDER_NAME: str = Field(
        default="Gym Dorian",
        description='The display name shown in the "From" field.',
    )

    @property
    def smtp_configured(self) -> bool:
        """Return True if the minimum SMTP settings are present to send emails."""
        return bool(self.SMTP_HOST and self.SENDER_EMAIL)

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )


# Global settings instance - imported by other modules
settings = Settings()