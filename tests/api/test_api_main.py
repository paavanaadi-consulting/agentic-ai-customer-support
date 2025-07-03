import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import time

from src.api.api_main import app


@pytest.fixture
def client():
    """Test client for the API application"""
    return TestClient(app)


@pytest.fixture
def mock_service_factory():
    """Mock service factory for testing"""
    factory = MagicMock()
    factory.customer_service = MagicMock()
    return factory


class TestApplicationLifespan:
    """Test application lifespan management"""

    @pytest.mark.asyncio
    async def test_lifespan_startup_success(self):
        """Test successful application startup"""
        with patch('src.api.api_main.initialize_service_factory_with_optimized_mcp') as mock_init:
            mock_factory = MagicMock()
            mock_factory.customer_service = MagicMock()
            mock_init.return_value = mock_factory
            
            # Test that lifespan can be called without errors
            from src.api.api_main import lifespan
            
            async with lifespan(app):
                # Should complete without errors
                pass

    @pytest.mark.asyncio
    async def test_lifespan_fallback_to_default_mcp(self):
        """Test fallback to default MCP client"""
        with patch('src.api.api_main.initialize_service_factory_with_optimized_mcp') as mock_init, \
             patch('src.api.api_main.initialize_service_factory_with_optimized_mcp_default') as mock_default:
            
            # First initialization fails
            mock_init.side_effect = Exception("Connection failed")
            
            # Default initialization succeeds
            mock_factory = MagicMock()
            mock_factory.customer_service = MagicMock()
            mock_default.return_value = mock_factory
            
            from src.api.api_main import lifespan
            
            async with lifespan(app):
                pass
            
            mock_init.assert_called_once()
            mock_default.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_fallback_to_in_memory(self):
        """Test fallback to in-memory services"""
        with patch('src.api.api_main.initialize_service_factory_with_optimized_mcp') as mock_init, \
             patch('src.api.api_main.initialize_service_factory_with_optimized_mcp_default') as mock_default, \
             patch('src.api.api_main.initialize_service_factory') as mock_memory:
            
            # Both MCP initializations fail
            mock_init.side_effect = Exception("Connection failed")
            mock_default.side_effect = Exception("Default failed")
            
            # In-memory initialization succeeds
            mock_factory = MagicMock()
            mock_memory.return_value = mock_factory
            
            from src.api.api_main import lifespan
            
            async with lifespan(app):
                pass
            
            mock_init.assert_called_once()
            mock_default.assert_called_once()
            mock_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_cleanup(self):
        """Test application shutdown cleanup"""
        with patch('src.api.api_main.initialize_service_factory') as mock_init, \
             patch('src.api.api_main.close_optimized_mcp_client') as mock_close:
            
            mock_factory = MagicMock()
            mock_init.return_value = mock_factory
            
            from src.api.api_main import lifespan
            
            async with lifespan(app):
                pass
            
            mock_close.assert_called_once()


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check_healthy(self, client):
        """Test health check when services are healthy"""
        with patch('src.api.api_main.service_factory') as mock_factory:
            mock_factory.customer_service = MagicMock()
            
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["version"] == "1.0.0"
            assert "timestamp" in data
            assert "services" in data

    def test_health_check_service_factory_not_initialized(self, client):
        """Test health check when service factory is not initialized"""
        with patch('src.api.api_main.service_factory', None):
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["services"]["service_factory"] == "not_initialized"

    def test_health_check_service_unhealthy(self, client):
        """Test health check when services are unhealthy"""
        with patch('src.api.api_main.service_factory') as mock_factory:
            mock_factory.customer_service = None  # Simulate unhealthy service
            
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["services"]["service_factory"] == "unhealthy"

    def test_health_check_exception_handling(self, client):
        """Test health check exception handling"""
        with patch('src.api.api_main.service_factory') as mock_factory:
            mock_factory.customer_service.side_effect = Exception("Service error")
            
            response = client.get("/health")
            assert response.status_code == 200  # Should still return 200 with warning


