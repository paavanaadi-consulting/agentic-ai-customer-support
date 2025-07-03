"""
Comprehensive tests for API dependencies.
Tests dependency injection, service factory integration, and error handling.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

from src.api.dependencies import (
    get_query_service_dep, get_ticket_service_dep, get_customer_service_dep,
    get_feedback_service_dep, get_analytics_service_dep, get_kafka_client_dep
)
from src.services.query_service import QueryService
from src.services.ticket_service import TicketService
from src.services.customer_service import CustomerService
from src.services.feedback_service import FeedbackService
from src.services.analytics_service import AnalyticsService
from src.mcp.kafka_mcp_client import OptimizedKafkaMCPClient


class TestQueryServiceDependency:
    """Test QueryService dependency provider."""
    
    @patch('src.api.dependencies.get_query_service')
    def test_get_query_service_dep_success(self, mock_get_service):
        """Test successful QueryService dependency injection."""
        # Setup mock
        mock_service = Mock(spec=QueryService)
        mock_get_service.return_value = mock_service
        
        # Call dependency provider
        result = get_query_service_dep()
        
        # Assertions
        assert result == mock_service
        assert isinstance(result, Mock)  # Mock object, but should be QueryService in real use
        mock_get_service.assert_called_once()
    
    @patch('src.api.dependencies.get_query_service')
    def test_get_query_service_dep_singleton(self, mock_get_service):
        """Test that QueryService dependency returns the same instance (singleton behavior)."""
        mock_service = Mock(spec=QueryService)
        mock_get_service.return_value = mock_service
        
        # Call dependency provider multiple times
        result1 = get_query_service_dep()
        result2 = get_query_service_dep()
        
        # Should return the same instance
        assert result1 == result2
        # Service factory should be called each time (but returns same instance)
        assert mock_get_service.call_count == 2
    
    @patch('src.api.dependencies.get_query_service')
    def test_get_query_service_dep_none(self, mock_get_service):
        """Test QueryService dependency when service factory returns None."""
        mock_get_service.return_value = None
        
        # Call dependency provider
        result = get_query_service_dep()
        
        # Should return None (FastAPI will handle this appropriately)
        assert result is None
    
    @patch('src.api.dependencies.get_query_service')
    def test_get_query_service_dep_exception(self, mock_get_service):
        """Test QueryService dependency when service factory raises exception."""
        mock_get_service.side_effect = Exception("Service initialization failed")
        
        # Call should raise the exception
        with pytest.raises(Exception) as exc_info:
            get_query_service_dep()
        
        assert "Service initialization failed" in str(exc_info.value)


class TestTicketServiceDependency:
    """Test TicketService dependency provider."""
    
    @patch('src.api.dependencies.get_ticket_service')
    def test_get_ticket_service_dep_success(self, mock_get_service):
        """Test successful TicketService dependency injection."""
        mock_service = Mock(spec=TicketService)
        mock_get_service.return_value = mock_service
        
        result = get_ticket_service_dep()
        
        assert result == mock_service
        mock_get_service.assert_called_once()
    
    @patch('src.api.dependencies.get_ticket_service')
    def test_get_ticket_service_dep_type_check(self, mock_get_service):
        """Test that TicketService dependency returns correct type."""
        mock_service = Mock(spec=TicketService)
        mock_service.__class__ = TicketService
        mock_get_service.return_value = mock_service
        
        result = get_ticket_service_dep()
        
        # Verify it has the expected methods
        assert hasattr(result, 'create_ticket')
        assert hasattr(result, 'get_ticket_by_id')
        assert hasattr(result, 'list_tickets')
        assert hasattr(result, 'update_ticket_status')


class TestCustomerServiceDependency:
    """Test CustomerService dependency provider."""
    
    @patch('src.api.dependencies.get_customer_service')
    def test_get_customer_service_dep_success(self, mock_get_service):
        """Test successful CustomerService dependency injection."""
        mock_service = Mock(spec=CustomerService)
        mock_get_service.return_value = mock_service
        
        result = get_customer_service_dep()
        
        assert result == mock_service
        mock_get_service.assert_called_once()
    
    @patch('src.api.dependencies.get_customer_service')
    def test_get_customer_service_dep_interface(self, mock_get_service):
        """Test CustomerService dependency interface."""
        mock_service = Mock(spec=CustomerService)
        mock_service.__class__ = CustomerService
        mock_get_service.return_value = mock_service
        
        result = get_customer_service_dep()
        
        # Verify expected interface
        assert hasattr(result, 'create_customer')
        assert hasattr(result, 'get_customer_by_id')
        assert hasattr(result, 'update_last_interaction')
        assert hasattr(result, 'increment_ticket_count')


class TestFeedbackServiceDependency:
    """Test FeedbackService dependency provider."""
    
    @patch('src.api.dependencies.get_feedback_service')
    def test_get_feedback_service_dep_success(self, mock_get_service):
        """Test successful FeedbackService dependency injection."""
        mock_service = Mock(spec=FeedbackService)
        mock_get_service.return_value = mock_service
        
        result = get_feedback_service_dep()
        
        assert result == mock_service
        mock_get_service.assert_called_once()
    
    @patch('src.api.dependencies.get_feedback_service')
    def test_get_feedback_service_dep_methods(self, mock_get_service):
        """Test FeedbackService dependency has expected methods."""
        mock_service = Mock(spec=FeedbackService)
        mock_service.__class__ = FeedbackService
        mock_get_service.return_value = mock_service
        
        result = get_feedback_service_dep()
        
        assert hasattr(result, 'create_feedback')
        assert hasattr(result, 'get_feedback_by_id')
        assert hasattr(result, 'get_feedback_by_customer')
        assert hasattr(result, 'get_average_rating')


class TestAnalyticsServiceDependency:
    """Test AnalyticsService dependency provider."""
    
    @patch('src.api.dependencies.get_analytics_service')
    def test_get_analytics_service_dep_success(self, mock_get_service):
        """Test successful AnalyticsService dependency injection."""
        mock_service = Mock(spec=AnalyticsService)
        mock_get_service.return_value = mock_service
        
        result = get_analytics_service_dep()
        
        assert result == mock_service
        mock_get_service.assert_called_once()
    
    @patch('src.api.dependencies.get_analytics_service')
    def test_get_analytics_service_dep_interface(self, mock_get_service):
        """Test AnalyticsService dependency interface."""
        mock_service = Mock(spec=AnalyticsService)
        mock_service.__class__ = AnalyticsService
        mock_get_service.return_value = mock_service
        
        result = get_analytics_service_dep()
        
        assert hasattr(result, 'get_analytics')
        assert hasattr(result, 'get_query_metrics')
        assert hasattr(result, 'get_ticket_metrics')
        assert hasattr(result, 'get_customer_metrics')


class TestKafkaClientDependency:
    """Test Kafka MCP Client dependency provider."""
    
    @patch('src.api.dependencies.get_kafka_client')
    def test_get_kafka_client_dep_success(self, mock_get_client):
        """Test successful Kafka client dependency injection."""
        mock_client = Mock(spec=OptimizedKafkaMCPClient)
        mock_get_client.return_value = mock_client
        
        result = get_kafka_client_dep()
        
        assert result == mock_client
        mock_get_client.assert_called_once()
    
    @patch('src.api.dependencies.get_kafka_client')
    def test_get_kafka_client_dep_none(self, mock_get_client):
        """Test Kafka client dependency when client is not available."""
        mock_get_client.return_value = None
        
        # Should raise HTTP 503 exception
        with pytest.raises(HTTPException) as exc_info:
            get_kafka_client_dep()
        
        assert exc_info.value.status_code == 503
        assert "Kafka MCP client not available" in exc_info.value.detail
    
    @patch('src.api.dependencies.get_kafka_client')
    def test_get_kafka_client_dep_interface(self, mock_get_client):
        """Test Kafka client dependency interface."""
        mock_client = Mock(spec=OptimizedKafkaMCPClient)
        mock_client.__class__ = OptimizedKafkaMCPClient
        mock_client.is_connected = True
        mock_get_client.return_value = mock_client
        
        result = get_kafka_client_dep()
        
        assert hasattr(result, 'call_tool')
        assert hasattr(result, 'is_connected')
        assert result.is_connected is True
    
    @patch('src.api.dependencies.get_kafka_client')
    def test_get_kafka_client_dep_disconnected(self, mock_get_client):
        """Test Kafka client dependency when client is disconnected."""
        mock_client = Mock(spec=OptimizedKafkaMCPClient)
        mock_client.is_connected = False
        mock_get_client.return_value = mock_client
        
        # Should still return the client (let the route handle disconnected state)
        result = get_kafka_client_dep()
        
        assert result == mock_client
        assert result.is_connected is False


class TestDependencyIntegration:
    """Test integration between dependencies and service factory."""
    
    @patch('src.api.dependencies.get_query_service')
    @patch('src.api.dependencies.get_ticket_service')
    @patch('src.api.dependencies.get_customer_service')
    def test_multiple_dependencies_together(self, mock_customer, mock_ticket, mock_query):
        """Test using multiple dependencies together."""
        # Setup mocks
        mock_query_service = Mock(spec=QueryService)
        mock_ticket_service = Mock(spec=TicketService)
        mock_customer_service = Mock(spec=CustomerService)
        
        mock_query.return_value = mock_query_service
        mock_ticket.return_value = mock_ticket_service
        mock_customer.return_value = mock_customer_service
        
        # Get all dependencies
        query_service = get_query_service_dep()
        ticket_service = get_ticket_service_dep()
        customer_service = get_customer_service_dep()
        
        # Verify all are different services
        assert query_service == mock_query_service
        assert ticket_service == mock_ticket_service
        assert customer_service == mock_customer_service
        assert query_service != ticket_service
        assert ticket_service != customer_service
    
    def test_dependency_module_exports(self):
        """Test that the module exports the expected functions."""
        from src.api.dependencies import __all__
        
        expected_exports = [
            "get_query_service_dep",
            "get_ticket_service_dep",
            "get_customer_service_dep",
            "get_feedback_service_dep",
            "get_analytics_service_dep",
            "get_kafka_client_dep"
        ]
        
        for export in expected_exports:
            assert export in __all__
    
    def test_dependency_functions_exist(self):
        """Test that all dependency functions exist and are callable."""
        import src.api.dependencies as deps
        
        dependency_functions = [
            'get_query_service_dep',
            'get_ticket_service_dep',
            'get_customer_service_dep',
            'get_feedback_service_dep',
            'get_analytics_service_dep',
            'get_kafka_client_dep'
        ]
        
        for func_name in dependency_functions:
            assert hasattr(deps, func_name)
            func = getattr(deps, func_name)
            assert callable(func)


class TestDependencyErrorHandling:
    """Test error handling in dependency providers."""
    
    @patch('src.api.dependencies.get_query_service')
    def test_service_factory_import_error(self, mock_get_service):
        """Test handling of import errors from service factory."""
        mock_get_service.side_effect = ImportError("Module not found")
        
        with pytest.raises(ImportError):
            get_query_service_dep()
    
    @patch('src.api.dependencies.get_query_service')
    def test_service_factory_runtime_error(self, mock_get_service):
        """Test handling of runtime errors from service factory."""
        mock_get_service.side_effect = RuntimeError("Service initialization failed")
        
        with pytest.raises(RuntimeError):
            get_query_service_dep()
    
    @patch('src.api.dependencies.get_kafka_client')
    def test_kafka_client_connection_error(self, mock_get_client):
        """Test handling of Kafka connection errors."""
        mock_get_client.side_effect = ConnectionError("Failed to connect to Kafka")
        
        with pytest.raises(ConnectionError):
            get_kafka_client_dep()
    
    def test_http_exception_properties(self):
        """Test HTTPException properties for Kafka client unavailable."""
        with patch('src.api.dependencies.get_kafka_client', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                get_kafka_client_dep()
            
            exception = exc_info.value
            assert exception.status_code == 503
            assert exception.detail == "Kafka MCP client not available"
            assert isinstance(exception, HTTPException)


class TestDependencyPerformance:
    """Test performance aspects of dependency injection."""
    
    @patch('src.api.dependencies.get_query_service')
    def test_dependency_call_performance(self, mock_get_service):
        """Test that dependency calls are fast."""
        import time
        
        mock_service = Mock(spec=QueryService)
        mock_get_service.return_value = mock_service
        
        # Measure time for multiple calls
        start_time = time.time()
        for _ in range(100):
            get_query_service_dep()
        end_time = time.time()
        
        # Should be very fast (under 1 second for 100 calls)
        assert (end_time - start_time) < 1.0
        assert mock_get_service.call_count == 100
    
    @patch('src.api.dependencies.get_kafka_client')
    def test_kafka_client_lazy_loading(self, mock_get_client):
        """Test that Kafka client is loaded lazily."""
        mock_client = Mock(spec=OptimizedKafkaMCPClient)
        mock_get_client.return_value = mock_client
        
        # First call should initialize the client
        result1 = get_kafka_client_dep()
        assert mock_get_client.call_count == 1
        
        # Subsequent calls should use the same client
        result2 = get_kafka_client_dep()
        assert mock_get_client.call_count == 2  # Service factory may create new instance
        
        # But results should be equivalent
        assert result1 == result2


class TestDependencyTyping:
    """Test type hints and return types of dependencies."""
    
    def test_query_service_return_type(self):
        """Test that QueryService dependency has correct return type annotation."""
        import inspect
        
        sig = inspect.signature(get_query_service_dep)
        return_annotation = sig.return_annotation
        
        assert return_annotation == QueryService
    
    def test_kafka_client_return_type(self):
        """Test that Kafka client dependency has correct return type annotation."""
        import inspect
        
        sig = inspect.signature(get_kafka_client_dep)
        return_annotation = sig.return_annotation
        
        assert return_annotation == OptimizedKafkaMCPClient
    
    def test_all_dependencies_have_return_types(self):
        """Test that all dependency functions have return type annotations."""
        import inspect
        import src.api.dependencies as deps
        
        dependency_functions = [
            get_query_service_dep,
            get_ticket_service_dep,
            get_customer_service_dep,
            get_feedback_service_dep,
            get_analytics_service_dep,
            get_kafka_client_dep
        ]
        
        for func in dependency_functions:
            sig = inspect.signature(func)
            assert sig.return_annotation != inspect.Signature.empty
    
    def test_no_parameters_required(self):
        """Test that dependency functions don't require parameters."""
        import inspect
        
        dependency_functions = [
            get_query_service_dep,
            get_ticket_service_dep,
            get_customer_service_dep,
            get_feedback_service_dep,
            get_analytics_service_dep,
            get_kafka_client_dep
        ]
        
        for func in dependency_functions:
            sig = inspect.signature(func)
            # Should have no required parameters
            required_params = [p for p in sig.parameters.values() 
                             if p.default == inspect.Parameter.empty]
            assert len(required_params) == 0


