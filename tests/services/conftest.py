"""
Shared test fixtures and configuration for services tests.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.services.query_service import QueryService
from src.services.ticket_service import TicketService
from src.services.customer_service import CustomerService
from src.services.feedback_service import FeedbackService
from src.services.analytics_service import AnalyticsService
from src.services.service_factory import ServiceFactory
from src.api.schemas import (
    QueryRequest, QueryResponse, QueryType, Priority,
    TicketRequest, TicketResponse, TicketStatus,
    CustomerRequest, CustomerResponse,
    FeedbackRequest, FeedbackResponse
)
from src.mcp.postgres_mcp_client import OptimizedPostgreSQLMCPClient
from src.mcp.kafka_mcp_client import OptimizedKafkaMCPClient


# Global fixtures for all service tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_postgres_mcp_client():
    """Create a mocked PostgreSQL MCP client for testing."""
    mock_client = AsyncMock(spec=OptimizedPostgreSQLMCPClient)
    
    # Setup default return values
    mock_client.create_customer.return_value = {
        "customer_id": "test_customer_123",
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "phone": "+1234567890",
        "company": None,
        "created_at": datetime.utcnow(),
        "status": "active",
        "tier": "standard",
        "last_interaction": None
    }
    
    mock_client.get_customer_by_id.return_value = None
    mock_client.update_customer.return_value = None
    mock_client.get_customers.return_value = []
    
    mock_client.create_ticket.return_value = {
        "ticket_id": "test_ticket_123",
        "customer_id": "test_customer_123",
        "subject": "Test Ticket",
        "description": "Test description",
        "priority": "medium",
        "status": "open",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "agent_name": None
    }
    
    mock_client.get_ticket_by_id.return_value = None
    mock_client.update_ticket_status.return_value = None
    
    mock_client.get_analytics.return_value = {
        "total_tickets": 0,
        "total_customers": 0,
        "avg_resolution_hours": 0.0,
        "avg_satisfaction": 0.0,
        "open_tickets": 0,
        "resolved_tickets": 0,
        "high_priority": 0
    }
    
    return mock_client


@pytest.fixture
def mock_kafka_mcp_client():
    """Create a mocked Kafka MCP client for testing."""
    mock_client = AsyncMock(spec=OptimizedKafkaMCPClient)
    
    # Setup default return values
    mock_client.call_tool.return_value = {
        'success': True,
        'result': {
            'topic': 'test_topic',
            'partition': 0,
            'offset': 0
        }
    }
    
    return mock_client


@pytest.fixture
def sample_query_requests():
    """Create sample query requests for testing."""
    return [
        QueryRequest(
            query="I can't log into my account",
            customer_id="customer_1",
            query_type=QueryType.TECHNICAL,
            priority=Priority.HIGH
        ),
        QueryRequest(
            query="Question about my bill",
            customer_id="customer_2",
            query_type=QueryType.BILLING,
            priority=Priority.MEDIUM
        ),
        QueryRequest(
            query="How do I update my profile?",
            customer_id="customer_3",
            query_type=QueryType.ACCOUNT,
            priority=Priority.LOW
        ),
        QueryRequest(
            query="I'm unhappy with the service",
            customer_id="customer_4",
            query_type=QueryType.COMPLAINT,
            priority=Priority.HIGH
        ),
        QueryRequest(
            query="General question about features",
            customer_id="customer_5",
            query_type=QueryType.GENERAL,
            priority=Priority.MEDIUM
        )
    ]


@pytest.fixture
def sample_customer_requests():
    """Create sample customer requests for testing."""
    return [
        CustomerRequest(
            name="John Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            company="TechCorp",
            metadata={"source": "web"}
        ),
        CustomerRequest(
            name="Jane Smith",
            email="jane.smith@company.com",
            phone="+0987654321",
            company="BusinessInc",
            metadata={"source": "mobile", "campaign": "spring2024"}
        ),
        CustomerRequest(
            name="Bob Johnson",
            email="bob@personal.com",
            metadata={"source": "referral"}
        ),
        CustomerRequest(
            name="Alice Williams",
            email="alice.williams@enterprise.com",
            phone="+1122334455",
            company="Enterprise Solutions",
            metadata={"source": "api", "tier": "premium"}
        ),
        CustomerRequest(
            name="Charlie Brown",
            email="charlie.brown@startup.io",
            company="StartupCo",
            metadata={"source": "web", "beta_user": True}
        )
    ]


@pytest.fixture
def sample_ticket_requests():
    """Create sample ticket requests for testing."""
    return [
        TicketRequest(
            title="Login Issue",
            description="Cannot access account after password reset",
            customer_id="customer_1",
            category="technical",
            priority=Priority.HIGH,
            tags=["login", "password", "urgent"]
        ),
        TicketRequest(
            title="Billing Question",
            description="Unexpected charge on my account",
            customer_id="customer_2",
            category="billing",
            priority=Priority.MEDIUM,
            tags=["billing", "charge"]
        ),
        TicketRequest(
            title="Feature Request",
            description="Would like to see dark mode option",
            customer_id="customer_3",
            category="feature",
            priority=Priority.LOW,
            tags=["feature", "ui", "enhancement"]
        ),
        TicketRequest(
            title="Service Complaint",
            description="Very poor customer service experience",
            customer_id="customer_4",
            category="complaint",
            priority=Priority.HIGH,
            tags=["complaint", "service", "escalate"]
        ),
        TicketRequest(
            title="Account Update",
            description="Need to update company information",
            customer_id="customer_5",
            category="account",
            priority=Priority.MEDIUM,
            tags=["account", "update"]
        )
    ]


@pytest.fixture
def sample_feedback_requests():
    """Create sample feedback requests for testing."""
    return [
        FeedbackRequest(
            customer_id="customer_1",
            rating=5,
            comment="Excellent service! Very satisfied with the support.",
            query_id="query_1",
            ticket_id="ticket_1"
        ),
        FeedbackRequest(
            customer_id="customer_2",
            rating=4,
            comment="Good experience overall, minor delay but helpful.",
            query_id="query_2"
        ),
        FeedbackRequest(
            customer_id="customer_3",
            rating=3,
            comment="Average service, could be improved.",
            ticket_id="ticket_3"
        ),
        FeedbackRequest(
            customer_id="customer_4",
            rating=2,
            comment="Poor response time and unhelpful answers.",
            query_id="query_4",
            ticket_id="ticket_4"
        ),
        FeedbackRequest(
            customer_id="customer_5",
            rating=1,
            comment="Terrible experience, very disappointed.",
            ticket_id="ticket_5"
        )
    ]


@pytest.fixture
def sample_analytics_data():
    """Create sample analytics data for testing."""
    return {
        "total_queries": 150,
        "total_tickets": 75,
        "total_customers": 100,
        "total_feedback": 80,
        "avg_response_time": 2.5,
        "avg_rating": 3.8,
        "customer_satisfaction_rate": 0.75,
        "resolution_rate": 0.85,
        "tickets_by_status": {
            "open": 25,
            "in_progress": 20,
            "resolved": 20,
            "closed": 10
        },
        "queries_by_type": {
            "technical": 60,
            "billing": 40,
            "account": 25,
            "complaint": 15,
            "general": 10
        },
        "customers_by_tier": {
            "standard": 70,
            "premium": 20,
            "enterprise": 10
        },
        "feedback_by_rating": {
            1: 8,
            2: 12,
            3: 20,
            4: 25,
            5: 15
        }
    }


# Test utilities
class TestDataGenerator:
    """Utility class for generating test data."""
    
    @staticmethod
    def generate_customers(count: int = 10) -> List[Dict[str, Any]]:
        """Generate customer data for testing."""
        customers = []
        for i in range(count):
            customers.append({
                "customer_id": f"customer_{i}",
                "first_name": f"Customer",
                "last_name": f"User{i}",
                "email": f"customer{i}@test.com",
                "phone": f"+{1000000000 + i}",
                "company": f"Company{i}" if i % 3 == 0 else None,
                "created_at": datetime.utcnow() - timedelta(days=i),
                "status": "active",
                "tier": "enterprise" if i % 5 == 0 else "standard",
                "last_interaction": datetime.utcnow() - timedelta(hours=i) if i % 2 == 0 else None
            })
        return customers
    
    @staticmethod
    def generate_queries(count: int = 20) -> List[Dict[str, Any]]:
        """Generate query data for testing."""
        queries = []
        query_types = list(QueryType)
        priorities = list(Priority)
        
        for i in range(count):
            queries.append({
                "query_id": f"query_{i}",
                "customer_id": f"customer_{i % 10}",
                "query": f"Test query {i}",
                "query_type": query_types[i % len(query_types)],
                "priority": priorities[i % len(priorities)],
                "result": f"Response to query {i}",
                "agent_used": f"agent_{i % 5}",
                "processing_time": 1.0 + (i % 5),
                "timestamp": datetime.utcnow() - timedelta(hours=i),
                "context": {"test": True},
                "metadata": {"source": "test"}
            })
        return queries
    
    @staticmethod
    def generate_tickets(count: int = 15) -> List[Dict[str, Any]]:
        """Generate ticket data for testing."""
        tickets = []
        statuses = list(TicketStatus)
        priorities = list(Priority)
        categories = ["technical", "billing", "account", "general", "complaint"]
        
        for i in range(count):
            tickets.append({
                "ticket_id": f"ticket_{i}",
                "customer_id": f"customer_{i % 10}",
                "title": f"Test Ticket {i}",
                "description": f"Description for ticket {i}",
                "category": categories[i % len(categories)],
                "priority": priorities[i % len(priorities)],
                "status": statuses[i % len(statuses)],
                "created_at": datetime.utcnow() - timedelta(days=i),
                "updated_at": datetime.utcnow() - timedelta(hours=i),
                "tags": [f"tag{i}", f"test"],
                "assigned_agent": f"agent_{i % 3}" if i % 2 == 0 else None
            })
        return tickets
    
    @staticmethod
    def generate_feedback(count: int = 25) -> List[Dict[str, Any]]:
        """Generate feedback data for testing."""
        feedback_list = []
        sentiments = ["positive", "neutral", "negative"]
        categories = ["praise", "suggestion", "complaint", "neutral"]
        
        for i in range(count):
            rating = (i % 5) + 1
            feedback_list.append({
                "feedback_id": f"feedback_{i}",
                "customer_id": f"customer_{i % 10}",
                "rating": rating,
                "comment": f"Test feedback comment {i}",
                "query_id": f"query_{i}" if i % 3 == 0 else None,
                "ticket_id": f"ticket_{i}" if i % 2 == 0 else None,
                "created_at": datetime.utcnow() - timedelta(hours=i),
                "sentiment": sentiments[i % len(sentiments)],
                "category": categories[i % len(categories)],
                "processed": i % 4 == 0
            })
        return feedback_list


# Test helpers
def assert_response_structure(response, expected_type):
    """Assert that a response has the expected structure."""
    assert isinstance(response, expected_type)
    assert hasattr(response, 'created_at') or hasattr(response, 'timestamp')
    
    if hasattr(response, 'customer_id'):
        assert response.customer_id is not None
    
    if hasattr(response, 'id') or hasattr(response, 'query_id') or hasattr(response, 'ticket_id') or hasattr(response, 'feedback_id'):
        # Has some kind of ID field
        pass


def assert_valid_timestamp(timestamp):
    """Assert that a timestamp is valid and recent."""
    assert isinstance(timestamp, datetime)
    assert timestamp <= datetime.utcnow()
    assert timestamp >= datetime.utcnow() - timedelta(hours=1)  # Should be recent


def assert_valid_uuid_format(uuid_string: str):
    """Assert that a string is a valid UUID format."""
    import uuid
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


# Performance testing helpers
class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(self, max_time: float = 1.0):
        self.max_time = max_time
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.end_time = time.time()
        elapsed = self.end_time - self.start_time
        assert elapsed < self.max_time, f"Operation took {elapsed:.3f}s, expected < {self.max_time}s"
    
    @property
    def elapsed_time(self):
        """Get elapsed time if operation is complete."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


