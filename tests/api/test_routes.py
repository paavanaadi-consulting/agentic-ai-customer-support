import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime
import uuid

from src.api.routes import router
from src.api.schemas import (
    QueryRequest, QueryResponse, TicketRequest, TicketResponse,
    CustomerRequest, CustomerResponse, FeedbackRequest, FeedbackResponse,
    AnalyticsResponse, QueryType, Priority, TicketStatus
)


def create_test_app():
    """Create a test FastAPI application"""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return app


@pytest.fixture
def client():
    app = create_test_app()
    return TestClient(app)


@pytest.fixture
def mock_query_service():
    """Mock query service for testing"""
    service = AsyncMock()
    service.process_query.return_value = QueryResponse(
        query_id=str(uuid.uuid4()),
        result="Test response",
        confidence=0.95,
        success=True,
        agent_used="test_agent",
        processing_time=0.5,
        suggestions=["suggestion1", "suggestion2"],
        timestamp=datetime.utcnow()
    )
    service.get_query_by_id.return_value = None  # Default to not found
    service.list_queries.return_value = []
    return service


@pytest.fixture
def mock_ticket_service():
    """Mock ticket service for testing"""
    service = AsyncMock()
    service.create_ticket.return_value = TicketResponse(
        ticket_id=str(uuid.uuid4()),
        title="Test Ticket",
        status=TicketStatus.OPEN,
        customer_id="test_customer_id",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        priority=Priority.MEDIUM,
        category=QueryType.GENERAL,
        assigned_agent=None
    )
    service.get_ticket_by_id.return_value = None
    service.update_ticket_status.return_value = None
    service.list_tickets.return_value = []
    return service


@pytest.fixture
def mock_customer_service():
    """Mock customer service for testing"""
    service = AsyncMock()
    service.create_customer.return_value = CustomerResponse(
        customer_id=str(uuid.uuid4()),
        name="Test Customer",
        email="test@example.com",
        phone="+1234567890",
        company="Test Company",
        created_at=datetime.utcnow(),
        metadata={},
        ticket_count=0,
        last_interaction=None
    )
    service.get_customer_by_id.return_value = None
    service.list_customers.return_value = []
    service.update_last_interaction.return_value = None
    service.increment_ticket_count.return_value = None
    return service


@pytest.fixture
def mock_feedback_service():
    """Mock feedback service for testing"""
    service = AsyncMock()
    service.submit_feedback.return_value = FeedbackResponse(
        feedback_id=str(uuid.uuid4()),
        customer_id="test_customer_id",
        rating=5,
        comment="Great service!",
        query_id=None,
        ticket_id=None,
        created_at=datetime.utcnow()
    )
    service.list_feedback.return_value = []
    return service


@pytest.fixture
def mock_analytics_service():
    """Mock analytics service for testing"""
    service = AsyncMock()
    service.get_system_analytics.return_value = AnalyticsResponse(
        total_queries=100,
        total_tickets=50,
        total_customers=25,
        avg_response_time=1.2,
        avg_rating=4.5,
        resolution_rate=0.85,
        customer_satisfaction=0.92,
        popular_categories={"general": 40, "technical": 35, "billing": 25},
        timestamp=datetime.utcnow()
    )
    service.get_performance_metrics.return_value = {
        "cpu_usage": 45.5,
        "memory_usage": 60.2,
        "response_times": {"p50": 0.8, "p95": 2.1, "p99": 5.2}
    }
    service.get_customer_insights.return_value = {
        "new_customers_today": 5,
        "active_sessions": 12,
        "top_issues": ["login", "billing", "technical"]
    }
    return service


@pytest.fixture(autouse=True)
def mock_dependencies(mock_query_service, mock_ticket_service, mock_customer_service, 
                     mock_feedback_service, mock_analytics_service):
    """Auto-use fixture to mock all service dependencies"""
    with patch('src.api.routes.get_query_service_dep', return_value=mock_query_service), \
         patch('src.api.routes.get_ticket_service_dep', return_value=mock_ticket_service), \
         patch('src.api.routes.get_customer_service_dep', return_value=mock_customer_service), \
         patch('src.api.routes.get_feedback_service_dep', return_value=mock_feedback_service), \
         patch('src.api.routes.get_analytics_service_dep', return_value=mock_analytics_service):
        yield


