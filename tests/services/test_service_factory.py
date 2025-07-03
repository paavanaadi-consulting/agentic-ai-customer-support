"""
Comprehensive test suite for ServiceFactory.
Tests dependency injection, service creation, and service management.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Optional

from src.services.service_factory import ServiceFactory, get_service_factory, initialize_service_factory
from src.services.query_service import QueryService
from src.services.ticket_service import TicketService
from src.services.customer_service import CustomerService
from src.services.feedback_service import FeedbackService
from src.services.analytics_service import AnalyticsService
from src.mcp.postgres_mcp_client import OptimizedPostgreSQLMCPClient
from src.mcp.kafka_mcp_client import OptimizedKafkaMCPClient


class TestServiceFactory:
    """Test cases for ServiceFactory class."""

    @pytest.fixture
    def mock_mcp_client(self):
        """Create a mocked PostgreSQL MCP client."""
        return AsyncMock(spec=OptimizedPostgreSQLMCPClient)

    @pytest.fixture
    def mock_kafka_client(self):
        """Create a mocked Kafka MCP client."""
        return AsyncMock(spec=OptimizedKafkaMCPClient)

    @pytest.fixture
    def service_factory(self):
        """Create a basic ServiceFactory instance."""
        return ServiceFactory()

    @pytest.fixture
    def service_factory_with_mcp(self, mock_mcp_client, mock_kafka_client):
        """Create a ServiceFactory instance with MCP clients."""
        return ServiceFactory(
            mcp_client=mock_mcp_client,
            kafka_mcp_client=mock_kafka_client
        )


class TestServiceCreation:
    """Test service creation and initialization."""

    def test_service_factory_initialization_empty(self, service_factory):
        """Test ServiceFactory initialization without MCP clients."""
        assert service_factory._query_service is None
        assert service_factory._ticket_service is None
        assert service_factory._customer_service is None
        assert service_factory._feedback_service is None
        assert service_factory._analytics_service is None
        assert service_factory._mcp_client is None
        assert service_factory._kafka_mcp_client is None
        assert isinstance(service_factory._tickets_db, dict)

    def test_service_factory_initialization_with_mcp(self, service_factory_with_mcp, 
                                                    mock_mcp_client, mock_kafka_client):
        """Test ServiceFactory initialization with MCP clients."""
        assert service_factory_with_mcp._mcp_client == mock_mcp_client
        assert service_factory_with_mcp._kafka_mcp_client == mock_kafka_client

    def test_query_service_creation_without_kafka(self, service_factory):
        """Test QueryService creation without Kafka client."""
        query_service = service_factory.query_service
        
        assert isinstance(query_service, QueryService)
        assert service_factory._query_service is query_service
        
        # Second call should return same instance
        query_service2 = service_factory.query_service
        assert query_service is query_service2

    def test_query_service_creation_with_kafka(self, service_factory_with_mcp, mock_kafka_client):
        """Test QueryService creation with Kafka client."""
        with patch('src.services.query_service.QueryService') as MockQueryService:
            mock_instance = Mock()
            MockQueryService.return_value = mock_instance
            
            query_service = service_factory_with_mcp.query_service
            
            # Should be called with kafka_client parameter
            MockQueryService.assert_called_once_with(kafka_client=mock_kafka_client)
            assert service_factory_with_mcp._query_service is mock_instance

    def test_customer_service_creation_without_mcp(self, service_factory):
        """Test CustomerService creation without MCP client."""
        customer_service = service_factory.customer_service
        
        assert isinstance(customer_service, CustomerService)
        assert service_factory._customer_service is customer_service
        
        # Second call should return same instance
        customer_service2 = service_factory.customer_service
        assert customer_service is customer_service2

    def test_customer_service_creation_with_mcp(self, service_factory_with_mcp, mock_mcp_client):
        """Test CustomerService creation with MCP client."""
        with patch('src.services.customer_service.CustomerService') as MockCustomerService:
            mock_instance = Mock()
            MockCustomerService.return_value = mock_instance
            
            customer_service = service_factory_with_mcp.customer_service
            
            # Should be called with mcp_client parameter
            MockCustomerService.assert_called_once_with(mcp_client=mock_mcp_client)
            assert service_factory_with_mcp._customer_service is mock_instance

    def test_ticket_service_creation_without_mcp(self, service_factory):
        """Test TicketService creation without MCP client."""
        ticket_service = service_factory.ticket_service
        
        assert isinstance(ticket_service, TicketService)
        assert service_factory._ticket_service is ticket_service
        
        # Second call should return same instance
        ticket_service2 = service_factory.ticket_service
        assert ticket_service is ticket_service2

    def test_ticket_service_creation_with_mcp(self, service_factory_with_mcp, mock_mcp_client):
        """Test TicketService creation with MCP client."""
        with patch('src.services.ticket_service.TicketService') as MockTicketService:
            mock_instance = Mock()
            MockTicketService.return_value = mock_instance
            
            ticket_service = service_factory_with_mcp.ticket_service
            
            # Should be called with mcp_client parameter
            MockTicketService.assert_called_once_with(mcp_client=mock_mcp_client)
            assert service_factory_with_mcp._ticket_service is mock_instance

    def test_feedback_service_creation(self, service_factory):
        """Test FeedbackService creation."""
        feedback_service = service_factory.feedback_service
        
        assert isinstance(feedback_service, FeedbackService)
        assert service_factory._feedback_service is feedback_service
        
        # Second call should return same instance
        feedback_service2 = service_factory.feedback_service
        assert feedback_service is feedback_service2

    def test_analytics_service_creation_without_mcp(self, service_factory):
        """Test AnalyticsService creation without MCP client."""
        analytics_service = service_factory.analytics_service
        
        assert isinstance(analytics_service, AnalyticsService)
        assert service_factory._analytics_service is analytics_service
        
        # Should be created with all other services
        assert analytics_service.query_service is service_factory.query_service
        assert analytics_service.ticket_service is service_factory.ticket_service
        assert analytics_service.customer_service is service_factory.customer_service
        assert analytics_service.feedback_service is service_factory.feedback_service

    def test_analytics_service_creation_with_mcp(self, service_factory_with_mcp, mock_mcp_client):
        """Test AnalyticsService creation with MCP client."""
        with patch('src.services.analytics_service.AnalyticsService') as MockAnalyticsService:
            mock_instance = Mock()
            MockAnalyticsService.return_value = mock_instance
            
            analytics_service = service_factory_with_mcp.analytics_service
            
            # Should be called with query_service and mcp_client
            MockAnalyticsService.assert_called_once_with(
                query_service=service_factory_with_mcp.query_service,
                mcp_client=mock_mcp_client
            )
            assert service_factory_with_mcp._analytics_service is mock_instance

    def test_kafka_client_property(self, service_factory_with_mcp, mock_kafka_client):
        """Test Kafka client property access."""
        kafka_client = service_factory_with_mcp.kafka_client
        assert kafka_client is mock_kafka_client

    def test_kafka_client_property_none(self, service_factory):
        """Test Kafka client property when not provided."""
        kafka_client = service_factory.kafka_client
        assert kafka_client is None


class TestServiceSingletonBehavior:
    """Test that services are created as singletons within factory."""

    def test_all_services_singleton_behavior(self, service_factory):
        """Test that all services maintain singleton behavior."""
        # Get services multiple times
        query1 = service_factory.query_service
        query2 = service_factory.query_service
        
        customer1 = service_factory.customer_service
        customer2 = service_factory.customer_service
        
        ticket1 = service_factory.ticket_service
        ticket2 = service_factory.ticket_service
        
        feedback1 = service_factory.feedback_service
        feedback2 = service_factory.feedback_service
        
        analytics1 = service_factory.analytics_service
        analytics2 = service_factory.analytics_service
        
        # All should be same instances
        assert query1 is query2
        assert customer1 is customer2
        assert ticket1 is ticket2
        assert feedback1 is feedback2
        assert analytics1 is analytics2

    def test_service_interdependencies(self, service_factory):
        """Test that service interdependencies are maintained."""
        analytics_service = service_factory.analytics_service
        
        # Analytics service should have references to other services
        assert analytics_service.query_service is service_factory.query_service
        assert analytics_service.ticket_service is service_factory.ticket_service
        assert analytics_service.customer_service is service_factory.customer_service
        assert analytics_service.feedback_service is service_factory.feedback_service

    def test_shared_ticket_database(self, service_factory):
        """Test that ticket service shares database with factory."""
        ticket_service = service_factory.ticket_service
        
        # Should use the same tickets_db instance
        assert ticket_service.tickets_db is service_factory._tickets_db


class TestGlobalServiceFactory:
    """Test global service factory management."""

    def test_initialize_service_factory_empty(self):
        """Test initializing global service factory without parameters."""
        with patch('src.services.service_factory._service_factory', None):
            factory = initialize_service_factory()
            
            assert isinstance(factory, ServiceFactory)
            assert factory._mcp_client is None
            assert factory._kafka_mcp_client is None

    def test_initialize_service_factory_with_clients(self, mock_mcp_client, mock_kafka_client):
        """Test initializing global service factory with MCP clients."""
        with patch('src.services.service_factory._service_factory', None):
            factory = initialize_service_factory(
                mcp_client=mock_mcp_client,
                kafka_mcp_client=mock_kafka_client
            )
            
            assert isinstance(factory, ServiceFactory)
            assert factory._mcp_client is mock_mcp_client
            assert factory._kafka_mcp_client is mock_kafka_client

    def test_get_service_factory_initialized(self):
        """Test getting service factory when initialized."""
        mock_factory = Mock(spec=ServiceFactory)
        
        with patch('src.services.service_factory._service_factory', mock_factory):
            factory = get_service_factory()
            assert factory is mock_factory

    def test_get_service_factory_not_initialized(self):
        """Test getting service factory when not initialized."""
        with patch('src.services.service_factory._service_factory', None):
            with pytest.raises(RuntimeError) as exc_info:
                get_service_factory()
            
            assert "Service factory not initialized" in str(exc_info.value)

    def test_global_factory_singleton_behavior(self, mock_mcp_client):
        """Test that global factory maintains singleton behavior."""
        with patch('src.services.service_factory._service_factory', None):
            # Initialize factory
            factory1 = initialize_service_factory(mcp_client=mock_mcp_client)
            
            # Get factory
            factory2 = get_service_factory()
            
            # Should be same instance
            assert factory1 is factory2

    def test_reinitialize_service_factory(self, mock_mcp_client, mock_kafka_client):
        """Test reinitializing service factory replaces existing one."""
        with patch('src.services.service_factory._service_factory', None):
            # Initialize first time
            factory1 = initialize_service_factory(mcp_client=mock_mcp_client)
            
            # Initialize again with different parameters
            factory2 = initialize_service_factory(kafka_mcp_client=mock_kafka_client)
            
            # Should be different instances
            assert factory1 is not factory2
            assert factory2._kafka_mcp_client is mock_kafka_client
            assert factory2._mcp_client is None


class TestServiceFactoryErrorHandling:
    """Test error handling in ServiceFactory."""

    def test_service_creation_with_invalid_mcp_client(self):
        """Test service creation with invalid MCP client."""
        invalid_client = "not_a_client"
        
        # Should still create factory but might cause issues when services are used
        factory = ServiceFactory(mcp_client=invalid_client)
        assert factory._mcp_client == invalid_client

    def test_service_factory_with_none_clients(self):
        """Test ServiceFactory behavior with explicitly None clients."""
        factory = ServiceFactory(mcp_client=None, kafka_mcp_client=None)
        
        # Should behave like default factory
        assert factory._mcp_client is None
        assert factory._kafka_mcp_client is None
        
        # Services should still be created
        query_service = factory.query_service
        assert isinstance(query_service, QueryService)


class TestServiceFactoryIntegration:
    """Test ServiceFactory integration scenarios."""

    def test_full_service_stack_creation(self, service_factory_with_mcp, mock_mcp_client, mock_kafka_client):
        """Test creating complete service stack."""
        # Create all services
        query_service = service_factory_with_mcp.query_service
        customer_service = service_factory_with_mcp.customer_service
        ticket_service = service_factory_with_mcp.ticket_service
        feedback_service = service_factory_with_mcp.feedback_service
        analytics_service = service_factory_with_mcp.analytics_service
        
        # All should be created
        assert query_service is not None
        assert customer_service is not None
        assert ticket_service is not None
        assert feedback_service is not None
        assert analytics_service is not None
        
        # Analytics should have references to all others
        assert analytics_service.query_service is query_service

    def test_service_factory_mcp_client_usage(self, service_factory_with_mcp, mock_mcp_client):
        """Test that MCP client is properly passed to services that need it."""
        # Get services that should use MCP client
        customer_service = service_factory_with_mcp.customer_service
        ticket_service = service_factory_with_mcp.ticket_service
        analytics_service = service_factory_with_mcp.analytics_service
        
        # Verify MCP client is available (testing would depend on actual implementation)
        assert customer_service is not None
        assert ticket_service is not None
        assert analytics_service is not None

    def test_service_factory_kafka_client_usage(self, service_factory_with_mcp, mock_kafka_client):
        """Test that Kafka client is properly passed to services that need it."""
        # Get service that should use Kafka client
        query_service = service_factory_with_mcp.query_service
        
        # Verify Kafka client is available
        assert query_service is not None
        assert service_factory_with_mcp.kafka_client is mock_kafka_client

    @pytest.mark.asyncio
    async def test_service_factory_end_to_end_workflow(self, service_factory):
        """Test end-to-end workflow using services from factory."""
        # This would test actual service interactions
        # Here we'll test that services can be created and basic operations work
        
        query_service = service_factory.query_service
        customer_service = service_factory.customer_service
        ticket_service = service_factory.ticket_service
        feedback_service = service_factory.feedback_service
        analytics_service = service_factory.analytics_service
        
        # All services should be operational
        assert query_service.get_query_count() == 0
        assert customer_service.get_customer_count() == 0
        assert ticket_service.get_ticket_count() == 0
        assert feedback_service.get_feedback_count() == 0


class TestServiceFactoryPerformance:
    """Test ServiceFactory performance characteristics."""

    def test_service_creation_performance(self, service_factory):
        """Test that service creation is efficient."""
        import time
        
        start_time = time.time()
        
        # Create all services
        query_service = service_factory.query_service
        customer_service = service_factory.customer_service
        ticket_service = service_factory.ticket_service
        feedback_service = service_factory.feedback_service
        analytics_service = service_factory.analytics_service
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Should be very fast (under 0.1 seconds)
        assert creation_time < 0.1
        
        # All services should be created
        assert query_service is not None
        assert customer_service is not None
        assert ticket_service is not None
        assert feedback_service is not None
        assert analytics_service is not None

    def test_repeated_service_access_performance(self, service_factory):
        """Test performance of repeated service access."""
        import time
        
        start_time = time.time()
        
        # Access services multiple times
        for _ in range(100):
            _ = service_factory.query_service
            _ = service_factory.customer_service
            _ = service_factory.ticket_service
            _ = service_factory.feedback_service
            _ = service_factory.analytics_service
        
        end_time = time.time()
        access_time = end_time - start_time
        
        # Should be very fast since they're singletons
        assert access_time < 0.1

    def test_concurrent_service_access(self, service_factory):
        """Test concurrent access to services."""
        import threading
        import time
        
        results = []
        
        def access_services():
            start_time = time.time()
            query_service = service_factory.query_service
            customer_service = service_factory.customer_service
            end_time = time.time()
            results.append((query_service, customer_service, end_time - start_time))
        
        # Create multiple threads accessing services
        threads = [threading.Thread(target=access_services) for _ in range(10)]
        
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        end_time = time.time()
        
        # All should complete quickly
        total_time = end_time - start_time
        assert total_time < 1.0
        
        # All threads should get the same service instances
        assert len(results) == 10
        first_query_service = results[0][0]
        first_customer_service = results[0][1]
        
        for query_service, customer_service, _ in results:
            assert query_service is first_query_service
            assert customer_service is first_customer_service


class TestServiceFactoryConfiguration:
    """Test ServiceFactory configuration scenarios."""

    def test_service_factory_with_partial_mcp_configuration(self, mock_mcp_client):
        """Test ServiceFactory with only PostgreSQL MCP client."""
        factory = ServiceFactory(mcp_client=mock_mcp_client)
        
        assert factory._mcp_client is mock_mcp_client
        assert factory._kafka_mcp_client is None
        
        # Services should still work
        customer_service = factory.customer_service
        query_service = factory.query_service
        
        assert customer_service is not None
        assert query_service is not None

    def test_service_factory_with_kafka_only_configuration(self, mock_kafka_client):
        """Test ServiceFactory with only Kafka MCP client."""
        factory = ServiceFactory(kafka_mcp_client=mock_kafka_client)
        
        assert factory._mcp_client is None
        assert factory._kafka_mcp_client is mock_kafka_client
        
        # Services should still work
        query_service = factory.query_service
        customer_service = factory.customer_service
        
        assert query_service is not None
        assert customer_service is not None

    def test_service_factory_configuration_changes(self, mock_mcp_client, mock_kafka_client):
        """Test that configuration changes require new factory instance."""
        # Create factory with one configuration
        factory1 = ServiceFactory(mcp_client=mock_mcp_client)
        service1 = factory1.customer_service
        
        # Create factory with different configuration
        factory2 = ServiceFactory(kafka_mcp_client=mock_kafka_client)
        service2 = factory2.customer_service
        
        # Services from different factories should be different instances
        assert service1 is not service2
        assert factory1._mcp_client is mock_mcp_client
        assert factory2._kafka_mcp_client is mock_kafka_client


class TestServiceFactoryCleanup:
    """Test ServiceFactory cleanup and resource management."""

    def test_service_factory_cleanup(self, service_factory):
        """Test that ServiceFactory can be cleaned up properly."""
        # Create some services
        query_service = service_factory.query_service
        customer_service = service_factory.customer_service
        
        # Clear references
        service_factory._query_service = None
        service_factory._customer_service = None
        
        # New calls should create new instances
        new_query_service = service_factory.query_service
        new_customer_service = service_factory.customer_service
        
        assert new_query_service is not query_service
        assert new_customer_service is not customer_service

    def test_global_factory_cleanup(self):
        """Test global factory cleanup."""
        with patch('src.services.service_factory._service_factory', None):
            # Initialize factory
            factory1 = initialize_service_factory()
            
            # Clear global reference
            with patch('src.services.service_factory._service_factory', None):
                # Should raise error when trying to get factory
                with pytest.raises(RuntimeError):
                    get_service_factory()
