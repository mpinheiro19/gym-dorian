"""
Integration tests for health check and basic endpoints.

These tests verify that the API is properly configured and responding.
"""

import pytest
import os
from fastapi.testclient import TestClient




@pytest.mark.integration
class TestHealthEndpoint:
    """Test suite for health check endpoint."""
    
    def test_root_endpoint_returns_200(self, client: TestClient):
        """Test that the root endpoint returns a 200 status code."""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_root_endpoint_returns_correct_json(self, client: TestClient):
        """Test that the root endpoint returns the expected JSON structure."""
        response = client.get("/")
        data = response.json()
        
        assert "status" in data
        assert "message" in data
        assert data["status"] == "ok"
        assert data["message"] == "Gym Dorian API is running"
    
    def test_root_endpoint_content_type(self, client: TestClient):
        """Test that the root endpoint returns JSON content type."""
        response = client.get("/")
        assert "application/json" in response.headers["content-type"]


@pytest.mark.integration
class TestAPIConfiguration:
    """Test suite for API configuration and metadata."""
    
    def test_api_has_correct_title(self, client: TestClient):
        """Test that the API has the correct title in OpenAPI schema."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert data["info"]["title"] == "Gym Dorian API"
    
    def test_api_has_correct_version(self, client: TestClient):
        """Test that the API has the correct version in OpenAPI schema."""
        response = client.get("/openapi.json")
        data = response.json()
        assert data["info"]["version"] == "1.0.0"
    
    def test_docs_endpoint_is_accessible(self, client: TestClient):
        """Test that the API documentation is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc_endpoint_is_accessible(self, client: TestClient):
        """Test that the ReDoc documentation is accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200


@pytest.mark.integration
class TestDatabaseConnection:
    """Test suite for database connectivity."""
    
    def test_database_session_is_available(self, db_session):
        """Test that database session is properly configured."""
        assert db_session is not None
        assert db_session.is_active
    
    def test_can_query_database(self, db_session):
        """Test that we can execute queries against the database."""
        from app.models.exercise import Exercise
        
        # Should not raise an exception
        result = db_session.query(Exercise).all()
        assert isinstance(result, list)
