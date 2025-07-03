import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from src.api.dependencies import (
    get_query_service_dep,
    get_ticket_service_dep,
    get_customer_service_dep,
    get_feedback_service_dep,
    get_analytics_service_dep,
    get_kafka_client_dep
)


class TestServiceDependencies:
    """Test service dependency providers"""

    def test_get_query_service_dep(self):
        """Test query service dependency"""
        with patch('src.api.dependencies.get_query_service') as mock_get_service:
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service
            
            result = get_query_service_dep()
            assert result == mock_service
            mock_get_service.assert_called_once()

    def test_get_ticket_service_dep(self):
        """Test ticket service dependency"""
        with patch('src.api.dependencies.get_ticket_service') as mock_get_service:
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service
            
            result = get_ticket_service_dep()
            assert result == mock_service
            mock_get_service.assert_called_once()

    def test_get_customer_service_dep(self):
        """Test customer service dependency"""
        with patch('src.api.dependencies.get_customer_service') as mock_get_service:
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service
            
            result = get_customer_service_dep()
            assert result == mock_service
            mock_get_service.assert_called_once()

    def test_get_feedback_service_dep(self):
        """Test feedback service dependency"""
        with patch('src.api.dependencies.get_feedback_service') as mock_get_service:
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service
            
            result = get_feedback_service_dep()
            assert result == mock_service
            mock_get_service.assert_called_once()

    def test_get_analytics_service_dep(self):
        """Test analytics service dependency"""
        with patch('src.api.dependencies.get_analytics_service') as mock_get_service:
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service
            
            result = get_analytics_service_dep()
            assert result == mock_service
            mock_get_service.assert_called_once()

    def test_get_kafka_client_dep_success(self):
        """Test Kafka client dependency when available"""
        with patch('src.api.dependencies.get_kafka_client') as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            
            result = get_kafka_client_dep()
            assert result == mock_client
            mock_get_client.assert_called_once()

    def test_get_kafka_client_dep_unavailable(self):
        """Test Kafka client dependency when unavailable"""
        with patch('src.api.dependencies.get_kafka_client') as mock_get_client:
            mock_get_client.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                get_kafka_client_dep()
            
            assert exc_info.value.status_code == 503
            assert "Kafka MCP client not available" in str(exc_info.value.detail)

    def test_get_kafka_client_dep_exception(self):
        """Test Kafka client dependency when get_kafka_client raises exception"""
        with patch('src.api.dependencies.get_kafka_client') as mock_get_client:
            mock_get_client.side_effect = Exception("Connection failed")
            
            # The exception should bubble up since we only catch None return values
            with pytest.raises(Exception) as exc_info:
                get_kafka_client_dep()
            
            assert "Connection failed" in str(exc_info.value)


class TestDependencyIntegration:
    """Test dependency integration with service factory"""

    def test_all_dependencies_available(self):
        """Test that all dependencies can be resolved"""
        with patch('src.api.dependencies.get_query_service') as mock_query, \
             patch('src.api.dependencies.get_ticket_service') as mock_ticket, \
             patch('src.api.dependencies.get_customer_service') as mock_customer, \
             patch('src.api.dependencies.get_feedback_service') as mock_feedback, \
             patch('src.api.dependencies.get_analytics_service') as mock_analytics, \
             patch('src.api.dependencies.get_kafka_client') as mock_kafka:
            
            # Setup mocks
            mock_query.return_value = MagicMock(name="QueryService")
            mock_ticket.return_value = MagicMock(name="TicketService")
            mock_customer.return_value = MagicMock(name="CustomerService")
            mock_feedback.return_value = MagicMock(name="FeedbackService")
            mock_analytics.return_value = MagicMock(name="AnalyticsService")
            mock_kafka.return_value = MagicMock(name="KafkaClient")
            
            # Test all dependencies
            query_service = get_query_service_dep()
            ticket_service = get_ticket_service_dep()
            customer_service = get_customer_service_dep()
            feedback_service = get_feedback_service_dep()
            analytics_service = get_analytics_service_dep()
            kafka_client = get_kafka_client_dep()
            
            # Verify all services are returned
            assert query_service is not None
            assert ticket_service is not None
            assert customer_service is not None
            assert feedback_service is not None
            assert analytics_service is not None
            assert kafka_client is not None
            
            # Verify service factory methods were called
            mock_query.assert_called_once()
            mock_ticket.assert_called_once()
            mock_customer.assert_called_once()
            mock_feedback.assert_called_once()
            mock_analytics.assert_called_once()
            mock_kafka.assert_called_once()

    def test_dependency_consistency(self):
        """Test that dependencies return consistent instances"""
        with patch('src.api.dependencies.get_query_service') as mock_get_service:
            mock_service = MagicMock(name="QueryService")
            mock_get_service.return_value = mock_service
            
            # Call dependency multiple times
            service1 = get_query_service_dep()
            service2 = get_query_service_dep()
            
            # Should return same instance (singleton behavior through service factory)
            assert service1 == service2
            assert mock_get_service.call_count == 2  # Called each time but returns same instance
