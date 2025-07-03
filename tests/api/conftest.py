"""
Test configuration and fixtures for API tests.
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

@pytest.fixture
def mock_query_service():
    """Mock query service for testing"""
    service = AsyncMock()
    return service

@pytest.fixture
def mock_ticket_service():
    """Mock ticket service for testing"""
    service = AsyncMock()
    return service

@pytest.fixture
def mock_customer_service():
    """Mock customer service for testing"""
    service = AsyncMock()
    return service

@pytest.fixture
def mock_feedback_service():
    """Mock feedback service for testing"""
    service = AsyncMock()
    return service

@pytest.fixture
def mock_analytics_service():
    """Mock analytics service for testing"""
    service = AsyncMock()
    return service

@pytest.fixture
def mock_kafka_client():
    """Mock Kafka MCP client for testing"""
    client = AsyncMock()
    client.call_tool.return_value = {
        "success": True,
        "message": "Operation completed successfully"
    }
    return client

@pytest.fixture
def test_app():
    """Create a test FastAPI application"""
    app = FastAPI(title="Test API")
    return app

@pytest.fixture
def test_client(test_app):
    """Create a test client"""
    return TestClient(test_app)
