"""
Unit tests for app.core.config module.

Tests cover:
- Settings parsing with default values
- Environment variable override
- .env file loading
- DATABASE_URL validation
- ENV_STATE validation
"""
import os
import pytest
from pathlib import Path
from pydantic import ValidationError
from app.core.config import Settings


@pytest.mark.unit
class TestSettings:
    """Unit tests for Settings class."""
    
    def test_settings_default_values(self, monkeypatch):
        """Test Settings initialization with default values."""
        # Clear any environment variables
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("ENV_STATE", raising=False)
        
        # Mock _env_file to prevent loading from actual .env
        monkeypatch.setattr(
            "app.core.config.Settings.model_config",
            {"env_file": None, "extra": "ignore"}
        )
        
        settings = Settings()
        
        # Check defaults
        assert str(settings.DATABASE_URL) == "postgresql+psycopg2://user:password@localhost:5432/gym_db"
        assert settings.ENV_STATE == "development"
    
    def test_settings_from_environment_variables(self, monkeypatch):
        """Test Settings loading from environment variables."""
        # Set environment variables (simulating Docker Compose)
        monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://testuser:testpass@testhost:5432/testdb")
        monkeypatch.setenv("ENV_STATE", "production")
        
        settings = Settings()
        
        assert "testuser" in str(settings.DATABASE_URL)
        assert "testhost" in str(settings.DATABASE_URL)
        assert "testdb" in str(settings.DATABASE_URL)
        assert settings.ENV_STATE == "production"
    
    def test_settings_database_url_validation(self, monkeypatch):
        """Test DATABASE_URL validation with PostgresDsn."""
        # Valid PostgreSQL URL
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host:5432/db")
        settings = Settings()
        assert "postgresql" in str(settings.DATABASE_URL)
        
        # Valid PostgreSQL with psycopg2
        monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://user:pass@host:5432/db")
        settings = Settings()
        assert "postgresql+psycopg2" in str(settings.DATABASE_URL)
    
    def test_settings_invalid_database_url(self, monkeypatch):
        """Test Settings raises error for invalid DATABASE_URL."""
        # Invalid URL format should raise ValidationError
        monkeypatch.setenv("DATABASE_URL", "not-a-valid-url")
        
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        assert "DATABASE_URL" in str(exc_info.value)
    
    def test_settings_env_state_validation(self, monkeypatch):
        """Test ENV_STATE accepts only valid literal values."""
        # Valid values
        for valid_state in ["development", "staging", "production"]:
            monkeypatch.setenv("ENV_STATE", valid_state)
            settings = Settings()
            assert settings.ENV_STATE == valid_state
    
    def test_settings_invalid_env_state(self, monkeypatch):
        """Test ENV_STATE rejects invalid values."""
        monkeypatch.setenv("ENV_STATE", "invalid_state")
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host:5432/db")
        
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        assert "ENV_STATE" in str(exc_info.value)
    
    def test_settings_extra_fields_ignored(self, monkeypatch):
        """Test that extra environment variables are ignored."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host:5432/db")
        monkeypatch.setenv("RANDOM_EXTRA_VAR", "some_value")
        
        # Should not raise error due to extra='ignore'
        settings = Settings()
        assert not hasattr(settings, "RANDOM_EXTRA_VAR")
    
    def test_settings_case_insensitive(self, monkeypatch):
        """Test that environment variables are case-insensitive."""
        # lowercase env var should work
        monkeypatch.setenv("database_url", "postgresql://user:pass@host:5432/db")
        monkeypatch.setenv("env_state", "staging")
        
        settings = Settings()
        assert "postgresql" in str(settings.DATABASE_URL)
        assert settings.ENV_STATE == "staging"
    
    def test_settings_from_env_file(self, tmp_path, monkeypatch):
        """Test Settings loading from .env file."""
        # Create a temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text(
            "DATABASE_URL=postgresql://envfile:pass@localhost:5432/envdb\n"
            "ENV_STATE=staging\n"
        )
        
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        # Clear environment variables to test .env file loading
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("ENV_STATE", raising=False)
        
        settings = Settings()
        
        assert "envfile" in str(settings.DATABASE_URL)
        assert "envdb" in str(settings.DATABASE_URL)
        assert settings.ENV_STATE == "staging"
    
    def test_settings_env_var_overrides_env_file(self, tmp_path, monkeypatch):
        """Test environment variables override .env file (priority test)."""
        # Create .env file with some values
        env_file = tmp_path / ".env"
        env_file.write_text(
            "DATABASE_URL=postgresql://envfile:pass@localhost:5432/envdb\n"
            "ENV_STATE=development\n"
        )
        
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        # Set environment variable (should override .env file)
        monkeypatch.setenv("DATABASE_URL", "postgresql://override:pass@localhost:5432/overridedb")
        monkeypatch.setenv("ENV_STATE", "production")
        
        settings = Settings()
        
        # Environment variable should win
        assert "override" in str(settings.DATABASE_URL)
        assert "overridedb" in str(settings.DATABASE_URL)
        assert settings.ENV_STATE == "production"
