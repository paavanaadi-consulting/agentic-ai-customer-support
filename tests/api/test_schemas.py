"""
Comprehensive tests for API schemas (Pydantic models).
Tests validation, serialization, and edge cases.
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from pydantic import ValidationError

from src.api.schemas import (
    QueryRequest, QueryResponse, TicketRequest, TicketResponse,
    CustomerRequest, CustomerResponse, FeedbackRequest, FeedbackResponse,
    AnalyticsResponse, ErrorResponse, SuccessResponse,
    KafkaMessageRequest, KafkaMessageResponse, KafkaTopicRequest, KafkaTopicResponse,
    StreamingQueryRequest, StreamingQueryResponse,
    QueryType, Priority, TicketStatus
)


class TestEnums:
    """Test enum validations."""
    
    def test_query_type_enum(self):
        """Test QueryType enum values."""
        assert QueryType.GENERAL == "general"
        assert QueryType.TECHNICAL == "technical"
        assert QueryType.BILLING == "billing"
        assert QueryType.ACCOUNT == "account"
        assert QueryType.COMPLAINT == "complaint"
    
    def test_priority_enum(self):
        """Test Priority enum values."""
        assert Priority.LOW == "low"
        assert Priority.MEDIUM == "medium"
        assert Priority.HIGH == "high"
        assert Priority.CRITICAL == "critical"
    
    def test_ticket_status_enum(self):
        """Test TicketStatus enum values."""
        assert TicketStatus.OPEN == "open"
        assert TicketStatus.IN_PROGRESS == "in_progress"
        assert TicketStatus.PENDING == "pending"
        assert TicketStatus.RESOLVED == "resolved"
        assert TicketStatus.CLOSED == "closed"


class TestQuerySchemas:
    """Test query-related schemas."""
    
    def test_query_request_valid(self):
        """Test valid QueryRequest creation."""
        request = QueryRequest(
            query="How can I reset my password?",
            customer_id="customer_123",
            query_type=QueryType.TECHNICAL,
            priority=Priority.HIGH,
            context={"source": "web"},
            metadata={"ip": "192.168.1.1"}
        )
        
        assert request.query == "How can I reset my password?"
        assert request.customer_id == "customer_123"
        assert request.query_type == QueryType.TECHNICAL
        assert request.priority == Priority.HIGH
        assert request.context == {"source": "web"}
        assert request.metadata == {"ip": "192.168.1.1"}
    
    def test_query_request_minimal(self):
        """Test QueryRequest with minimal required fields."""
        request = QueryRequest(
            query="Test query",
            customer_id="customer_123"
        )
        
        assert request.query == "Test query"
        assert request.customer_id == "customer_123"
        assert request.query_type == QueryType.GENERAL  # default
        assert request.priority == Priority.MEDIUM  # default
        assert request.context == {}  # default
        assert request.metadata == {}  # default
    
    def test_query_request_validation_errors(self):
        """Test QueryRequest validation errors."""
        # Missing required fields
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest()
        
        errors = exc_info.value.errors()
        assert len(errors) == 2  # query and customer_id are required
        
        # Empty query
        with pytest.raises(ValidationError):
            QueryRequest(query="", customer_id="customer_123")
        
        # Empty customer_id
        with pytest.raises(ValidationError):
            QueryRequest(query="Test", customer_id="")
    
    def test_query_response_valid(self):
        """Test valid QueryResponse creation."""
        response = QueryResponse(
            query_id="query_123",
            result="Password reset instructions sent",
            confidence=0.95,
            success=True,
            agent_used="technical_agent",
            processing_time=1.25,
            suggestions=["Check email", "Contact support"],
            timestamp=datetime.utcnow()
        )
        
        assert response.query_id == "query_123"
        assert response.result == "Password reset instructions sent"
        assert response.confidence == 0.95
        assert response.success is True
        assert response.agent_used == "technical_agent"
        assert response.processing_time == 1.25
        assert len(response.suggestions) == 2
        assert isinstance(response.timestamp, datetime)
    
    def test_query_response_confidence_validation(self):
        """Test confidence score validation."""
        # Valid confidence values
        QueryResponse(
            query_id="test", result="test", confidence=0.0,
            success=True, agent_used="test", processing_time=1.0
        )
        QueryResponse(
            query_id="test", result="test", confidence=1.0,
            success=True, agent_used="test", processing_time=1.0
        )
        
        # Invalid confidence values
        with pytest.raises(ValidationError):
            QueryResponse(
                query_id="test", result="test", confidence=-0.1,
                success=True, agent_used="test", processing_time=1.0
            )
        
        with pytest.raises(ValidationError):
            QueryResponse(
                query_id="test", result="test", confidence=1.1,
                success=True, agent_used="test", processing_time=1.0
            )


class TestTicketSchemas:
    """Test ticket-related schemas."""
    
    def test_ticket_request_valid(self):
        """Test valid TicketRequest creation."""
        request = TicketRequest(
            title="Login Issue",
            description="Cannot login to my account",
            customer_id="customer_123",
            category=QueryType.TECHNICAL,
            priority=Priority.HIGH,
            tags=["login", "authentication"]
        )
        
        assert request.title == "Login Issue"
        assert request.description == "Cannot login to my account"
        assert request.customer_id == "customer_123"
        assert request.category == QueryType.TECHNICAL
        assert request.priority == Priority.HIGH
        assert request.tags == ["login", "authentication"]
    
    def test_ticket_request_defaults(self):
        """Test TicketRequest default values."""
        request = TicketRequest(
            title="Test Ticket",
            description="Test Description",
            customer_id="customer_123"
        )
        
        assert request.category == QueryType.GENERAL
        assert request.priority == Priority.MEDIUM
        assert request.tags == []
    
    def test_ticket_response_valid(self):
        """Test valid TicketResponse creation."""
        now = datetime.utcnow()
        response = TicketResponse(
            ticket_id="ticket_123",
            title="Login Issue",
            status=TicketStatus.OPEN,
            customer_id="customer_123",
            created_at=now,
            updated_at=now,
            priority=Priority.HIGH,
            category=QueryType.TECHNICAL,
            assigned_agent="agent_456"
        )
        
        assert response.ticket_id == "ticket_123"
        assert response.title == "Login Issue"
        assert response.status == TicketStatus.OPEN
        assert response.customer_id == "customer_123"
        assert response.created_at == now
        assert response.updated_at == now
        assert response.priority == Priority.HIGH
        assert response.category == QueryType.TECHNICAL
        assert response.assigned_agent == "agent_456"


class TestCustomerSchemas:
    """Test customer-related schemas."""
    
    def test_customer_request_valid(self):
        """Test valid CustomerRequest creation."""
        request = CustomerRequest(
            name="John Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            company="ACME Corp",
            metadata={"source": "website"}
        )
        
        assert request.name == "John Doe"
        assert request.email == "john.doe@example.com"
        assert request.phone == "+1234567890"
        assert request.company == "ACME Corp"
        assert request.metadata == {"source": "website"}
    
    def test_customer_request_minimal(self):
        """Test CustomerRequest with minimal fields."""
        request = CustomerRequest(
            name="John Doe",
            email="john.doe@example.com"
        )
        
        assert request.name == "John Doe"
        assert request.email == "john.doe@example.com"
        assert request.phone is None
        assert request.company is None
        assert request.metadata == {}
    
    def test_customer_response_valid(self):
        """Test valid CustomerResponse creation."""
        now = datetime.utcnow()
        response = CustomerResponse(
            customer_id="customer_123",
            name="John Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            company="ACME Corp",
            created_at=now,
            metadata={"source": "website"},
            ticket_count=5,
            last_interaction=now
        )
        
        assert response.customer_id == "customer_123"
        assert response.name == "John Doe"
        assert response.email == "john.doe@example.com"
        assert response.phone == "+1234567890"
        assert response.company == "ACME Corp"
        assert response.created_at == now
        assert response.metadata == {"source": "website"}
        assert response.ticket_count == 5
        assert response.last_interaction == now


class TestFeedbackSchemas:
    """Test feedback-related schemas."""
    
    def test_feedback_request_valid(self):
        """Test valid FeedbackRequest creation."""
        request = FeedbackRequest(
            customer_id="customer_123",
            rating=5,
            comment="Excellent service!",
            query_id="query_123",
            ticket_id="ticket_123"
        )
        
        assert request.customer_id == "customer_123"
        assert request.rating == 5
        assert request.comment == "Excellent service!"
        assert request.query_id == "query_123"
        assert request.ticket_id == "ticket_123"
    
    def test_feedback_request_rating_validation(self):
        """Test rating validation."""
        # Valid ratings
        for rating in [1, 2, 3, 4, 5]:
            request = FeedbackRequest(
                customer_id="customer_123",
                rating=rating
            )
            assert request.rating == rating
        
        # Invalid ratings
        for rating in [0, 6, -1, 10]:
            with pytest.raises(ValidationError):
                FeedbackRequest(
                    customer_id="customer_123",
                    rating=rating
                )
    
    def test_feedback_response_valid(self):
        """Test valid FeedbackResponse creation."""
        now = datetime.utcnow()
        response = FeedbackResponse(
            feedback_id="feedback_123",
            customer_id="customer_123",
            rating=4,
            comment="Good service",
            query_id="query_123",
            ticket_id="ticket_123",
            created_at=now
        )
        
        assert response.feedback_id == "feedback_123"
        assert response.customer_id == "customer_123"
        assert response.rating == 4
        assert response.comment == "Good service"
        assert response.query_id == "query_123"
        assert response.ticket_id == "ticket_123"
        assert response.created_at == now


class TestAnalyticsSchemas:
    """Test analytics-related schemas."""
    
    def test_analytics_response_valid(self):
        """Test valid AnalyticsResponse creation."""
        response = AnalyticsResponse(
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
            resolution_rate=0.90,
            additional_metrics={"peak_hour": "14:00"}
        )
        
        assert response.total_queries == 1000
        assert response.total_tickets == 250
        assert response.total_customers == 500
        assert response.avg_response_time == 2.5
        assert response.avg_rating == 4.2
        assert response.tickets_by_status["open"] == 50
        assert response.queries_by_type["general"] == 400
        assert response.customer_satisfaction_rate == 0.85
        assert response.resolution_rate == 0.90
        assert response.additional_metrics["peak_hour"] == "14:00"


class TestGenericSchemas:
    """Test generic response schemas."""
    
    def test_error_response_valid(self):
        """Test valid ErrorResponse creation."""
        response = ErrorResponse(
            error="Something went wrong",
            error_code="ERR_001",
            timestamp=datetime.utcnow()
        )
        
        assert response.error == "Something went wrong"
        assert response.error_code == "ERR_001"
        assert isinstance(response.timestamp, datetime)
    
    def test_error_response_auto_timestamp(self):
        """Test ErrorResponse with automatic timestamp."""
        response = ErrorResponse(
            error="Test error",
            error_code="ERR_TEST"
        )
        
        assert response.error == "Test error"
        assert response.error_code == "ERR_TEST"
        assert isinstance(response.timestamp, datetime)
        # Check timestamp is recent (within last minute)
        assert (datetime.utcnow() - response.timestamp).total_seconds() < 60
    
    def test_success_response_valid(self):
        """Test valid SuccessResponse creation."""
        response = SuccessResponse(
            message="Operation completed successfully",
            success=True,
            timestamp=datetime.utcnow()
        )
        
        assert response.message == "Operation completed successfully"
        assert response.success is True
        assert isinstance(response.timestamp, datetime)
    
    def test_success_response_defaults(self):
        """Test SuccessResponse default values."""
        response = SuccessResponse(
            message="Test message"
        )
        
        assert response.message == "Test message"
        assert response.success is True  # default
        assert isinstance(response.timestamp, datetime)


class TestKafkaSchemas:
    """Test Kafka-related schemas."""
    
    def test_kafka_message_request_valid(self):
        """Test valid KafkaMessageRequest creation."""
        request = KafkaMessageRequest(
            topic="customer_queries",
            message={"query": "test", "customer_id": "123"},
            key="customer_123"
        )
        
        assert request.topic == "customer_queries"
        assert request.message == {"query": "test", "customer_id": "123"}
        assert request.key == "customer_123"
    
    def test_kafka_message_request_no_key(self):
        """Test KafkaMessageRequest without key."""
        request = KafkaMessageRequest(
            topic="test_topic",
            message={"data": "test"}
        )
        
        assert request.topic == "test_topic"
        assert request.message == {"data": "test"}
        assert request.key is None
    
    def test_kafka_message_response_valid(self):
        """Test valid KafkaMessageResponse creation."""
        now = datetime.utcnow()
        response = KafkaMessageResponse(
            success=True,
            topic="customer_queries",
            partition=0,
            offset=12345,
            timestamp=now
        )
        
        assert response.success is True
        assert response.topic == "customer_queries"
        assert response.partition == 0
        assert response.offset == 12345
        assert response.timestamp == now
    
    def test_kafka_topic_request_valid(self):
        """Test valid KafkaTopicRequest creation."""
        request = KafkaTopicRequest(
            topic="new_topic",
            num_partitions=5,
            replication_factor=2
        )
        
        assert request.topic == "new_topic"
        assert request.num_partitions == 5
        assert request.replication_factor == 2
    
    def test_kafka_topic_request_defaults(self):
        """Test KafkaTopicRequest default values."""
        request = KafkaTopicRequest(topic="test_topic")
        
        assert request.topic == "test_topic"
        assert request.num_partitions == 3  # default
        assert request.replication_factor == 1  # default


class TestStreamingSchemas:
    """Test streaming-related schemas."""
    
    def test_streaming_query_request_valid(self):
        """Test valid StreamingQueryRequest creation."""
        request = StreamingQueryRequest(
            query="How can I help you?",
            customer_id="customer_123",
            stream_response=True,
            callback_url="https://api.example.com/callback"
        )
        
        assert request.query == "How can I help you?"
        assert request.customer_id == "customer_123"
        assert request.stream_response is True
        assert request.callback_url == "https://api.example.com/callback"
    
    def test_streaming_query_request_defaults(self):
        """Test StreamingQueryRequest default values."""
        request = StreamingQueryRequest(
            query="Test query",
            customer_id="customer_123"
        )
        
        assert request.query == "Test query"
        assert request.customer_id == "customer_123"
        assert request.stream_response is True  # default
        assert request.callback_url is None
    
    def test_streaming_query_response_valid(self):
        """Test valid StreamingQueryResponse creation."""
        estimated_completion = datetime.utcnow() + timedelta(minutes=5)
        response = StreamingQueryResponse(
            query_id="query_123",
            status="processing",
            stream_id="stream_456",
            estimated_completion=estimated_completion
        )
        
        assert response.query_id == "query_123"
        assert response.status == "processing"
        assert response.stream_id == "stream_456"
        assert response.estimated_completion == estimated_completion


class TestSchemaValidation:
    """Test schema validation edge cases."""
    
    def test_empty_strings_validation(self):
        """Test validation of empty strings."""
        # QueryRequest should reject empty query
        with pytest.raises(ValidationError):
            QueryRequest(query="", customer_id="customer_123")
        
        # TicketRequest should reject empty title
        with pytest.raises(ValidationError):
            TicketRequest(title="", description="desc", customer_id="customer_123")
    
    def test_special_characters_validation(self):
        """Test validation with special characters."""
        # Special characters should be allowed in text fields
        request = QueryRequest(
            query="How can I reset my password? 特殊字符 émojis 🚀",
            customer_id="customer_123"
        )
        assert "特殊字符" in request.query
        assert "émojis" in request.query
        assert "🚀" in request.query
    
    def test_long_text_validation(self):
        """Test validation with very long text."""
        long_text = "x" * 10000
        
        # Should accept long text in appropriate fields
        request = QueryRequest(
            query=long_text,
            customer_id="customer_123"
        )
        assert len(request.query) == 10000
    
    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        original = QueryRequest(
            query="Test query",
            customer_id="customer_123",
            query_type=QueryType.TECHNICAL,
            priority=Priority.HIGH,
            context={"source": "api"},
            metadata={"version": "1.0"}
        )
        
        # Serialize to JSON
        json_data = original.model_dump()
        
        # Deserialize from JSON
        restored = QueryRequest(**json_data)
        
        assert restored.query == original.query
        assert restored.customer_id == original.customer_id
        assert restored.query_type == original.query_type
        assert restored.priority == original.priority
        assert restored.context == original.context
        assert restored.metadata == original.metadata
    
    def test_datetime_handling(self):
        """Test datetime field handling."""
        now = datetime.utcnow()
        
        response = QueryResponse(
            query_id="test",
            result="test",
            confidence=0.9,
            success=True,
            agent_used="test",
            processing_time=1.0,
            timestamp=now
        )
        
        assert response.timestamp == now
        assert isinstance(response.timestamp, datetime)
        
        # Test JSON serialization preserves datetime
        json_data = response.model_dump()
        assert isinstance(json_data['timestamp'], datetime)


class TestSchemaInheritance:
    """Test schema inheritance and composition."""
    
    def test_model_inheritance(self):
        """Test that schemas properly inherit from BaseModel."""
        from pydantic import BaseModel
        
        request = QueryRequest(query="test", customer_id="test")
        assert isinstance(request, BaseModel)
        
        response = QueryResponse(
            query_id="test", result="test", confidence=0.9,
            success=True, agent_used="test", processing_time=1.0
        )
        assert isinstance(response, BaseModel)
    
    def test_field_descriptions(self):
        """Test that fields have proper descriptions."""
        # Get field info from schema
        schema = QueryRequest.model_json_schema()
        properties = schema['properties']
        
        assert 'description' in properties['query']
        assert 'description' in properties['customer_id']
        assert properties['query']['description'] == "Customer query text"
        assert properties['customer_id']['description'] == "Unique customer identifier"