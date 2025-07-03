import pytest
from datetime import datetime
from pydantic import ValidationError
import uuid

from src.api.schemas import (
    QueryRequest, QueryResponse, TicketRequest, TicketResponse,
    CustomerRequest, CustomerResponse, FeedbackRequest, FeedbackResponse,
    AnalyticsResponse, QueryType, Priority, TicketStatus,
    KafkaMessageRequest, KafkaMessageResponse,
    KafkaTopicRequest, StreamingQueryRequest
)


class TestEnums:
    """Test enum validations"""

    def test_query_type_values(self):
        """Test QueryType enum values"""
        assert QueryType.GENERAL == "general"
        assert QueryType.TECHNICAL == "technical"
        assert QueryType.BILLING == "billing"
        assert QueryType.ACCOUNT == "account"
        assert QueryType.COMPLAINT == "complaint"

    def test_priority_values(self):
        """Test Priority enum values"""
        assert Priority.LOW == "low"
        assert Priority.MEDIUM == "medium"
        assert Priority.HIGH == "high"
        assert Priority.CRITICAL == "critical"

    def test_ticket_status_values(self):
        """Test TicketStatus enum values"""
        assert TicketStatus.OPEN == "open"
        assert TicketStatus.IN_PROGRESS == "in_progress"
        assert TicketStatus.PENDING == "pending"
        assert TicketStatus.RESOLVED == "resolved"
        assert TicketStatus.CLOSED == "closed"