class TestQueryEndpoints:
    """Test query-related endpoints"""

    def test_process_query_success(self, client, mock_query_service):
        """Test successful query processing"""
        request_data = {
            "query": "How do I reset my password?",
            "customer_id": "test_customer_id",
            "query_type": "technical",
            "priority": "medium"
        }
        
        response = client.post("/api/v1/queries", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["result"] == "Test response"
        assert data["success"] is True
        assert data["confidence"] == 0.95
        assert data["agent_used"] == "test_agent"

    def test_process_query_invalid_data(self, client):
        """Test query processing with invalid data"""
        request_data = {
            "query": "",  # Empty query
            "customer_id": "test_customer_id"
        }
        
        response = client.post("/api/v1/queries", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_get_query_by_id_not_found(self, client):
        """Test getting a query that doesn't exist"""
        response = client.get("/api/v1/queries/nonexistent_id")
        assert response.status_code == 404

    def test_get_query_by_id_success(self, client, mock_query_service):
        """Test successfully getting a query by ID"""
        query_id = str(uuid.uuid4())
        mock_query_service.get_query_by_id.return_value = QueryResponse(
            query_id=query_id,
            result="Test response",
            confidence=0.95,
            success=True,
            agent_used="test_agent",
            processing_time=0.5,
            suggestions=[],
            timestamp=datetime.utcnow()
        )
        
        response = client.get(f"/api/v1/queries/{query_id}")
        assert response.status_code == 200
        assert response.json()["query_id"] == query_id

    def test_list_queries(self, client, mock_query_service):
        """Test listing queries with filters"""
        response = client.get("/api/v1/queries?customer_id=test_customer&limit=5")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestTicketEndpoints:
    """Test ticket-related endpoints"""

    def test_create_ticket_success(self, client, mock_ticket_service):
        """Test successful ticket creation"""
        request_data = {
            "title": "Password Reset Issue",
            "description": "Cannot reset password",
            "customer_id": "test_customer_id",
            "category": "technical",
            "priority": "high",
            "tags": ["password", "login"]
        }
        
        response = client.post("/api/v1/tickets", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Test Ticket"
        assert data["status"] == "open"

    def test_get_ticket_by_id_not_found(self, client):
        """Test getting a ticket that doesn't exist"""
        response = client.get("/api/v1/tickets/nonexistent_id")
        assert response.status_code == 404

    def test_update_ticket_status_not_found(self, client):
        """Test updating status of non-existent ticket"""
        response = client.put("/api/v1/tickets/nonexistent_id/status?status=resolved")
        assert response.status_code == 404

    def test_update_ticket_status_success(self, client, mock_ticket_service):
        """Test successful ticket status update"""
        ticket_id = str(uuid.uuid4())
        mock_ticket_service.update_ticket_status.return_value = TicketResponse(
            ticket_id=ticket_id,
            title="Test Ticket",
            status=TicketStatus.RESOLVED,
            customer_id="test_customer_id",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            priority=Priority.MEDIUM,
            category=QueryType.GENERAL,
            assigned_agent=None
        )
        
        response = client.put(f"/api/v1/tickets/{ticket_id}/status?status=resolved")
        assert response.status_code == 200
        assert response.json()["status"] == "resolved"

    def test_list_tickets(self, client):
        """Test listing tickets with filters"""
        response = client.get("/api/v1/tickets?status=open&priority=high&limit=10")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestCustomerEndpoints:
    """Test customer-related endpoints"""

    def test_create_customer_success(self, client, mock_customer_service):
        """Test successful customer creation"""
        request_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "company": "Acme Corp",
            "metadata": {"source": "website"}
        }
        
        response = client.post("/api/v1/customers", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Test Customer"
        assert data["email"] == "test@example.com"

    def test_create_customer_invalid_email(self, client):
        """Test customer creation with invalid email"""
        request_data = {
            "name": "John Doe",
            "email": "invalid-email"
        }
        
        response = client.post("/api/v1/customers", json=request_data)
        assert response.status_code == 422

    def test_get_customer_by_id_not_found(self, client):
        """Test getting a customer that doesn't exist"""
        response = client.get("/api/v1/customers/nonexistent_id")
        assert response.status_code == 404

    def test_list_customers(self, client):
        """Test listing customers"""
        response = client.get("/api/v1/customers?limit=20")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestFeedbackEndpoints:
    """Test feedback-related endpoints"""

    def test_submit_feedback_success(self, client, mock_feedback_service):
        """Test successful feedback submission"""
        request_data = {
            "customer_id": "test_customer_id",
            "rating": 5,
            "comment": "Excellent service!",
            "query_id": "test_query_id"
        }
        
        response = client.post("/api/v1/feedback", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["rating"] == 5
        assert data["comment"] == "Great service!"

    def test_submit_feedback_invalid_rating(self, client):
        """Test feedback submission with invalid rating"""
        request_data = {
            "customer_id": "test_customer_id",
            "rating": 6  # Invalid rating (should be 1-5)
        }
        
        response = client.post("/api/v1/feedback", json=request_data)
        assert response.status_code == 422

    def test_list_feedback(self, client):
        """Test listing feedback with filters"""
        response = client.get("/api/v1/feedback?rating=5&limit=15")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAnalyticsEndpoints:
    """Test analytics-related endpoints"""

    def test_get_analytics(self, client, mock_analytics_service):
        """Test getting system analytics"""
        response = client.get("/api/v1/analytics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_queries"] == 100
        assert data["total_tickets"] == 50
        assert data["avg_response_time"] == 1.2

    def test_get_performance_metrics(self, client, mock_analytics_service):
        """Test getting performance metrics"""
        response = client.get("/api/v1/analytics/performance")
        assert response.status_code == 200
        
        data = response.json()
        assert "cpu_usage" in data
        assert "memory_usage" in data
        assert "response_times" in data

    def test_get_customer_insights(self, client, mock_analytics_service):
        """Test getting customer insights"""
        response = client.get("/api/v1/analytics/customers")
        assert response.status_code == 200
        
        data = response.json()
        assert "new_customers_today" in data
        assert "active_sessions" in data
        assert "top_issues" in data


class TestStatusEndpoints:
    """Test status and health endpoints"""

    def test_get_api_status(self, client, mock_analytics_service):
        """Test getting API status"""
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "operational"
        assert data["version"] == "1.0.0"
        assert "uptime" in data
        assert "endpoints" in data
        assert "performance" in data
