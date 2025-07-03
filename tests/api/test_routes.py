"""
Comprehensive tests for API routes.
Tests all endpoints including success cases, error handling, and edge cases.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime
import json

from src.api.schemas import (
    QueryRequest, QueryResponse, TicketRequest, TicketResponse,
    CustomerRequest, CustomerResponse, FeedbackRequest, FeedbackResponse,
    AnalyticsResponse, QueryType, Priority, TicketStatus
)


class TestQueryEndpoints:
    """Test query-related endpoints."""
    
    def test_process_query_success(self, test_client, mock_service_dependencies, sample_query_request, sample_query_response):
        """Test successful query processing."""
        # Setup mock
        mock_service_dependencies['query_service'].process_query.return_value = sample_query_response
        mock_service_dependencies['customer_service'].update_last_interaction.return_value = None
        
        # Make request
        response = test_client.post("/queries", json=sample_query_request.model_dump())
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["query_id"] == sample_query_response.query_id
        assert data["result"] == sample_query_response.result
        assert data["confidence"] == sample_query_response.confidence
        assert data["success"] == sample_query_response.success
        assert data["agent_used"] == sample_query_response.agent_used
        
        # Verify service calls
        mock_service_dependencies['query_service'].process_query.assert_called_once()
        mock_service_dependencies['customer_service'].update_last_interaction.assert_called_once_with(
            sample_query_request.customer_id
        )
    
    def test_process_query_invalid_input(self, test_client, mock_service_dependencies):
        """Test query processing with invalid input."""
        # Invalid request - missing required fields
        invalid_request = {"query": "test"}  # missing customer_id
        
        response = test_client.post("/queries", json=invalid_request)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
    
    def test_process_query_service_error(self, test_client, mock_service_dependencies, sample_query_request):
        """Test query processing when service throws error."""
        # Setup mock to raise exception
        mock_service_dependencies['query_service'].process_query.side_effect = Exception("Service error")
        mock_service_dependencies['customer_service'].update_last_interaction.return_value = None
        
        response = test_client.post("/queries", json=sample_query_request.model_dump())
        
        assert response.status_code == 500
        data = response.json()
        assert "Query processing failed" in data["detail"]
    
    def test_get_query_by_id_success(self, test_client, mock_service_dependencies, sample_query_response):
        """Test successful query retrieval by ID."""
        # Setup mock
        mock_service_dependencies['query_service'].get_query_by_id.return_value = sample_query_response
        
        response = test_client.get(f"/queries/{sample_query_response.query_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["query_id"] == sample_query_response.query_id
        
        # Verify service call
        mock_service_dependencies['query_service'].get_query_by_id.assert_called_once_with(
            sample_query_response.query_id
        )
    
    def test_get_query_by_id_not_found(self, test_client, mock_service_dependencies):
        """Test query retrieval when query doesn't exist."""
        # Setup mock to return None
        mock_service_dependencies['query_service'].get_query_by_id.return_value = None
        
        response = test_client.get("/queries/nonexistent_id")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Query not found"
    
    def test_list_queries_success(self, test_client, mock_service_dependencies, sample_query_response):
        """Test successful query listing."""
        # Setup mock
        mock_service_dependencies['query_service'].list_queries.return_value = [sample_query_response]
        
        response = test_client.get("/queries")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["query_id"] == sample_query_response.query_id
    
    def test_list_queries_with_filters(self, test_client, mock_service_dependencies, sample_query_response):
        """Test query listing with filters."""
        # Setup mock
        mock_service_dependencies['query_service'].list_queries.return_value = [sample_query_response]
        
        response = test_client.get("/queries?customer_id=customer_123&query_type=technical&limit=5")
        
        assert response.status_code == 200
        
        # Verify service call with filters
        mock_service_dependencies['query_service'].list_queries.assert_called_once_with(
            customer_id="customer_123",
            query_type=QueryType.TECHNICAL,
            limit=5
        )
    
    def test_list_queries_invalid_limit(self, test_client, mock_service_dependencies):
        """Test query listing with invalid limit."""
        response = test_client.get("/queries?limit=0")  # Invalid limit
        
        assert response.status_code == 422  # Validation error