class TestRequestSchemas:
    """Test request schema validations"""

    def test_query_request_valid(self):
        """Test valid QueryRequest"""
        data = {
            "query": "How do I reset my password?",
            "customer_id": "customer_123",
            "query_type": "technical",
            "priority": "medium",
            "context": {"page": "login"},
            "metadata": {"source": "website"}
        }
        
        request = QueryRequest(**data)
        assert request.query == "How do I reset my password?"
        assert request.customer_id == "customer_123"
        assert request.query_type == QueryType.TECHNICAL
        assert request.priority == Priority.MEDIUM
        assert request.context == {"page": "login"}
        assert request.metadata == {"source": "website"}

    def test_query_request_minimal(self):
        """Test QueryRequest with minimal required fields"""
        data = {
            "query": "Test query",
            "customer_id": "customer_123"
        }
        
        request = QueryRequest(**data)
        assert request.query == "Test query"
        assert request.customer_id == "customer_123"
        assert request.query_type == QueryType.GENERAL  # Default
        assert request.priority == Priority.MEDIUM  # Default
        assert request.context == {}  # Default
        assert request.metadata == {}  # Default

    def test_query_request_empty_query(self):
        """Test QueryRequest with empty query"""
        data = {
            "query": "",
            "customer_id": "customer_123"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(**data)
        
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_ticket_request_valid(self):
        """Test valid TicketRequest"""
        data = {
            "title": "Cannot access account",
            "description": "Customer cannot log into their account",
            "customer_id": "customer_123",
            "category": "account",
            "priority": "high",
            "tags": ["login", "access", "urgent"]
        }
        
        request = TicketRequest(**data)
        assert request.title == "Cannot access account"
        assert request.description == "Customer cannot log into their account"
        assert request.customer_id == "customer_123"
        assert request.category == QueryType.ACCOUNT
        assert request.priority == Priority.HIGH
        assert request.tags == ["login", "access", "urgent"]

    def test_customer_request_valid(self):
        """Test valid CustomerRequest"""
        data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "company": "Acme Corp",
            "metadata": {"source": "referral", "campaign": "summer2024"}
        }
        
        request = CustomerRequest(**data)
        assert request.name == "John Doe"
        assert request.email == "john.doe@example.com"
        assert request.phone == "+1-555-123-4567"
        assert request.company == "Acme Corp"
        assert request.metadata == {"source": "referral", "campaign": "summer2024"}

    def test_customer_request_invalid_email(self):
        """Test CustomerRequest with invalid email"""
        data = {
            "name": "John Doe",
            "email": "invalid-email"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            CustomerRequest(**data)
        
        assert "value is not a valid email address" in str(exc_info.value)

    def test_feedback_request_valid(self):
        """Test valid FeedbackRequest"""
        data = {
            "customer_id": "customer_123",
            "rating": 5,
            "comment": "Excellent service!",
            "query_id": "query_456",
            "ticket_id": "ticket_789"
        }
        
        request = FeedbackRequest(**data)
        assert request.customer_id == "customer_123"
        assert request.rating == 5
        assert request.comment == "Excellent service!"
        assert request.query_id == "query_456"
        assert request.ticket_id == "ticket_789"

    def test_feedback_request_invalid_rating(self):
        """Test FeedbackRequest with invalid rating"""
        data = {
            "customer_id": "customer_123",
            "rating": 6  # Should be 1-5
        }
        
        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(**data)
        
        assert "Input should be less than or equal to 5" in str(exc_info.value)

    def test_feedback_request_zero_rating(self):
        """Test FeedbackRequest with zero rating"""
        data = {
            "customer_id": "customer_123",
            "rating": 0  # Should be 1-5
        }
        
        with pytest.raises(ValidationError) as exc_info:
            FeedbackRequest(**data)
        
        assert "Input should be greater than or equal to 1" in str(exc_info.value)


class TestResponseSchemas:
    """Test response schema validations"""

    def test_query_response_valid(self):
        """Test valid QueryResponse"""
        data = {
            "query_id": str(uuid.uuid4()),
            "result": "To reset your password, go to Settings > Security",
            "confidence": 0.95,
            "success": True,
            "agent_used": "password_reset_agent",
            "processing_time": 1.23,
            "suggestions": ["Change password", "Enable 2FA"],
            "timestamp": datetime.utcnow()
        }
        
        response = QueryResponse(**data)
        assert response.query_id == data["query_id"]
        assert response.result == data["result"]
        assert response.confidence == 0.95
        assert response.success is True
        assert response.agent_used == "password_reset_agent"
        assert response.processing_time == 1.23
        assert response.suggestions == ["Change password", "Enable 2FA"]

    def test_query_response_confidence_bounds(self):
        """Test QueryResponse confidence bounds"""
        # Test confidence too high
        with pytest.raises(ValidationError):
            QueryResponse(
                query_id="test",
                result="test",
                confidence=1.5,  # Should be <= 1.0
                success=True,
                agent_used="test",
                processing_time=1.0
            )
        
        # Test confidence too low
        with pytest.raises(ValidationError):
            QueryResponse(
                query_id="test",
                result="test",
                confidence=-0.1,  # Should be >= 0.0
                success=True,
                agent_used="test",
                processing_time=1.0
            )

    def test_ticket_response_valid(self):
        """Test valid TicketResponse"""
        now = datetime.utcnow()
        data = {
            "ticket_id": str(uuid.uuid4()),
            "title": "Password Reset Issue",
            "status": "open",
            "customer_id": "customer_123",
            "created_at": now,
            "updated_at": now,
            "priority": "high",
            "category": "technical",
            "assigned_agent": "agent_456"
        }
        
        response = TicketResponse(**data)
        assert response.ticket_id == data["ticket_id"]
        assert response.title == "Password Reset Issue"
        assert response.status == TicketStatus.OPEN
        assert response.priority == Priority.HIGH
        assert response.category == QueryType.TECHNICAL

    def test_customer_response_valid(self):
        """Test valid CustomerResponse"""
        now = datetime.utcnow()
        data = {
            "customer_id": str(uuid.uuid4()),
            "name": "Jane Smith",
            "email": "jane@example.com",
            "phone": "+1-555-987-6543",
            "company": "Tech Solutions Inc",
            "created_at": now,
            "metadata": {"tier": "premium"},
            "ticket_count": 3,
            "last_interaction": now
        }
        
        response = CustomerResponse(**data)
        assert response.customer_id == data["customer_id"]
        assert response.name == "Jane Smith"
        assert response.email == "jane@example.com"
        assert response.ticket_count == 3

    def test_analytics_response_valid(self):
        """Test valid AnalyticsResponse"""
        now = datetime.utcnow()
        data = {
            "total_queries": 1500,
            "total_tickets": 750,
            "total_customers": 300,
            "avg_response_time": 2.5,
            "avg_rating": 4.2,
            "resolution_rate": 0.87,
            "customer_satisfaction": 0.92,
            "popular_categories": {
                "technical": 45,
                "billing": 30,
                "general": 25
            },
            "timestamp": now
        }
        
        response = AnalyticsResponse(**data)
        assert response.total_queries == 1500
        assert response.avg_response_time == 2.5
        assert response.resolution_rate == 0.87
        assert response.popular_categories == data["popular_categories"]


class TestKafkaSchemas:
    """Test Kafka-related schemas"""

    def test_kafka_message_request_valid(self):
        """Test valid KafkaMessageRequest"""
        data = {
            "topic": "customer_queries",
            "message": {
                "query": "How do I cancel my subscription?",
                "customer_id": "customer_123",
                "timestamp": datetime.utcnow().isoformat()
            },
            "key": "customer_123"
        }
        
        request = KafkaMessageRequest(**data)
        assert request.topic == "customer_queries"
        assert request.message["query"] == "How do I cancel my subscription?"
        assert request.key == "customer_123"

    def test_kafka_topic_request_valid(self):
        """Test valid KafkaTopicRequest"""
        data = {
            "topic_name": "agent_responses",
            "num_partitions": 3,
            "replication_factor": 2,
            "config": {
                "cleanup.policy": "delete",
                "retention.ms": "604800000"
            }
        }
        
        request = KafkaTopicRequest(**data)
        assert request.topic_name == "agent_responses"
        assert request.num_partitions == 3
        assert request.replication_factor == 2
        assert request.config["cleanup.policy"] == "delete"

    def test_streaming_query_request_valid(self):
        """Test valid StreamingQueryRequest"""
        data = {
            "query": "What's my account status?",
            "customer_id": "customer_123",
            "stream_to_topic": "query_responses",
            "query_type": "account",
            "priority": "medium",
            "context": {"session_id": "sess_789"},
            "metadata": {"channel": "web"}
        }
        
        request = StreamingQueryRequest(**data)
        assert request.query == "What's my account status?"
        assert request.customer_id == "customer_123"
        assert request.stream_to_topic == "query_responses"
        assert request.query_type == QueryType.ACCOUNT


class TestSchemaDefaults:
    """Test schema default values"""

    def test_query_request_defaults(self):
        """Test QueryRequest default values"""
        request = QueryRequest(
            query="Test query",
            customer_id="customer_123"
        )
        
        assert request.query_type == QueryType.GENERAL
        assert request.priority == Priority.MEDIUM
        assert request.context == {}
        assert request.metadata == {}

    def test_ticket_request_defaults(self):
        """Test TicketRequest default values"""
        request = TicketRequest(
            title="Test ticket",
            description="Test description",
            customer_id="customer_123"
        )
        
        assert request.category == QueryType.GENERAL
        assert request.priority == Priority.MEDIUM
        assert request.tags == []

    def test_customer_request_defaults(self):
        """Test CustomerRequest default values"""
        request = CustomerRequest(
            name="Test Customer",
            email="test@example.com"
        )
        
        assert request.phone is None
        assert request.company is None
        assert request.metadata == {}

    def test_customer_response_defaults(self):
        """Test CustomerResponse default values"""
        response = CustomerResponse(
            customer_id="customer_123",
            name="Test Customer",
            email="test@example.com",
            created_at=datetime.utcnow()
        )
        
        assert response.phone is None
        assert response.company is None
        assert response.metadata == {}
        assert response.ticket_count == 0
        assert response.last_interaction is None


class TestSchemaEdgeCases:
    """Test schema edge cases and validation"""

    def test_empty_strings(self):
        """Test handling of empty strings"""
        with pytest.raises(ValidationError):
            QueryRequest(query="", customer_id="test")
        
        with pytest.raises(ValidationError):
            CustomerRequest(name="", email="test@example.com")

    def test_none_values(self):
        """Test handling of None values for required fields"""
        with pytest.raises(ValidationError):
            QueryRequest(query=None, customer_id="test")
        
        with pytest.raises(ValidationError):
            CustomerRequest(name=None, email="test@example.com")

    def test_type_coercion(self):
        """Test type coercion in schemas"""
        # Test string to int coercion for rating
        request = FeedbackRequest(
            customer_id="test",
            rating="5"  # String should be coerced to int
        )
        assert request.rating == 5
        assert isinstance(request.rating, int)

    def test_additional_properties(self):
        """Test schemas with additional properties"""
        # Pydantic should ignore extra fields by default
        data = {
            "query": "test query",
            "customer_id": "test",
            "extra_field": "should be ignored"
        }
        
        request = QueryRequest(**data)
        assert request.query == "test query"
        assert request.customer_id == "test"
        # extra_field should not be accessible
        assert not hasattr(request, "extra_field")
