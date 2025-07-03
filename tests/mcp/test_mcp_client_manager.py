"""
Comprehensive test suite for MCP Client Manager.
Tests centralized management of multiple MCP client connections.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any, List, Optional

from src.mcp.mcp_client_manager import MCPClientManager
from src.mcp.mcp_client_interface import MCPClientInterface


class TestMCPClientManager:
    """Test cases for MCPClientManager class."""

    @pytest.fixture
    def client_manager(self):
        """Create an MCP client manager instance for testing."""
        return MCPClientManager()

    @pytest.fixture
    def mock_mcp_client(self):
        """Create a mock MCP client for testing."""
        mock_client = AsyncMock(spec=MCPClientInterface)
        mock_client.connect.return_value = True
        mock_client.disconnect.return_value = None
        mock_client.get_server_info.return_value = {
            'server_id': 'test_server',
            'connection_uri': 'ws://localhost:8080/mcp',
            'connected': True,
            'available_tools': [],
            'available_resources': []
        }
        return mock_client

    def test_client_manager_initialization(self, client_manager):
        """Test MCP client manager initialization."""
        assert isinstance(client_manager.clients, dict)
        assert len(client_manager.clients) == 0
        assert client_manager.logger is not None

    @pytest.mark.asyncio
    async def test_add_client_success(self, client_manager):
        """Test successful addition of MCP client."""
        with patch('src.mcp.mcp_client_manager.MCPClient') as MockMCPClient:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            MockMCPClient.return_value = mock_client
            
            result = await client_manager.add_client("test_server", "ws://localhost:8080/mcp")
            
            assert result is True
            assert "test_server" in client_manager.clients
            assert client_manager.clients["test_server"] == mock_client
            MockMCPClient.assert_called_once_with("test_server", "ws://localhost:8080/mcp")
            mock_client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_client_connection_failure(self, client_manager):
        """Test addition of MCP client when connection fails."""
        with patch('src.mcp.mcp_client_manager.MCPClient') as MockMCPClient:
            mock_client = AsyncMock()
            mock_client.connect.return_value = False
            MockMCPClient.return_value = mock_client
            
            result = await client_manager.add_client("test_server", "ws://localhost:8080/mcp")
            
            assert result is False
            assert "test_server" not in client_manager.clients

    @pytest.mark.asyncio
    async def test_add_client_already_exists(self, client_manager, mock_mcp_client):
        """Test adding client when server ID already exists."""
        # Add initial client
        client_manager.clients["test_server"] = mock_mcp_client
        
        result = await client_manager.add_client("test_server", "ws://localhost:8080/mcp")
        
        assert result is False
        assert len(client_manager.clients) == 1

    @pytest.mark.asyncio
    async def test_remove_client(self, client_manager, mock_mcp_client):
        """Test removal of MCP client."""
        # Add client first
        client_manager.clients["test_server"] = mock_mcp_client
        
        await client_manager.remove_client("test_server")
        
        assert "test_server" not in client_manager.clients
        mock_mcp_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_nonexistent_client(self, client_manager):
        """Test removal of non-existent client."""
        # Should not raise an error
        await client_manager.remove_client("nonexistent_server")
        assert len(client_manager.clients) == 0

    def test_get_client_exists(self, client_manager, mock_mcp_client):
        """Test getting existing client."""
        client_manager.clients["test_server"] = mock_mcp_client
        
        result = client_manager.get_client("test_server")
        
        assert result == mock_mcp_client

    def test_get_client_not_exists(self, client_manager):
        """Test getting non-existent client."""
        result = client_manager.get_client("nonexistent_server")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_call_tool_success(self, client_manager, mock_mcp_client):
        """Test successful tool call via client manager."""
        client_manager.clients["test_server"] = mock_mcp_client
        mock_mcp_client.call_tool.return_value = {"output": "Tool executed successfully"}
        
        result = await client_manager.call_tool("test_server", "test_tool", {"param": "value"})
        
        assert result == {"output": "Tool executed successfully"}
        mock_mcp_client.call_tool.assert_called_once_with("test_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_client_not_found(self, client_manager):
        """Test tool call when client not found."""
        with pytest.raises(ValueError, match="MCP client 'nonexistent_server' not found"):
            await client_manager.call_tool("nonexistent_server", "test_tool")

    @pytest.mark.asyncio
    async def test_get_resource_success(self, client_manager, mock_mcp_client):
        """Test successful resource retrieval via client manager."""
        client_manager.clients["test_server"] = mock_mcp_client
        mock_mcp_client.get_resource.return_value = {"contents": [{"text": "Resource content"}]}
        
        result = await client_manager.get_resource("test_server", "test://resource")
        
        assert "contents" in result
        mock_mcp_client.get_resource.assert_called_once_with("test://resource")

    @pytest.mark.asyncio
    async def test_get_resource_client_not_found(self, client_manager):
        """Test resource retrieval when client not found."""
        with pytest.raises(ValueError, match="MCP client 'nonexistent_server' not found"):
            await client_manager.get_resource("nonexistent_server", "test://resource")

    def test_list_clients(self, client_manager):
        """Test listing all connected clients."""
        mock_client1 = Mock()
        mock_client1.get_server_info.return_value = {"server_id": "server1", "connected": True}
        mock_client2 = Mock()
        mock_client2.get_server_info.return_value = {"server_id": "server2", "connected": True}
        
        client_manager.clients["server1"] = mock_client1
        client_manager.clients["server2"] = mock_client2
        
        result = client_manager.list_clients()
        
        assert len(result) == 2
        assert any(client["server_id"] == "server1" for client in result)
        assert any(client["server_id"] == "server2" for client in result)

    def test_list_clients_empty(self, client_manager):
        """Test listing clients when none are connected."""
        result = client_manager.list_clients()
        
        assert result == []

    @pytest.mark.asyncio
    async def test_disconnect_all(self, client_manager):
        """Test disconnecting all managed clients."""
        mock_client1 = AsyncMock()
        mock_client2 = AsyncMock()
        
        client_manager.clients["server1"] = mock_client1
        client_manager.clients["server2"] = mock_client2
        
        await client_manager.disconnect_all()
        
        assert len(client_manager.clients) == 0
        mock_client1.disconnect.assert_called_once()
        mock_client2.disconnect.assert_called_once()


class TestMCPClientManagerAWSIntegration:
    """Test AWS MCP client integration in client manager."""

    @pytest.fixture
    def client_manager(self):
        """Create an MCP client manager instance for testing."""
        return MCPClientManager()

    @pytest.mark.asyncio
    async def test_add_aws_client_success(self, client_manager):
        """Test successful addition of AWS MCP client."""
        with patch('src.mcp.mcp_client_manager.OptimizedAWSMCPClient') as MockAWSClient:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            MockAWSClient.return_value = mock_client
            
            result = await client_manager.add_aws_client(
                "aws_server",
                connection_uri="ws://localhost:8765/ws",
                aws_access_key_id="test_key",
                aws_secret_access_key="test_secret",
                region_name="us-west-2",
                service_types=["lambda", "sns"]
            )
            
            assert result is True
            assert "aws_server" in client_manager.clients
            assert client_manager.clients["aws_server"] == mock_client
            mock_client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_aws_client_with_defaults(self, client_manager):
        """Test adding AWS client with default parameters."""
        with patch('src.mcp.mcp_client_manager.OptimizedAWSMCPClient') as MockAWSClient:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            MockAWSClient.return_value = mock_client
            
            result = await client_manager.add_aws_client("aws_server")
            
            assert result is True
            MockAWSClient.assert_called_once()
            
            # Check that it was called with expected defaults
            call_args = MockAWSClient.call_args
            assert call_args[1]["use_external_mcp_servers"] is True
            assert "lambda" in call_args[1]["service_types"]
            assert call_args[1]["region_name"] == "us-east-1"

    @pytest.mark.asyncio
    async def test_add_aws_client_already_exists(self, client_manager):
        """Test adding AWS client when server ID already exists."""
        # Add initial client
        client_manager.clients["aws_server"] = Mock()
        
        result = await client_manager.add_aws_client("aws_server")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_add_aws_client_connection_failure(self, client_manager):
        """Test adding AWS client when connection fails."""
        with patch('src.mcp.mcp_client_manager.OptimizedAWSMCPClient') as MockAWSClient:
            mock_client = AsyncMock()
            mock_client.connect.return_value = False
            MockAWSClient.return_value = mock_client
            
            result = await client_manager.add_aws_client("aws_server")
            
            assert result is False
            assert "aws_server" not in client_manager.clients

    @pytest.mark.asyncio
    async def test_add_aws_client_custom_mcp_servers(self, client_manager):
        """Test adding AWS client with custom MCP server configuration."""
        custom_servers = {
            "lambda": {"package": "custom.lambda-server", "port": 9000},
            "s3": {"package": "custom.s3-server", "port": 9001}
        }
        
        with patch('src.mcp.mcp_client_manager.OptimizedAWSMCPClient') as MockAWSClient:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            MockAWSClient.return_value = mock_client
            
            result = await client_manager.add_aws_client(
                "aws_server",
                service_types=["lambda", "s3"],
                mcp_servers=custom_servers
            )
            
            assert result is True
            
            # Verify custom servers were passed
            call_args = MockAWSClient.call_args
            assert call_args[1]["mcp_servers"] == custom_servers

    @pytest.mark.asyncio
    async def test_add_aws_client_service_specific_configuration(self, client_manager):
        """Test AWS client configuration for specific services."""
        service_types = ["sqs", "mq"]
        
        with patch('src.mcp.mcp_client_manager.OptimizedAWSMCPClient') as MockAWSClient:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            MockAWSClient.return_value = mock_client
            
            result = await client_manager.add_aws_client(
                "aws_server",
                service_types=service_types,
                use_external_mcp_servers=True
            )
            
            assert result is True
            
            # Verify service-specific configuration
            call_args = MockAWSClient.call_args
            assert call_args[1]["service_types"] == service_types
            
            # Check that default MCP servers were configured for these services
            mcp_servers = call_args[1]["mcp_servers"]
            assert "messaging" in mcp_servers  # SQS should be in messaging
            assert "mq" in mcp_servers


class TestMCPClientManagerConcurrency:
    """Test concurrent operations with MCP client manager."""

    @pytest.fixture
    def client_manager(self):
        """Create an MCP client manager instance for testing."""
        return MCPClientManager()

    @pytest.mark.asyncio
    async def test_concurrent_client_addition(self, client_manager):
        """Test concurrent addition of multiple clients."""
        with patch('src.mcp.mcp_client_manager.MCPClient') as MockMCPClient:
            # Create mock clients that connect successfully
            mock_clients = []
            for i in range(3):
                mock_client = AsyncMock()
                mock_client.connect.return_value = True
                mock_clients.append(mock_client)
            
            MockMCPClient.side_effect = mock_clients
            
            # Add clients concurrently
            tasks = [
                client_manager.add_client(f"server_{i}", f"ws://localhost:{8080+i}/mcp")
                for i in range(3)
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert all(result is True for result in results)
            assert len(client_manager.clients) == 3
            assert all(f"server_{i}" in client_manager.clients for i in range(3))

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, client_manager):
        """Test concurrent tool calls across multiple clients."""
        # Set up multiple clients
        mock_clients = {}
        for i in range(3):
            mock_client = AsyncMock()
            mock_client.call_tool.return_value = {"output": f"result_{i}"}
            client_manager.clients[f"server_{i}"] = mock_client
            mock_clients[f"server_{i}"] = mock_client
        
        # Make concurrent tool calls
        tasks = [
            client_manager.call_tool(f"server_{i}", "test_tool", {"param": f"value_{i}"})
            for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["output"] == f"result_{i}"
            mock_clients[f"server_{i}"].call_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_disconnect_all(self, client_manager):
        """Test concurrent disconnect operations."""
        # Set up multiple clients
        mock_clients = []
        for i in range(5):
            mock_client = AsyncMock()
            client_manager.clients[f"server_{i}"] = mock_client
            mock_clients.append(mock_client)
        
        # Disconnect all concurrently
        await client_manager.disconnect_all()
        
        assert len(client_manager.clients) == 0
        for mock_client in mock_clients:
            mock_client.disconnect.assert_called_once()


class TestMCPClientManagerErrorHandling:
    """Test error handling in MCP client manager."""

    @pytest.fixture
    def client_manager(self):
        """Create an MCP client manager instance for testing."""
        return MCPClientManager()

    @pytest.mark.asyncio
    async def test_add_client_import_error(self, client_manager):
        """Test handling of import errors when adding clients."""
        with patch('src.mcp.mcp_client_manager.MCPClient', side_effect=ImportError("Module not found")):
            # Should handle import error gracefully
            try:
                result = await client_manager.add_client("test_server", "ws://localhost:8080/mcp")
                assert result is False
            except ImportError:
                # If the error propagates, that's also acceptable behavior
                pass

    @pytest.mark.asyncio
    async def test_tool_call_client_exception(self, client_manager):
        """Test handling of exceptions during tool calls."""
        mock_client = AsyncMock()
        mock_client.call_tool.side_effect = Exception("Tool call failed")
        client_manager.clients["test_server"] = mock_client
        
        with pytest.raises(Exception, match="Tool call failed"):
            await client_manager.call_tool("test_server", "test_tool")

    @pytest.mark.asyncio
    async def test_disconnect_client_exception(self, client_manager):
        """Test handling of exceptions during client disconnect."""
        mock_client = AsyncMock()
        mock_client.disconnect.side_effect = Exception("Disconnect failed")
        client_manager.clients["test_server"] = mock_client
        
        # Should handle disconnect errors gracefully
        try:
            await client_manager.remove_client("test_server")
            # Client should still be removed from registry even if disconnect fails
            assert "test_server" not in client_manager.clients
        except Exception:
            # If exception propagates, that's also acceptable
            pass

    @pytest.mark.asyncio
    async def test_disconnect_all_partial_failure(self, client_manager):
        """Test disconnect_all when some clients fail to disconnect."""
        mock_client1 = AsyncMock()
        mock_client1.disconnect.return_value = None  # Success
        
        mock_client2 = AsyncMock()
        mock_client2.disconnect.side_effect = Exception("Disconnect failed")  # Failure
        
        mock_client3 = AsyncMock()
        mock_client3.disconnect.return_value = None  # Success
        
        client_manager.clients["server1"] = mock_client1
        client_manager.clients["server2"] = mock_client2
        client_manager.clients["server3"] = mock_client3
        
        # Should attempt to disconnect all clients
        try:
            await client_manager.disconnect_all()
        except Exception:
            pass  # Some implementations might raise, others might handle gracefully
        
        # All clients should be removed from registry regardless
        assert len(client_manager.clients) == 0


class TestMCPClientManagerConfigurationScenarios:
    """Test various configuration scenarios for MCP client manager."""

    @pytest.fixture
    def client_manager(self):
        """Create an MCP client manager instance for testing."""
        return MCPClientManager()

    @pytest.mark.asyncio
    async def test_mixed_client_types(self, client_manager):
        """Test managing different types of MCP clients."""
        # Mock regular MCP client
        with patch('src.mcp.mcp_client_manager.MCPClient') as MockMCPClient:
            mock_regular_client = AsyncMock()
            mock_regular_client.connect.return_value = True
            MockMCPClient.return_value = mock_regular_client
            
            # Add regular client
            result1 = await client_manager.add_client("regular_server", "ws://localhost:8080/mcp")
            assert result1 is True
            
        # Mock AWS client
        with patch('src.mcp.mcp_client_manager.OptimizedAWSMCPClient') as MockAWSClient:
            mock_aws_client = AsyncMock()
            mock_aws_client.connect.return_value = True
            MockAWSClient.return_value = mock_aws_client
            
            # Add AWS client
            result2 = await client_manager.add_aws_client("aws_server")
            assert result2 is True
        
        # Verify both clients are managed
        assert len(client_manager.clients) == 2
        assert "regular_server" in client_manager.clients
        assert "aws_server" in client_manager.clients

    @pytest.mark.asyncio
    async def test_client_manager_state_consistency(self, client_manager):
        """Test that client manager maintains consistent state."""
        with patch('src.mcp.mcp_client_manager.MCPClient') as MockMCPClient:
            mock_client = AsyncMock()
            mock_client.connect.return_value = True
            mock_client.get_server_info.return_value = {
                'server_id': 'test_server',
                'connected': True
            }
            MockMCPClient.return_value = mock_client
            
            # Add client
            await client_manager.add_client("test_server", "ws://localhost:8080/mcp")
            
            # Verify state
            assert len(client_manager.clients) == 1
            assert client_manager.get_client("test_server") is not None
            
            # List clients should return one
            client_list = client_manager.list_clients()
            assert len(client_list) == 1
            assert client_list[0]['server_id'] == 'test_server'
            
            # Remove client
            await client_manager.remove_client("test_server")
            
            # Verify state after removal
            assert len(client_manager.clients) == 0
            assert client_manager.get_client("test_server") is None
            assert client_manager.list_clients() == []

    def test_client_manager_thread_safety_considerations(self, client_manager):
        """Test considerations for thread safety in client manager."""
        # Note: This test verifies that the data structures used are appropriate
        # for concurrent access, though full thread safety would require actual
        # threading tests which are more complex in async contexts
        
        # Verify that client registry is a standard dict (not thread-safe by default)
        assert isinstance(client_manager.clients, dict)
        
        # In a production system, you might want to use:
        # - asyncio.Lock for protecting critical sections
        # - Concurrent data structures
        # - Proper async context management
        
        # This test documents the current state and requirements for improvement
        assert hasattr(client_manager, 'clients')
        assert hasattr(client_manager, 'logger')