class TestTicketEndpoints:
    """Test ticket-related endpoints."""
    
    def test_create_ticket_success(self, test_client, mock_service_dependencies, sample_ticket_request, sample_ticket_response):
        """Test successful ticket creation."""
        # Setup mocks
        mock_service_dependencies['ticket_service'].create_ticket.return_value = sample_ticket_response
        mock_service_dependencies['customer_service'].update_last_interaction.return_value = None
        mock_service_dependencies['customer_service'].increment_ticket_count.return_value = None
        
        response = test_client.post("/tickets", json=sample_ticket_request.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["ticket_id"] == sample_ticket_response.ticket_id
        assert data["title"] == sample_ticket_response.title
        assert data["status"] == sample_ticket_response.status
        
        # Verify service calls
        mock_service_dependencies['ticket_service'].create_ticket.assert_called_once()
        mock_service_dependencies['customer_service'].update_last_interaction.assert_called_once_with(
            sample_ticket_request.customer_id
        )
        mock_service_dependencies['customer_service'].increment_ticket_count.assert_called_once_with(
            sample_ticket_request.customer_id
        )
    
    def test_create_ticket_invalid_input(self, test_client, mock_service_dependencies):
        """Test ticket creation with invalid input."""
        invalid_request = {"title": "test"}  # missing required fields
        
        response = test_client.post("/tickets", json=invalid_request)
        
        assert response.status_code == 422
    
    def test_get_ticket_by_id_success(self, test_client, mock_service_dependencies, sample_ticket_response):
        """Test successful ticket retrieval by ID."""
        mock_service_dependencies['ticket_service'].get_ticket_by_id.return_value = sample_ticket_response
        
        response = test_client.get(f"/tickets/{sample_ticket_response.ticket_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ticket_id"] == sample_ticket_response.ticket_id
    
    def test_get_ticket_by_id_not_found(self, test_client, mock_service_dependencies):
        """Test ticket retrieval when ticket doesn't exist."""
        mock_service_dependencies['ticket_service'].get_ticket_by_id.return_value = None
        
        response = test_client.get("/tickets/nonexistent_id")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Ticket not found"
    
    def test_list_tickets_success(self, test_client, mock_service_dependencies, sample_ticket_response):
        """Test successful ticket listing."""
        mock_service_dependencies['ticket_service'].list_tickets.return_value = [sample_ticket_response]
        
        response = test_client.get("/tickets")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["ticket_id"] == sample_ticket_response.ticket_id
    
    def test_update_ticket_status_success(self, test_client, mock_service_dependencies, sample_ticket_response):
        """Test successful ticket status update."""
        updated_ticket = sample_ticket_response.model_copy()
        updated_ticket.status = TicketStatus.RESOLVED
        
        mock_service_dependencies['ticket_service'].update_ticket_status.return_value = updated_ticket
        
        response = test_client.patch(
            f"/tickets/{sample_ticket_response.ticket_id}/status",
            json={"status": "resolved"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"
    
    def test_update_ticket_status_invalid_status(self, test_client, mock_service_dependencies):
        """Test ticket status update with invalid status."""
        response = test_client.patch(
            "/tickets/ticket_123/status",
            json={"status": "invalid_status"}
        )
        
        assert response.status_code == 422


class TestCustomerEndpoints:
    """Test customer-related endpoints."""
    
    def test_create_customer_success(self, test_client, mock_service_dependencies, sample_customer_request, sample_customer_response):
        """Test successful customer creation."""
        mock_service_dependencies['customer_service'].create_customer.return_value = sample_customer_response
        
        response = test_client.post("/customers", json=sample_customer_request.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["customer_id"] == sample_customer_response.customer_id
        assert data["name"] == sample_customer_response.name
        assert data["email"] == sample_customer_response.email
    
    def test_create_customer_invalid_input(self, test_client, mock_service_dependencies):
        """Test customer creation with invalid input."""
        invalid_request = {"name": ""}  # Empty name
        
        response = test_client.post("/customers", json=invalid_request)
        
        assert response.status_code == 422
    
    def test_get_customer_by_id_success(self, test_client, mock_service_dependencies, sample_customer_response):
        """Test successful customer retrieval by ID."""
        mock_service_dependencies['customer_service'].get_customer_by_id.return_value = sample_customer_response
        
        response = test_client.get(f"/customers/{sample_customer_response.customer_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["customer_id"] == sample_customer_response.customer_id
    
    def test_get_customer_by_id_not_found(self, test_client, mock_service_dependencies):
        """Test customer retrieval when customer doesn't exist."""
        mock_service_dependencies['customer_service'].get_customer_by_id.return_value = None
        
        response = test_client.get("/customers/nonexistent_id")
        
        assert response.status_code == 404
    
    def test_list_customers_success(self, test_client, mock_service_dependencies, sample_customer_response):
        """Test successful customer listing."""
        mock_service_dependencies['customer_service'].list_customers.return_value = [sample_customer_response]
        
        response = test_client.get("/customers")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["customer_id"] == sample_customer_response.customer_id
    
    def test_update_customer_success(self, test_client, mock_service_dependencies, sample_customer_response):
        """Test successful customer update."""
        updated_customer = sample_customer_response.model_copy()
        updated_customer.name = "Updated Name"
        
        mock_service_dependencies['customer_service'].update_customer.return_value = updated_customer
        
        response = test_client.put(
            f"/customers/{sample_customer_response.customer_id}",
            json={"name": "Updated Name", "email": "updated@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
    
    def test_delete_customer_success(self, test_client, mock_service_dependencies):
        """Test successful customer deletion."""
        mock_service_dependencies['customer_service'].delete_customer.return_value = True
        
        response = test_client.delete("/customers/customer_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestFeedbackEndpoints:
    """Test feedback-related endpoints."""
    
    def test_create_feedback_success(self, test_client, mock_service_dependencies, sample_feedback_request, sample_feedback_response):
        """Test successful feedback creation."""
        mock_service_dependencies['feedback_service'].create_feedback.return_value = sample_feedback_response
        
        response = test_client.post("/feedback", json=sample_feedback_request.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["feedback_id"] == sample_feedback_response.feedback_id
        assert data["rating"] == sample_feedback_response.rating
    
    def test_create_feedback_invalid_rating(self, test_client, mock_service_dependencies):
        """Test feedback creation with invalid rating."""
        invalid_request = {
            "customer_id": "customer_123",
            "rating": 6  # Invalid rating (should be 1-5)
        }
        
        response = test_client.post("/feedback", json=invalid_request)
        
        assert response.status_code == 422
    
    def test_get_feedback_by_id_success(self, test_client, mock_service_dependencies, sample_feedback_response):
        """Test successful feedback retrieval by ID."""
        mock_service_dependencies['feedback_service'].get_feedback_by_id.return_value = sample_feedback_response
        
        response = test_client.get(f"/feedback/{sample_feedback_response.feedback_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["feedback_id"] == sample_feedback_response.feedback_id
    
    def test_list_feedback_success(self, test_client, mock_service_dependencies, sample_feedback_response):
        """Test successful feedback listing."""
        mock_service_dependencies['feedback_service'].list_feedback.return_value = [sample_feedback_response]
        
        response = test_client.get("/feedback")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["feedback_id"] == sample_feedback_response.feedback_id
    
    def test_get_feedback_by_customer_success(self, test_client, mock_service_dependencies, sample_feedback_response):
        """Test successful feedback retrieval by customer ID."""
        mock_service_dependencies['feedback_service'].get_feedback_by_customer.return_value = [sample_feedback_response]
        
        response = test_client.get(f"/feedback/customer/{sample_feedback_response.customer_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["customer_id"] == sample_feedback_response.customer_id


class TestAnalyticsEndpoints:
    """Test analytics-related endpoints."""
    
    def test_get_analytics_success(self, test_client, mock_service_dependencies, sample_analytics_response):
        """Test successful analytics retrieval."""
        mock_service_dependencies['analytics_service'].get_analytics.return_value = sample_analytics_response
        
        response = test_client.get("/analytics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_queries"] == sample_analytics_response.total_queries
        assert data["total_tickets"] == sample_analytics_response.total_tickets
        assert data["total_customers"] == sample_analytics_response.total_customers
        assert data["avg_response_time"] == sample_analytics_response.avg_response_time
        assert data["avg_rating"] == sample_analytics_response.avg_rating
    
    def test_get_analytics_with_date_range(self, test_client, mock_service_dependencies, sample_analytics_response):
        """Test analytics retrieval with date range."""
        mock_service_dependencies['analytics_service'].get_analytics.return_value = sample_analytics_response
        
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        
        response = test_client.get(f"/analytics?start_date={start_date}&end_date={end_date}")
        
        assert response.status_code == 200
        
        # Verify service was called with date parameters
        mock_service_dependencies['analytics_service'].get_analytics.assert_called_once()
    
    def test_get_query_metrics_success(self, test_client, mock_service_dependencies):
        """Test successful query metrics retrieval."""
        mock_metrics = {
            "total_queries": 100,
            "avg_processing_time": 2.5,
            "success_rate": 0.95,
            "queries_by_type": {"technical": 50, "billing": 30, "general": 20}
        }
        mock_service_dependencies['analytics_service'].get_query_metrics.return_value = mock_metrics
        
        response = test_client.get("/analytics/queries")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_queries"] == 100
        assert data["avg_processing_time"] == 2.5
        assert data["success_rate"] == 0.95
    
    def test_get_ticket_metrics_success(self, test_client, mock_service_dependencies):
        """Test successful ticket metrics retrieval."""
        mock_metrics = {
            "total_tickets": 50,
            "resolution_rate": 0.8,
            "avg_resolution_time": 24.5,
            "tickets_by_status": {"open": 10, "resolved": 40}
        }
        mock_service_dependencies['analytics_service'].get_ticket_metrics.return_value = mock_metrics
        
        response = test_client.get("/analytics/tickets")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_tickets"] == 50
        assert data["resolution_rate"] == 0.8


class TestErrorHandling:
    """Test error handling across all endpoints."""
    
    def test_internal_server_error(self, test_client, mock_service_dependencies, sample_query_request):
        """Test handling of internal server errors."""
        # Make service throw unexpected error
        mock_service_dependencies['query_service'].process_query.side_effect = RuntimeError("Unexpected error")
        mock_service_dependencies['customer_service'].update_last_interaction.return_value = None
        
        response = test_client.post("/queries", json=sample_query_request.model_dump())
        
        assert response.status_code == 500
        data = response.json()
        assert "Query processing failed" in data["detail"]
    
    def test_validation_error_handling(self, test_client):
        """Test handling of validation errors."""
        # Send invalid JSON
        response = test_client.post("/queries", json={"invalid": "data"})
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_method_not_allowed(self, test_client):
        """Test method not allowed errors."""
        response = test_client.patch("/queries")  # PATCH not allowed on collection
        
        assert response.status_code == 405
    
    def test_not_found_endpoint(self, test_client):
        """Test accessing non-existent endpoints."""
        response = test_client.get("/nonexistent")
        
        assert response.status_code == 404


class TestAuthenticationAndAuthorization:
    """Test authentication and authorization (if implemented)."""
    
    @pytest.mark.skip(reason="Authentication not implemented yet")
    def test_unauthorized_access(self, test_client):
        """Test unauthorized access to protected endpoints."""
        response = test_client.get("/analytics")
        
        assert response.status_code == 401
    
    @pytest.mark.skip(reason="Authentication not implemented yet")
    def test_forbidden_access(self, test_client):
        """Test forbidden access with insufficient permissions."""
        # This would test role-based access control
        pass


class TestRateLimiting:
    """Test rate limiting (if implemented)."""
    
    @pytest.mark.skip(reason="Rate limiting not implemented yet")
    def test_rate_limit_exceeded(self, test_client, sample_query_request):
        """Test rate limiting functionality."""
        # This would test rate limiting by making many requests quickly
        for i in range(100):
            response = test_client.post("/queries", json=sample_query_request.model_dump())
            if response.status_code == 429:  # Too Many Requests
                break
        else:
            pytest.fail("Rate limiting not triggered")


class TestPagination:
    """Test pagination functionality."""
    
    def test_list_queries_pagination(self, test_client, mock_service_dependencies):
        """Test query listing with pagination."""
        # Create multiple mock responses
        mock_responses = [
            create_test_query_response(f"query_{i}", f"customer_{i}")
            for i in range(25)
        ]
        mock_service_dependencies['query_service'].list_queries.return_value = mock_responses[:10]
        
        response = test_client.get("/queries?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
    
    def test_list_tickets_pagination(self, test_client, mock_service_dependencies):
        """Test ticket listing with pagination."""
        mock_responses = [
            create_test_ticket_response(f"ticket_{i}", f"customer_{i}")
            for i in range(25)
        ]
        mock_service_dependencies['ticket_service'].list_tickets.return_value = mock_responses[:20]
        
        response = test_client.get("/tickets?limit=20")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 20


class TestConcurrentRequests:
    """Test concurrent request handling."""
    
    @pytest.mark.asyncio
    async def test_concurrent_query_processing(self, mock_service_dependencies, sample_query_request, sample_query_response):
        """Test handling of concurrent query requests."""
        import asyncio
        from httpx import AsyncClient
        from src.api.api_main import app
        
        # Setup mocks
        mock_service_dependencies['query_service'].process_query.return_value = sample_query_response
        mock_service_dependencies['customer_service'].update_last_interaction.return_value = None
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Send multiple concurrent requests
            tasks = []
            for i in range(10):
                task = client.post("/queries", json=sample_query_request.model_dump())
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True


# Helper functions (imported from conftest.py)
def create_test_query_response(query_id: str = None, customer_id: str = None):
    """Create a test QueryResponse with optional overrides."""
    from src.api.schemas import QueryResponse, QueryType, Priority
    
    return QueryResponse(
        query_id=query_id or "test_query",
        result="Test response",
        confidence=0.9,
        success=True,
        agent_used="test_agent",
        processing_time=1.0,
        suggestions=["Test suggestion"],
        timestamp=datetime.utcnow()
    )


def create_test_ticket_response(ticket_id: str = None, customer_id: str = None):
    """Create a test TicketResponse with optional overrides."""
    from src.api.schemas import TicketResponse, TicketStatus, Priority, QueryType
    
    return TicketResponse(
        ticket_id=ticket_id or "test_ticket",
        title="Test ticket",
        status=TicketStatus.OPEN,
        customer_id=customer_id or "test_customer",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        priority=Priority.MEDIUM,
        category=QueryType.GENERAL,
        assigned_agent=None
    )