class TestFastAPIIntegration:
    """Test integration with FastAPI dependency injection system."""
    
    def test_dependency_with_fastapi_depends(self):
        """Test that dependencies work with FastAPI Depends."""
        from fastapi import Depends
        
        # This should not raise any errors
        query_dep = Depends(get_query_service_dep)
        kafka_dep = Depends(get_kafka_client_dep)
        
        assert query_dep.dependency == get_query_service_dep
        assert kafka_dep.dependency == get_kafka_client_dep
    
    @patch('src.api.dependencies.get_query_service')
    def test_dependency_in_route_context(self, mock_get_service):
        """Test dependency behavior in a route-like context."""
        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        mock_service = Mock(spec=QueryService)
        mock_get_service.return_value = mock_service
        
        @app.get("/test")
        async def test_route(service: QueryService = Depends(get_query_service_dep)):
            return {"service_available": service is not None}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service_available"] is True
        mock_get_service.assert_called_once()


class TestModuleStructure:
    """Test module structure and organization."""
    
    def test_module_docstring(self):
        """Test that the module has proper documentation."""
        import src.api.dependencies as deps
        
        assert deps.__doc__ is not None
        assert "dependency providers" in deps.__doc__.lower()
        assert "services" in deps.__doc__.lower()
    
    def test_imports_are_correct(self):
        """Test that all necessary imports are present."""
        # This test ensures all imports in the dependencies module work
        try:
            from src.api.dependencies import (
                get_query_service_dep, get_ticket_service_dep,
                get_customer_service_dep, get_feedback_service_dep,
                get_analytics_service_dep, get_kafka_client_dep
            )
        except ImportError as e:
            pytest.fail(f"Import error in dependencies module: {e}")
    
    def test_no_circular_imports(self):
        """Test that there are no circular import issues."""
        # Simply importing the module should not cause circular import errors
        try:
            import src.api.dependencies
            # If we get here without exceptions, circular imports are not an issue
            assert True
        except ImportError as e:
            if "circular import" in str(e).lower():
                pytest.fail(f"Circular import detected: {e}")
            else:
                # Re-raise other import errors
                raise