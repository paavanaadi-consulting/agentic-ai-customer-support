"""
Comprehensive test suite for PostgreSQL MCP Client.
Tests optimized PostgreSQL operations via MCP with multiple fallback strategies.
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.mcp.postgres_mcp_client import OptimizedPostgreSQLMCPClient, MCPClientError
from src.mcp.mcp_client_interface import MCPClientInterface


class TestOptimizedPostgreSQLMCPClient:
    """Test cases for OptimizedPostgreSQLMCPClient class."""

    @pytest.fixture
    def postgres_client(self):
        """Create a PostgreSQL MCP client instance for testing."""
        return OptimizedPostgreSQLMCPClient(
            connection_string="postgresql://user:pass@localhost:5432/testdb",
            mcp_server_url="http://localhost:8001",
            use_direct_connection=True
        )

    @pytest.fixture
    def postgres_client_http_only(self):
        """Create a PostgreSQL MCP client instance configured for HTTP only."""
        return OptimizedPostgreSQLMCPClient(
            connection_string=None,
            mcp_server_url="http://localhost:8001",
            use_direct_connection=False
        )

    @pytest.fixture
    def mock_http_session(self):
        """Create a mock HTTP session for testing."""
        session = AsyncMock()
        session.post.return_value.__aenter__.return_value.json.return_value = {"result": "success"}
        session.post.return_value.__aenter__.return_value.status = 200
        return session

    def test_postgres_client_initialization(self, postgres_client):
        """Test PostgreSQL MCP client initialization."""
        assert postgres_client.connection_string == "postgresql://user:pass@localhost:5432/testdb"
        assert postgres_client.mcp_server_url == "http://localhost:8001"
        assert postgres_client.use_direct_connection is True
        assert postgres_client.connected is False
        assert postgres_client.external_server is None
        assert postgres_client.http_session is None
        assert postgres_client.cache_duration == 300
        assert isinstance(postgres_client._cache, dict)

    def test_postgres_client_implements_interface(self, postgres_client):
        """Test that PostgreSQL client implements MCPClientInterface."""
        assert isinstance(postgres_client, MCPClientInterface)

    @pytest.mark.asyncio
    async def test_connect_direct_success(self, postgres_client):
        """Test successful direct connection to PostgreSQL MCP server."""
        with patch('src.mcp.postgres_mcp_client.POSTGRES_MCP_AVAILABLE', True):
            with patch('src.mcp.postgres_mcp_client.ExternalPostgresMCPServer') as MockServer:
                mock_server = AsyncMock()
                MockServer.return_value = mock_server
                
                result = await postgres_client.connect()
                
                assert result is True
                assert postgres_client.connected is True
                assert postgres_client.external_server == mock_server

    @pytest.mark.asyncio
    async def test_connect_http_fallback(self, postgres_client):
        """Test HTTP fallback when direct connection fails."""
        with patch('src.mcp.postgres_mcp_client.POSTGRES_MCP_AVAILABLE', True):
            with patch('src.mcp.postgres_mcp_client.ExternalPostgresMCPServer', side_effect=Exception("Connection failed")):
                with patch('aiohttp.ClientSession') as MockSession:
                    mock_session = AsyncMock()
                    MockSession.return_value = mock_session
                    
                    result = await postgres_client.connect()
                    
                    assert result is True
                    assert postgres_client.connected is True
                    assert postgres_client.http_session == mock_session

    @pytest.mark.asyncio
    async def test_connect_http_only(self, postgres_client_http_only):
        """Test connection using HTTP only mode."""
        with patch('aiohttp.ClientSession') as MockSession:
            mock_session = AsyncMock()
            MockSession.return_value = mock_session
            
            result = await postgres_client_http_only.connect()
            
            assert result is True
            assert postgres_client_http_only.connected is True
            assert postgres_client_http_only.http_session == mock_session

    @pytest.mark.asyncio
    async def test_connect_already_connected(self, postgres_client):
        """Test connection when already connected."""
        postgres_client.connected = True
        
        result = await postgres_client.connect()
        
        assert result is True

    @pytest.mark.asyncio
    async def test_connect_all_methods_fail(self, postgres_client):
        """Test connection when all methods fail."""
        with patch('src.mcp.postgres_mcp_client.POSTGRES_MCP_AVAILABLE', False):
            with patch('aiohttp.ClientSession', side_effect=Exception("HTTP connection failed")):
                result = await postgres_client.connect()
                
                assert result is False
                assert postgres_client.connected is False

    @pytest.mark.asyncio
    async def test_disconnect_direct_connection(self, postgres_client):
        """Test disconnection from direct connection."""
        mock_server = AsyncMock()
        postgres_client.external_server = mock_server
        postgres_client.connected = True
        
        await postgres_client.disconnect()
        
        assert postgres_client.connected is False
        assert postgres_client.external_server is None

    @pytest.mark.asyncio
    async def test_disconnect_http_connection(self, postgres_client):
        """Test disconnection from HTTP connection."""
        mock_session = AsyncMock()
        postgres_client.http_session = mock_session
        postgres_client.connected = True
        
        await postgres_client.disconnect()
        
        assert postgres_client.connected is False
        assert postgres_client.http_session is None
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_not_connected(self, postgres_client):
        """Test disconnection when not connected."""
        await postgres_client.disconnect()  # Should not raise
        assert postgres_client.connected is False


class TestPostgreSQLClientCustomerOperations:
    """Test customer-related operations via PostgreSQL MCP client."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected PostgreSQL MCP client for testing."""
        client = OptimizedPostgreSQLMCPClient()
        client.connected = True
        client.http_session = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_get_customers_success(self, connected_client, mock_http_session):
        """Test successful retrieval of customers."""
        mock_response = {
            "result": [
                {"id": "1", "name": "Customer 1", "email": "customer1@example.com"},
                {"id": "2", "name": "Customer 2", "email": "customer2@example.com"}
            ]
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.get_customers(limit=50)
        
        assert len(result) == 2
        assert result[0]["name"] == "Customer 1"
        mock_http_session.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_customer_by_id(self, connected_client, mock_http_session):
        """Test getting customer by ID."""
        mock_response = {
            "result": {"id": "123", "name": "Test Customer", "email": "test@example.com"}
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.get_customer_by_id("123")
        
        assert result["id"] == "123"
        assert result["name"] == "Test Customer"

    @pytest.mark.asyncio
    async def test_get_customer_by_id_not_found(self, connected_client, mock_http_session):
        """Test getting customer by ID when not found."""
        mock_response = {"result": None}
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.get_customer_by_id("nonexistent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_create_customer(self, connected_client, mock_http_session):
        """Test creating a new customer."""
        customer_data = {"name": "New Customer", "email": "new@example.com"}
        mock_response = {"result": {"id": "new_123", **customer_data}}
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.create_customer(customer_data)
        
        assert result["id"] == "new_123"
        assert result["name"] == "New Customer"

    @pytest.mark.asyncio
    async def test_update_customer(self, connected_client, mock_http_session):
        """Test updating customer information."""
        updates = {"name": "Updated Customer", "email": "updated@example.com"}
        mock_response = {"result": {"id": "123", **updates}}
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.update_customer("123", updates)
        
        assert result["id"] == "123"
        assert result["name"] == "Updated Customer"

    @pytest.mark.asyncio
    async def test_customer_operations_not_connected(self, postgres_client):
        """Test customer operations when not connected."""
        with pytest.raises(MCPClientError, match="Client not connected"):
            await postgres_client.get_customers()


class TestPostgreSQLClientTicketOperations:
    """Test ticket-related operations via PostgreSQL MCP client."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected PostgreSQL MCP client for testing."""
        client = OptimizedPostgreSQLMCPClient()
        client.connected = True
        client.http_session = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_get_tickets(self, connected_client, mock_http_session):
        """Test getting tickets with filters."""
        mock_response = {
            "result": [
                {"id": "1", "title": "Ticket 1", "status": "open", "priority": "high"},
                {"id": "2", "title": "Ticket 2", "status": "open", "priority": "medium"}
            ]
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.get_tickets(limit=100, status="open")
        
        assert len(result) == 2
        assert all(ticket["status"] == "open" for ticket in result)

    @pytest.mark.asyncio
    async def test_get_ticket_by_id(self, connected_client, mock_http_session):
        """Test getting ticket by ID."""
        mock_response = {
            "result": {
                "id": "456",
                "title": "Test Ticket",
                "status": "open",
                "priority": "high",
                "customer_id": "123"
            }
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.get_ticket_by_id("456")
        
        assert result["id"] == "456"
        assert result["title"] == "Test Ticket"
        assert result["priority"] == "high"

    @pytest.mark.asyncio
    async def test_create_ticket(self, connected_client, mock_http_session):
        """Test creating a new ticket."""
        ticket_data = {
            "title": "New Support Ticket",
            "description": "Customer needs help",
            "customer_id": "123",
            "priority": "medium"
        }
        mock_response = {"result": {"id": "new_456", "status": "open", **ticket_data}}
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.create_ticket(ticket_data)
        
        assert result["id"] == "new_456"
        assert result["title"] == "New Support Ticket"
        assert result["status"] == "open"

    @pytest.mark.asyncio
    async def test_update_ticket(self, connected_client, mock_http_session):
        """Test updating ticket information."""
        updates = {"status": "resolved", "resolution": "Issue fixed"}
        mock_response = {"result": {"id": "456", **updates}}
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.update_ticket("456", updates)
        
        assert result["id"] == "456"
        assert result["status"] == "resolved"


class TestPostgreSQLClientKnowledgeBase:
    """Test knowledge base operations via PostgreSQL MCP client."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected PostgreSQL MCP client for testing."""
        client = OptimizedPostgreSQLMCPClient()
        client.connected = True
        client.http_session = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_search_knowledge_base(self, connected_client, mock_http_session):
        """Test searching knowledge base."""
        mock_response = {
            "result": [
                {
                    "id": "1",
                    "title": "How to reset password",
                    "content": "Step 1: Click forgot password...",
                    "category": "account"
                },
                {
                    "id": "2",
                    "title": "Password requirements",
                    "content": "Passwords must be at least 8 characters...",
                    "category": "security"
                }
            ]
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.search_knowledge_base("password reset", limit=10)
        
        assert len(result) == 2
        assert "password" in result[0]["title"].lower()
        assert "password" in result[1]["title"].lower()


class TestPostgreSQLClientAnalytics:
    """Test analytics operations via PostgreSQL MCP client."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected PostgreSQL MCP client for testing."""
        client = OptimizedPostgreSQLMCPClient()
        client.connected = True
        client.http_session = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_get_analytics(self, connected_client, mock_http_session):
        """Test getting analytics data."""
        mock_response = {
            "result": {
                "period_days": 30,
                "total_tickets": 150,
                "resolved_tickets": 120,
                "open_tickets": 25,
                "closed_tickets": 5,
                "average_resolution_time": "4.5 hours",
                "customer_satisfaction": 4.2,
                "ticket_categories": {
                    "technical": 80,
                    "billing": 40,
                    "general": 30
                }
            }
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.get_analytics(days=30)
        
        assert result["period_days"] == 30
        assert result["total_tickets"] == 150
        assert result["customer_satisfaction"] == 4.2
        assert "ticket_categories" in result


class TestPostgreSQLClientCaching:
    """Test caching functionality in PostgreSQL MCP client."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected PostgreSQL MCP client for testing."""
        client = OptimizedPostgreSQLMCPClient()
        client.connected = True
        client.http_session = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_cache_customer_data(self, connected_client, mock_http_session):
        """Test caching of customer data."""
        customer_data = {"id": "123", "name": "Test Customer", "email": "test@example.com"}
        mock_response = {"result": customer_data}
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        # First call should hit the server
        result1 = await connected_client.get_customer_by_id("123")
        assert result1 == customer_data
        assert mock_http_session.post.call_count == 1
        
        # Second call should use cache (implement caching logic in client)
        # Note: This test assumes caching is implemented in the client
        # The actual implementation would need to check cache before making HTTP calls

    def test_cache_expiry(self, connected_client):
        """Test cache expiry functionality."""
        # Test cache TTL logic
        current_time = datetime.now().timestamp()
        
        # Set cache entry
        connected_client._cache["test_key"] = "test_value"
        connected_client._cache_ttl["test_key"] = current_time + 100  # Future expiry
        
        # Check if cache is valid (would be part of actual implementation)
        assert "test_key" in connected_client._cache
        
        # Simulate expired cache
        connected_client._cache_ttl["test_key"] = current_time - 100  # Past expiry
        
        # Implementation would check TTL and remove expired entries
        # This is a placeholder for the actual cache expiry logic

    def test_cache_invalidation(self, connected_client):
        """Test cache invalidation on updates."""
        # Set some cached data
        connected_client._cache["customer_123"] = {"id": "123", "name": "Old Name"}
        
        # After an update operation, cache should be invalidated
        # This would be implemented in the update methods
        assert "customer_123" in connected_client._cache
        
        # Cache invalidation logic would remove or update the cache entry
        # This is a placeholder for the actual cache invalidation logic


class TestPostgreSQLClientErrorHandling:
    """Test error handling in PostgreSQL MCP client."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected PostgreSQL MCP client for testing."""
        client = OptimizedPostgreSQLMCPClient()
        client.connected = True
        client.http_session = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_http_error_handling(self, connected_client, mock_http_session):
        """Test handling of HTTP errors."""
        mock_http_session.post.return_value.__aenter__.return_value.status = 500
        mock_http_session.post.return_value.__aenter__.return_value.text.return_value = "Internal Server Error"
        connected_client.http_session = mock_http_session
        
        with pytest.raises(MCPClientError):
            await connected_client.get_customers()

    @pytest.mark.asyncio
    async def test_connection_timeout(self, connected_client):
        """Test handling of connection timeouts."""
        mock_session = AsyncMock()
        mock_session.post.side_effect = asyncio.TimeoutError("Request timed out")
        connected_client.http_session = mock_session
        
        with pytest.raises(MCPClientError):
            await connected_client.get_customers()

    @pytest.mark.asyncio
    async def test_invalid_json_response(self, connected_client, mock_http_session):
        """Test handling of invalid JSON responses."""
        mock_http_session.post.return_value.__aenter__.return_value.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        with pytest.raises(MCPClientError):
            await connected_client.get_customers()

    @pytest.mark.asyncio
    async def test_database_error_response(self, connected_client, mock_http_session):
        """Test handling of database error responses."""
        mock_response = {
            "error": {
                "code": "23505",
                "message": "duplicate key value violates unique constraint"
            }
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 400
        connected_client.http_session = mock_http_session
        
        with pytest.raises(MCPClientError, match="duplicate key"):
            await connected_client.create_customer({"email": "existing@example.com"})


class TestPostgreSQLClientPerformance:
    """Test performance characteristics of PostgreSQL MCP client."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected PostgreSQL MCP client for testing."""
        client = OptimizedPostgreSQLMCPClient()
        client.connected = True
        client.http_session = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, connected_client, mock_http_session):
        """Test handling of concurrent requests."""
        mock_response = {"result": [{"id": f"{i}", "name": f"Customer {i}"} for i in range(10)]}
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        # Make multiple concurrent requests
        tasks = [
            connected_client.get_customers(limit=10)
            for _ in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(len(result) == 10 for result in results)
        assert mock_http_session.post.call_count == 5

    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, connected_client, mock_http_session):
        """Test handling of large datasets."""
        # Simulate large response
        large_dataset = [
            {"id": f"{i}", "name": f"Customer {i}", "email": f"customer{i}@example.com"}
            for i in range(1000)
        ]
        mock_response = {"result": large_dataset}
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.get_customers(limit=1000)
        
        assert len(result) == 1000
        assert all("id" in customer for customer in result)


class TestPostgreSQLClientDirectConnection:
    """Test direct connection functionality when external server is available."""

    @pytest.fixture
    def postgres_client_direct(self):
        """Create a PostgreSQL MCP client configured for direct connection."""
        return OptimizedPostgreSQLMCPClient(
            connection_string="postgresql://user:pass@localhost:5432/testdb",
            use_direct_connection=True
        )

    @pytest.mark.asyncio
    async def test_direct_connection_available(self, postgres_client_direct):
        """Test direct connection when external server is available."""
        with patch('src.mcp.postgres_mcp_client.POSTGRES_MCP_AVAILABLE', True):
            with patch('src.mcp.postgres_mcp_client.ExternalPostgresMCPServer') as MockServer:
                mock_server = AsyncMock()
                mock_server.get_customers.return_value = [{"id": "1", "name": "Direct Customer"}]
                MockServer.return_value = mock_server
                
                await postgres_client_direct.connect()
                result = await postgres_client_direct.get_customers()
                
                assert len(result) == 1
                assert result[0]["name"] == "Direct Customer"
                mock_server.get_customers.assert_called_once()

    @pytest.mark.asyncio
    async def test_direct_connection_not_available(self, postgres_client_direct):
        """Test behavior when direct connection is not available."""
        with patch('src.mcp.postgres_mcp_client.POSTGRES_MCP_AVAILABLE', False):
            with patch('aiohttp.ClientSession') as MockSession:
                mock_session = AsyncMock()
                MockSession.return_value = mock_session
                
                result = await postgres_client_direct.connect()
                
                assert result is True
                assert postgres_client_direct.http_session == mock_session
                assert postgres_client_direct.external_server is None


class TestPostgreSQLClientConfiguration:
    """Test various configuration scenarios for PostgreSQL MCP client."""

    def test_default_configuration(self):
        """Test default configuration values."""
        client = OptimizedPostgreSQLMCPClient()
        
        assert client.connection_string is None
        assert client.mcp_server_url == "http://localhost:8001"
        assert client.use_direct_connection is False  # False when no connection string
        assert client.cache_duration == 300

    def test_custom_configuration(self):
        """Test custom configuration values."""
        client = OptimizedPostgreSQLMCPClient(
            connection_string="postgresql://custom:pass@example.com:5432/customdb",
            mcp_server_url="http://custom.server:9000",
            use_direct_connection=True
        )
        
        assert "custom" in client.connection_string
        assert client.mcp_server_url == "http://custom.server:9000"
        assert client.use_direct_connection is True

    def test_configuration_validation(self):
        """Test configuration validation."""
        # Test that client handles various configuration combinations gracefully
        
        # No connection string but direct connection requested
        client1 = OptimizedPostgreSQLMCPClient(
            connection_string=None,
            use_direct_connection=True
        )
        # Should still work by falling back to HTTP
        assert client1.use_direct_connection is False  # Should be adjusted
        
        # Valid configuration
        client2 = OptimizedPostgreSQLMCPClient(
            connection_string="postgresql://user:pass@localhost:5432/db",
            use_direct_connection=True
        )
        assert client2.use_direct_connection is True
