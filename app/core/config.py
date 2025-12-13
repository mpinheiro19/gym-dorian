"""
Core configuration module for the application.

This module defines the Settings class that manages application configuration
through environment variables and .env files. The configuration follows a priority:
1. Environment variables (highest priority - used by Docker Compose)
2. .env file (fallback for local development)
3. Default values (lowest priority)
"""
from typing import Literal
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    
    Attributes:
        DATABASE_URL: PostgreSQL connection string. Must be a valid PostgreSQL DSN.
        ENV_STATE: Application environment state (development, staging, production).
    
    Examples:
        >>> settings = Settings()
        >>> str(settings.DATABASE_URL)
        'postgresql+psycopg2://user:password@localhost:5432/gym_db'
    """
    
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+psycopg2://user:password@localhost:5432/gym_db",
        description="PostgreSQL database connection URL. Overridden by Docker Compose.",
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