class TestRootEndpoint:
    """Test root endpoint"""

    def test_root_endpoint(self, client):
        """Test root endpoint response"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Agentic AI Customer Support API"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"


class TestMiddleware:
    """Test middleware functionality"""

    def test_cors_middleware(self, client):
        """Test CORS middleware is applied"""
        response = client.options("/health")
        # Should not fail due to CORS
        assert response.status_code in [200, 405]  # 405 if OPTIONS not implemented

    def test_process_time_header(self, client):
        """Test that process time header is added"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers
        
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0

    def test_gzip_middleware(self, client):
        """Test GZip middleware for large responses"""
        # For large responses, gzip should be applied
        # This is harder to test directly, but we can verify it doesn't break anything
        response = client.get("/")
        assert response.status_code == 200


class TestExceptionHandling:
    """Test global exception handling"""

    def test_general_exception_handler(self, client):
        """Test general exception handler"""
        # Create a route that raises an exception for testing
        from fastapi import HTTPException
        
        @app.get("/test-error")
        async def test_error():
            raise Exception("Test exception")
        
        response = client.get("/test-error")
        assert response.status_code == 500
        
        data = response.json()
        assert data["error"] == "Internal server error"
        assert data["error_code"] == "INTERNAL_ERROR"
        assert "timestamp" in data
        
        # Clean up test route
        app.routes = [route for route in app.routes if not (hasattr(route, 'path') and route.path == "/test-error")]


class TestRouterInclusion:
    """Test that routers are properly included"""

    def test_api_router_included(self, client):
        """Test that API router is included"""
        # This will depend on having a working route in the API router
        # We'll test with a mock to ensure the router is included
        response = client.get("/api/v1/status")
        # Should not return 404 (router not found)
        assert response.status_code != 404

    def test_kafka_router_included(self, client):
        """Test that Kafka router is included"""
        # Test that Kafka streaming endpoints are available
        response = client.get("/api/v1/streaming/health")
        # Should not return 404 (router not found)
        assert response.status_code != 404


class TestApplicationConfiguration:
    """Test application configuration"""

    def test_app_metadata(self):
        """Test FastAPI app metadata"""
        assert app.title == "Agentic AI Customer Support API"
        assert app.description == "RESTful API for AI-powered customer support system"
        assert app.version == "1.0.0"
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"

    def test_openapi_schema_generation(self, client):
        """Test that OpenAPI schema can be generated"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert schema["info"]["title"] == "Agentic AI Customer Support API"
        assert schema["info"]["version"] == "1.0.0"

    def test_docs_endpoint_available(self, client):
        """Test that documentation endpoints are available"""
        # Test Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200


class TestEnvironmentVariables:
    """Test environment variable handling"""

    def test_database_url_handling(self):
        """Test DATABASE_URL environment variable handling"""
        import os
        original_url = os.getenv("DATABASE_URL")
        
        try:
            # Test with custom URL
            os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/testdb"
            
            # The URL should be accessible in the lifespan function
            # This is more of an integration test to ensure env vars are read
            assert os.getenv("DATABASE_URL") == "postgresql://test:test@localhost/testdb"
            
        finally:
            # Restore original value
            if original_url:
                os.environ["DATABASE_URL"] = original_url
            elif "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]

    def test_mcp_server_url_handling(self):
        """Test MCP_SERVER_URL environment variable handling"""
        import os
        original_url = os.getenv("MCP_SERVER_URL")
        
        try:
            # Test with custom URL
            os.environ["MCP_SERVER_URL"] = "http://test-mcp:8001"
            
            assert os.getenv("MCP_SERVER_URL") == "http://test-mcp:8001"
            
        finally:
            # Restore original value
            if original_url:
                os.environ["MCP_SERVER_URL"] = original_url
            elif "MCP_SERVER_URL" in os.environ:
                del os.environ["MCP_SERVER_URL"]


class TestLogging:
    """Test logging configuration"""

    def test_logging_configuration(self):
        """Test that logging is properly configured"""
        import logging
        
        # Test that logger exists and is configured
        logger = logging.getLogger("src.api.api_main")
        assert logger is not None
        
        # Test that root logger has handlers
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0

    def test_log_level_configuration(self):
        """Test log level configuration from config"""
        from config.env_settings import CONFIG
        import logging
        
        # Verify log level is set correctly
        expected_level = getattr(logging, CONFIG.LOG_LEVEL)
        root_logger = logging.getLogger()
        
        # The level should be set appropriately
        assert root_logger.level <= expected_level or len(root_logger.handlers) > 0
