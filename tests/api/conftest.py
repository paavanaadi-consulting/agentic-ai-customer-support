"""
Comprehensive test configuration for API tests.
Provides fixtures for FastAPI testing, mock services, and test data.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from fastapi import FastAPI
import uuid

from src.api.api_main import app
from src.api.schemas import (
    QueryRequest, QueryResponse, TicketRequest, TicketResponse,
    CustomerRequest, CustomerResponse, FeedbackRequest, FeedbackResponse,
    AnalyticsResponse, KafkaMessageRequest, KafkaMessageResponse,
    QueryType, Priority, TicketStatus
)
from src.services.query_service import QueryService
from src.services.ticket_service import TicketService
from src.services.customer_service import CustomerService
from src.services.feedback_service import FeedbackService
from src.services.analytics_service import AnalyticsService
from src.mcp.kafka_mcp_client import OptimizedKafkaMCPClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_query_service():
    """Mock QueryService for testing."""
    service = Mock(spec=QueryService)
    service.process_query = AsyncMock()
    service.get_query_by_id = AsyncMock()
    service.list_queries = AsyncMock()
    return service


@pytest.fixture
def mock_ticket_service():
    """Mock TicketService for testing."""
    service = Mock(spec=TicketService)
    service.create_ticket = AsyncMock()
    service.get_ticket_by_id = AsyncMock()
    service.list_tickets = AsyncMock()
    service.update_ticket_status = AsyncMock()
    service.assign_agent = AsyncMock()
    service.get_tickets_by_customer = AsyncMock()
    service.get_tickets_by_status = AsyncMock()
    return service


@pytest.fixture
def mock_customer_service():
    """Mock CustomerService for testing."""
    service = Mock(spec=CustomerService)
    service.create_customer = AsyncMock()
    service.get_customer_by_id = AsyncMock()
    service.list_customers = AsyncMock()
    service.update_customer = AsyncMock()
    service.delete_customer = AsyncMock()
    service.update_last_interaction = AsyncMock()
    service.increment_ticket_count = AsyncMock()
    return service


@pytest.fixture
def mock_feedback_service():
    """Mock FeedbackService for testing."""
    service = Mock(spec=FeedbackService)
    service.create_feedback = AsyncMock()
    service.get_feedback_by_id = AsyncMock()
    service.list_feedback = AsyncMock()
    service.get_feedback_by_customer = AsyncMock()
    service.get_average_rating = AsyncMock()
    return service


@pytest.fixture
def mock_analytics_service():
    """Mock AnalyticsService for testing."""
    service = Mock(spec=AnalyticsService)
    service.get_analytics = AsyncMock()
    service.get_query_metrics = AsyncMock()
    service.get_ticket_metrics = AsyncMock()
    service.get_customer_metrics = AsyncMock()
    return service


@pytest.fixture
def mock_kafka_client():
    """Mock OptimizedKafkaMCPClient for testing."""
    client = Mock(spec=OptimizedKafkaMCPClient)
    client.call_tool = AsyncMock()
    client.is_connected = True
    return client


# Test data fixtures
@pytest.fixture
def sample_query_request():
    """Sample QueryRequest for testing."""
    return QueryRequest(
        query="How can I reset my password?",
        customer_id="customer_123",
        query_type=QueryType.TECHNICAL,
        priority=Priority.MEDIUM,
        context={"source": "web_portal"},
        metadata={"ip_address": "192.168.1.1"}
    )


@pytest.fixture
def sample_query_response():
    """Sample QueryResponse for testing."""
    return QueryResponse(
        query_id="query_123",
        result="To reset your password, please visit the settings page and click 'Reset Password'.",
        confidence=0.95,
        success=True,
        agent_used="technical_agent",
        processing_time=1.25,
        suggestions=["Check your email for reset link", "Contact support if issues persist"],
        timestamp=datetime.utcnow()
    )


@pytest.fixture
def sample_ticket_request():
    """Sample TicketRequest for testing."""
    return TicketRequest(
        title="Unable to login to account",
        description="I have been trying to login but keep getting an error message.",
        customer_id="customer_123",
        category=QueryType.TECHNICAL,
        priority=Priority.HIGH,
        tags=["login", "authentication", "error"]
    )


@pytest.fixture
def sample_ticket_response():
    """Sample TicketResponse for testing."""
    return TicketResponse(
        ticket_id="ticket_123",
        title="Unable to login to account",
        status=TicketStatus.OPEN,
        customer_id="customer_123",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        priority=Priority.HIGH,
        category=QueryType.TECHNICAL,
        assigned_agent="agent_456"
    )


@pytest.fixture
def sample_customer_request():
    """Sample CustomerRequest for testing."""
    return CustomerRequest(
        name="John Doe",
        email="john.doe@example.com",
        phone="+1234567890",
        company="ACME Corp",
        metadata={"signup_source": "website"}
    )


@pytest.fixture
def sample_customer_response():
    """Sample CustomerResponse for testing."""
    return CustomerResponse(
        customer_id="customer_123",
        name="John Doe",
        email="john.doe@example.com",
        phone="+1234567890",
        company="ACME Corp",
        created_at=datetime.utcnow(),
        metadata={"signup_source": "website"},
        ticket_count=3,
        last_interaction=datetime.utcnow()
    )


@pytest.fixture
def sample_feedback_request():
    """Sample FeedbackRequest for testing."""
    return FeedbackRequest(
        customer_id="customer_123",
        rating=5,
        comment="Excellent service!",
        query_id="query_123",
        ticket_id="ticket_123"
    )


@pytest.fixture
def sample_feedback_response():
    """Sample FeedbackResponse for testing."""
    return FeedbackResponse(
        feedback_id="feedback_123",
        customer_id="customer_123",
        rating=5,
        comment="Excellent service!",
        query_id="query_123",
        ticket_id="ticket_123",
        created_at=datetime.utcnow()
    )


@pytest.fixture
def sample_analytics_response():
    """Sample AnalyticsResponse for testing."""
    return AnalyticsResponse(
        total_queries=1000,
        total_tickets=250,
        total_customers=500,
        avg_response_time=2.5,
        avg_rating=4.2,
        tickets_by_status={
            "open": 50,
            "in_progress": 75,
            "resolved": 100,
            "closed": 25
        },
        queries_by_type={
            "general": 400,
            "technical": 300,
            "billing": 200,
            "account": 100
        },
        customer_satisfaction_rate=0.85,
        resolution_rate=0.90
    )


@pytest.fixture
def sample_kafka_message_request():
    """Sample KafkaMessageRequest for testing."""
    return KafkaMessageRequest(
        topic="customer_queries",
        message={
            "query_id": "query_123",
            "customer_id": "customer_123",
            "query": "How can I reset my password?",
            "timestamp": datetime.utcnow().isoformat()
        },
        key="customer_123"
    )


@pytest.fixture
def sample_kafka_message_response():
    """Sample KafkaMessageResponse for testing."""
    return KafkaMessageResponse(
        success=True,
        topic="customer_queries",
        partition=0,
        offset=12345,
        timestamp=datetime.utcnow()
    )


@pytest.fixture
def mock_service_dependencies(
    mock_query_service,
    mock_ticket_service,
    mock_customer_service,
    mock_feedback_service,
    mock_analytics_service,
    mock_kafka_client
):
    """Fixture that patches all service dependencies."""
    from unittest.mock import patch
    
    with patch('src.api.dependencies.get_query_service_dep', return_value=mock_query_service), \
         patch('src.api.dependencies.get_ticket_service_dep', return_value=mock_ticket_service), \
         patch('src.api.dependencies.get_customer_service_dep', return_value=mock_customer_service), \
         patch('src.api.dependencies.get_feedback_service_dep', return_value=mock_feedback_service), \
         patch('src.api.dependencies.get_analytics_service_dep', return_value=mock_analytics_service), \
         patch('src.api.dependencies.get_kafka_client_dep', return_value=mock_kafka_client):
        yield {
            'query_service': mock_query_service,
            'ticket_service': mock_ticket_service,
            'customer_service': mock_customer_service,
            'feedback_service': mock_feedback_service,
            'analytics_service': mock_analytics_service,
            'kafka_client': mock_kafka_client
        }


# Utility functions for test data generation
def generate_test_customer_id() -> str:
    """Generate a test customer ID."""
    return f"test_customer_{uuid.uuid4().hex[:8]}"


def generate_test_query_id() -> str:
    """Generate a test query ID."""
    return f"test_query_{uuid.uuid4().hex[:8]}"


def generate_test_ticket_id() -> str:
    """Generate a test ticket ID."""
    return f"test_ticket_{uuid.uuid4().hex[:8]}"


def create_test_query_response(query_id: str = None, customer_id: str = None) -> QueryResponse:
    """Create a test QueryResponse with optional overrides."""
    return QueryResponse(
        query_id=query_id or generate_test_query_id(),
        result="Test response",
        confidence=0.9,
        success=True,
        agent_used="test_agent",
        processing_time=1.0,
        suggestions=["Test suggestion"],
        timestamp=datetime.utcnow()
    )


def create_test_ticket_response(ticket_id: str = None, customer_id: str = None) -> TicketResponse:
    """Create a test TicketResponse with optional overrides."""
    return TicketResponse(
        ticket_id=ticket_id or generate_test_ticket_id(),
        title="Test ticket",
        status=TicketStatus.OPEN,
        customer_id=customer_id or generate_test_customer_id(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        priority=Priority.MEDIUM,
        category=QueryType.GENERAL,
        assigned_agent=None
    )


# Error testing fixtures
@pytest.fixture
def http_error_scenarios():
    """Common HTTP error scenarios for testing."""
    return {
        'not_found': {
            'status_code': 404,
            'detail': 'Resource not found'
        },
        'validation_error': {
            'status_code': 422,
            'detail': 'Validation error'
        },
        'internal_error': {
            'status_code': 500,
            'detail': 'Internal server error'
        },
        'service_unavailable': {
            'status_code': 503,
            'detail': 'Service unavailable'
        }
    }


# Performance testing fixtures
@pytest.fixture
def performance_test_data():
    """Test data for performance testing."""
    return {
        'small_dataset': 10,
        'medium_dataset': 100,
        'large_dataset': 1000,
        'response_time_threshold': 2.0,  # seconds
        'concurrent_requests': 10
    }