# Integration test helpers
async def create_test_scenario_data(service_factory: ServiceFactory):
    """Create a complete test scenario with realistic data."""
    query_service = service_factory.query_service
    customer_service = service_factory.customer_service
    ticket_service = service_factory.ticket_service
    feedback_service = service_factory.feedback_service
    
    # Create customers
    customers = []
    for i in range(5):
        request = CustomerRequest(
            name=f"Test Customer {i}",
            email=f"customer{i}@test.com",
            company=f"Company {i}" if i % 2 == 0 else None
        )
        customer = await customer_service.create_customer(request)
        customers.append(customer)
    
    # Create queries
    queries = []
    query_types = [QueryType.TECHNICAL, QueryType.BILLING, QueryType.ACCOUNT, QueryType.GENERAL, QueryType.COMPLAINT]
    for i, customer in enumerate(customers):
        request = QueryRequest(
            query=f"Test query {i}",
            customer_id=customer.customer_id,
            query_type=query_types[i % len(query_types)]
        )
        query = await query_service.process_query(request)
        queries.append(query)
    
    # Create tickets
    tickets = []
    for i, customer in enumerate(customers[:3]):  # Only first 3 customers get tickets
        request = TicketRequest(
            title=f"Test Ticket {i}",
            description=f"Description for ticket {i}",
            customer_id=customer.customer_id,
            category="technical" if i % 2 == 0 else "billing"
        )
        ticket = await ticket_service.create_ticket(request)
        tickets.append(ticket)
    
    # Create feedback
    feedback_list = []
    for i, (customer, query) in enumerate(zip(customers, queries)):
        request = FeedbackRequest(
            customer_id=customer.customer_id,
            rating=(i % 5) + 1,
            comment=f"Test feedback {i}",
            query_id=query.query_id
        )
        feedback = await feedback_service.submit_feedback(request)
        feedback_list.append(feedback)
    
    return {
        "customers": customers,
        "queries": queries,
        "tickets": tickets,
        "feedback": feedback_list
    }


# Async test utilities
async def wait_for_async_completion(coro, timeout: float = 5.0):
    """Wait for async operation to complete with timeout."""
    import asyncio
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        pytest.fail(f"Async operation timed out after {timeout} seconds")


# Mock data validators
def validate_customer_data(customer_data: Dict[str, Any]) -> bool:
    """Validate customer data structure."""
    required_fields = ["customer_id", "name", "email"]
    return all(field in customer_data for field in required_fields)


def validate_query_data(query_data: Dict[str, Any]) -> bool:
    """Validate query data structure."""
    required_fields = ["query_id", "customer_id", "query", "result"]
    return all(field in query_data for field in required_fields)


def validate_ticket_data(ticket_data: Dict[str, Any]) -> bool:
    """Validate ticket data structure."""
    required_fields = ["ticket_id", "customer_id", "title", "status"]
    return all(field in ticket_data for field in required_fields)


def validate_feedback_data(feedback_data: Dict[str, Any]) -> bool:
    """Validate feedback data structure."""
    required_fields = ["feedback_id", "customer_id", "rating"]
    return all(field in feedback_data for field in required_fields)
