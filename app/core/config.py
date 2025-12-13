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
    
    Note:
        Do not hardcode credentials in source. `DATABASE_URL` should be provided
        via environment variables or a local `.env` file. When not set, the
        attribute may be `None` in development environments.
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
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )


# Global settings instance - imported by other modules
settings = Settings()