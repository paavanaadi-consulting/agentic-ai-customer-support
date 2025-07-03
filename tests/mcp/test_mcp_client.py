"""
Comprehensive test suite for MCP Client.
Tests WebSocket-based MCP client implementation.
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any, List, Optional

from src.mcp.mcp_client import MCPClient
from src.mcp.mcp_client_interface import MCPClientInterface


class TestMCPClient:
    """Test cases for MCPClient class."""

    @pytest.fixture
    def mcp_client(self):
        """Create an MCP client instance for testing."""
        return MCPClient("test_server", "ws://localhost:8080/mcp")

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock websocket for testing."""
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock()
        mock_ws.close = AsyncMock()
        return mock_ws

    def test_mcp_client_initialization(self, mcp_client):
        """Test MCP client initialization."""
        assert mcp_client.server_id == "test_server"
        assert mcp_client.connection_uri == "ws://localhost:8080/mcp"
        assert mcp_client.websocket is None
        assert mcp_client.running is False
        assert mcp_client.request_counter == 0
        assert isinstance(mcp_client.pending_requests, dict)
        assert isinstance(mcp_client.available_tools, list)
        assert isinstance(mcp_client.available_resources, list)

    def test_mcp_client_implements_interface(self, mcp_client):
        """Test that MCPClient implements MCPClientInterface."""
        assert isinstance(mcp_client, MCPClientInterface)

    @pytest.mark.asyncio
    async def test_connect_success(self, mcp_client, mock_websocket):
        """Test successful connection to MCP server."""
        with patch('websockets.connect', return_value=mock_websocket) as mock_connect:
            # Mock initialization responses
            mock_websocket.recv.side_effect = [
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {
                        "protocolVersion": "0.1.0",
                        "serverInfo": {"name": "Test Server", "version": "1.0.0"}
                    }
                }),
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {
                        "tools": [{"name": "test_tool", "description": "Test tool"}]
                    }
                }),
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": 3,
                    "result": {
                        "resources": [{"uri": "test://resource", "name": "Test Resource"}]
                    }
                })
            ]
            
            result = await mcp_client.connect()
            
            assert result is True
            assert mcp_client.running is True
            assert mcp_client.websocket == mock_websocket
            assert len(mcp_client.available_tools) == 1
            assert len(mcp_client.available_resources) == 1
            mock_connect.assert_called_once_with("ws://localhost:8080/mcp")

    @pytest.mark.asyncio
    async def test_connect_websockets_not_available(self, mcp_client):
        """Test connection when websockets package is not available."""
        with patch('websockets.connect', side_effect=ImportError("No module named 'websockets'")):
            result = await mcp_client.connect()
            
            assert result is False
            assert mcp_client.running is False
            assert mcp_client.websocket is None

    @pytest.mark.asyncio
    async def test_connect_connection_error(self, mcp_client):
        """Test connection when server is unreachable."""
        with patch('websockets.connect', side_effect=Exception("Connection refused")):
            result = await mcp_client.connect()
            
            assert result is False
            assert mcp_client.running is False
            assert mcp_client.websocket is None

    @pytest.mark.asyncio
    async def test_disconnect(self, mcp_client, mock_websocket):
        """Test disconnection from MCP server."""
        mcp_client.websocket = mock_websocket
        mcp_client.running = True
        
        await mcp_client.disconnect()
        
        assert mcp_client.websocket is None
        assert mcp_client.running is False
        mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_success(self, mcp_client, mock_websocket):
        """Test successful tool call."""
        mcp_client.websocket = mock_websocket
        mcp_client.running = True
        mcp_client.available_tools = [{"name": "test_tool", "description": "Test tool"}]
        
        # Mock response
        mock_websocket.recv.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"output": "Tool executed successfully"}
        })
        
        result = await mcp_client.call_tool("test_tool", {"param": "value"})
        
        assert result == {"output": "Tool executed successfully"}
        mock_websocket.send.assert_called_once()
        
        # Verify the sent message
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_message["method"] == "tools/call"
        assert sent_message["params"]["name"] == "test_tool"
        assert sent_message["params"]["arguments"] == {"param": "value"}

    @pytest.mark.asyncio
    async def test_call_tool_not_connected(self, mcp_client):
        """Test tool call when client is not connected."""
        with pytest.raises(RuntimeError, match="Client not connected to server"):
            await mcp_client.call_tool("test_tool")

    @pytest.mark.asyncio
    async def test_call_tool_not_available(self, mcp_client, mock_websocket):
        """Test tool call when tool is not available."""
        mcp_client.websocket = mock_websocket
        mcp_client.running = True
        mcp_client.available_tools = []
        
        with pytest.raises(ValueError, match="Tool 'nonexistent_tool' not available on server"):
            await mcp_client.call_tool("nonexistent_tool")

    @pytest.mark.asyncio
    async def test_call_tool_server_error(self, mcp_client, mock_websocket):
        """Test tool call when server returns error."""
        mcp_client.websocket = mock_websocket
        mcp_client.running = True
        mcp_client.available_tools = [{"name": "test_tool", "description": "Test tool"}]
        
        # Mock error response
        mock_websocket.recv.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -1, "message": "Tool execution failed"}
        })
        
        with pytest.raises(Exception, match="MCP Error"):
            await mcp_client.call_tool("test_tool")

    @pytest.mark.asyncio
    async def test_get_resource_success(self, mcp_client, mock_websocket):
        """Test successful resource retrieval."""
        mcp_client.websocket = mock_websocket
        mcp_client.running = True
        
        # Mock response
        mock_websocket.recv.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"contents": [{"uri": "test://resource", "mimeType": "text/plain", "text": "Resource content"}]}
        })
        
        result = await mcp_client.get_resource("test://resource")
        
        assert "contents" in result
        mock_websocket.send.assert_called_once()
        
        # Verify the sent message
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_message["method"] == "resources/read"
        assert sent_message["params"]["uri"] == "test://resource"

    @pytest.mark.asyncio
    async def test_get_resource_not_connected(self, mcp_client):
        """Test resource retrieval when client is not connected."""
        with pytest.raises(RuntimeError, match="Client not connected to server"):
            await mcp_client.get_resource("test://resource")

    def test_get_request_id_increments(self, mcp_client):
        """Test that request ID increments correctly."""
        first_id = mcp_client._get_request_id()
        second_id = mcp_client._get_request_id()
        third_id = mcp_client._get_request_id()
        
        assert first_id == 1
        assert second_id == 2
        assert third_id == 3
        assert mcp_client.request_counter == 3

    def test_get_server_info(self, mcp_client):
        """Test getting comprehensive server information."""
        mcp_client.server_info = {"name": "Test Server", "version": "1.0.0"}
        mcp_client.available_tools = [{"name": "tool1"}, {"name": "tool2"}]
        mcp_client.available_resources = [{"uri": "resource1"}, {"uri": "resource2"}]
        mcp_client.running = True
        
        info = mcp_client.get_server_info()
        
        assert info["server_id"] == "test_server"
        assert info["connection_uri"] == "ws://localhost:8080/mcp"
        assert info["server_info"] == {"name": "Test Server", "version": "1.0.0"}
        assert len(info["available_tools"]) == 2
        assert len(info["available_resources"]) == 2
        assert info["connected"] is True

    @pytest.mark.asyncio
    async def test_send_request_with_response_matching(self, mcp_client, mock_websocket):
        """Test that _send_request correctly matches responses to requests."""
        mcp_client.websocket = mock_websocket
        
        # Mock multiple responses coming back in different order
        mock_websocket.recv.side_effect = [
            json.dumps({"jsonrpc": "2.0", "id": 2, "result": {"data": "response2"}}),
            json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"data": "response1"}})
        ]
        
        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "test_method"
        }
        
        result = await mcp_client._send_request(message)
        
        assert result == {"jsonrpc": "2.0", "id": 1, "result": {"data": "response1"}}


class TestMCPClientCustomerOperations:
    """Test customer-related operations via MCP client."""

    @pytest.fixture
    def connected_client(self, mock_websocket):
        """Create a connected MCP client for testing."""
        client = MCPClient("test_server", "ws://localhost:8080/mcp")
        client.websocket = mock_websocket
        client.running = True
        client.available_tools = [
            {"name": "get_customers"},
            {"name": "get_customer_by_id"},
            {"name": "create_customer"},
            {"name": "update_customer"}
        ]
        return client

    @pytest.mark.asyncio
    async def test_get_customers(self, connected_client, mock_websocket):
        """Test getting customers via MCP tool."""
        mock_websocket.recv.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": [
                {"id": "1", "name": "Customer 1"},
                {"id": "2", "name": "Customer 2"}
            ]
        })
        
        result = await connected_client.get_customers(limit=50)
        
        assert len(result) == 2
        assert result[0]["name"] == "Customer 1"
        
        # Verify the sent message
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_message["params"]["name"] == "get_customers"
        assert sent_message["params"]["arguments"]["limit"] == 50

    @pytest.mark.asyncio
    async def test_get_customer_by_id(self, connected_client, mock_websocket):
        """Test getting customer by ID via MCP tool."""
        mock_websocket.recv.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"id": "123", "name": "Test Customer", "email": "test@example.com"}
        })
        
        result = await connected_client.get_customer_by_id("123")
        
        assert result["id"] == "123"
        assert result["name"] == "Test Customer"
        
        # Verify the sent message
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_message["params"]["arguments"]["customer_id"] == "123"

    @pytest.mark.asyncio
    async def test_create_customer(self, connected_client, mock_websocket):
        """Test creating customer via MCP tool."""
        customer_data = {"name": "New Customer", "email": "new@example.com"}
        
        mock_websocket.recv.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"id": "new_123", **customer_data}
        })
        
        result = await connected_client.create_customer(customer_data)
        
        assert result["id"] == "new_123"
        assert result["name"] == "New Customer"
        
        # Verify the sent message
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_message["params"]["name"] == "create_customer"
        assert sent_message["params"]["arguments"] == customer_data

    @pytest.mark.asyncio
    async def test_update_customer(self, connected_client, mock_websocket):
        """Test updating customer via MCP tool."""
        updates = {"name": "Updated Customer", "email": "updated@example.com"}
        
        mock_websocket.recv.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"id": "123", **updates}
        })
        
        result = await connected_client.update_customer("123", updates)
        
        assert result["id"] == "123"
        assert result["name"] == "Updated Customer"
        
        # Verify the sent message
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_message["params"]["arguments"]["customer_id"] == "123"
        assert sent_message["params"]["arguments"]["updates"] == updates


class TestMCPClientTicketOperations:
    """Test ticket-related operations via MCP client."""

    @pytest.fixture
    def connected_client(self, mock_websocket):
        """Create a connected MCP client for testing."""
        client = MCPClient("test_server", "ws://localhost:8080/mcp")
        client.websocket = mock_websocket
        client.running = True
        client.available_tools = [
            {"name": "get_tickets"},
            {"name": "get_ticket_by_id"},
            {"name": "create_ticket"},
            {"name": "update_ticket"}
        ]
        return client

    @pytest.mark.asyncio
    async def test_get_tickets(self, connected_client, mock_websocket):
        """Test getting tickets via MCP tool."""
        mock_websocket.recv.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": [
                {"id": "1", "title": "Ticket 1", "status": "open"},
                {"id": "2", "title": "Ticket 2", "status": "closed"}
            ]
        })
        
        result = await connected_client.get_tickets(limit=100, status="open")
        
        assert len(result) == 2
        assert result[0]["title"] == "Ticket 1"
        
        # Verify the sent message
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_message["params"]["arguments"]["limit"] == 100
        assert sent_message["params"]["arguments"]["status"] == "open"

    @pytest.mark.asyncio
    async def test_get_tickets_no_status_filter(self, connected_client, mock_websocket):
        """Test getting tickets without status filter."""
        mock_websocket.recv.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": []
        })
        
        result = await connected_client.get_tickets(limit=50)
        
        # Verify the sent message doesn't include status parameter
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        assert "status" not in sent_message["params"]["arguments"]
        assert sent_message["params"]["arguments"]["limit"] == 50

    @pytest.mark.asyncio
    async def test_get_ticket_by_id(self, connected_client, mock_websocket):
        """Test getting ticket by ID via MCP tool."""
        mock_websocket.recv.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"id": "456", "title": "Test Ticket", "status": "open", "priority": "high"}
        })
        
        result = await connected_client.get_ticket_by_id("456")
        
        assert result["id"] == "456"
        assert result["title"] == "Test Ticket"
        assert result["priority"] == "high"

    @pytest.mark.asyncio
    async def test_create_ticket(self, connected_client, mock_websocket):
        """Test creating ticket via MCP tool."""
        ticket_data = {
            "title": "New Support Ticket",
            "description": "Customer needs help",
            "priority": "medium",
            "customer_id": "123"
        }
        
        mock_websocket.recv.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"id": "new_456", "status": "open", **ticket_data}
        })
        
        result = await connected_client.create_ticket(ticket_data)
        
        assert result["id"] == "new_456"
        assert result["title"] == "New Support Ticket"
        assert result["status"] == "open"

    @pytest.mark.asyncio
    async def test_update_ticket(self, connected_client, mock_websocket):
        """Test updating ticket via MCP tool."""
        updates = {"status": "resolved", "resolution": "Issue fixed"}
        
        mock_websocket.recv.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"id": "456", **updates}
        })
        
        result = await connected_client.update_ticket("456", updates)
        
        assert result["id"] == "456"
        assert result["status"] == "resolved"


class TestMCPClientKnowledgeBase:
    """Test knowledge base operations via MCP client."""

    @pytest.fixture
    def connected_client(self, mock_websocket):
        """Create a connected MCP client for testing."""
        client = MCPClient("test_server", "ws://localhost:8080/mcp")
        client.websocket = mock_websocket
        client.running = True
        client.available_tools = [{"name": "search_knowledge_base"}]
        return client

    @pytest.mark.asyncio
    async def test_search_knowledge_base(self, connected_client, mock_websocket):
        """Test searching knowledge base via MCP tool."""
        mock_websocket.recv.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": [
                {"id": "1", "title": "How to reset password", "content": "Step 1: ..."},
                {"id": "2", "title": "Account recovery", "content": "To recover..."}
            ]
        })
        
        result = await connected_client.search_knowledge_base("password reset", limit=5)
        
        assert len(result) == 2
        assert "password" in result[0]["title"].lower()
        
        # Verify the sent message
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_message["params"]["arguments"]["search_term"] == "password reset"
        assert sent_message["params"]["arguments"]["limit"] == 5


class TestMCPClientAnalytics:
    """Test analytics operations via MCP client."""

    @pytest.fixture
    def connected_client(self, mock_websocket):
        """Create a connected MCP client for testing."""
        client = MCPClient("test_server", "ws://localhost:8080/mcp")
        client.websocket = mock_websocket
        client.running = True
        client.available_tools = [{"name": "get_analytics"}]
        return client

    @pytest.mark.asyncio
    async def test_get_analytics(self, connected_client, mock_websocket):
        """Test getting analytics via MCP tool."""
        mock_websocket.recv.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "period_days": 30,
                "total_tickets": 150,
                "resolved_tickets": 120,
                "average_resolution_time": "4.5 hours",
                "customer_satisfaction": 4.2
            }
        })
        
        result = await connected_client.get_analytics(days=30)
        
        assert result["period_days"] == 30
        assert result["total_tickets"] == 150
        assert result["customer_satisfaction"] == 4.2
        
        # Verify the sent message
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_message["params"]["arguments"]["days"] == 30


class TestMCPClientErrorHandling:
    """Test error handling in MCP client."""

    @pytest.fixture
    def connected_client(self, mock_websocket):
        """Create a connected MCP client for testing."""
        client = MCPClient("test_server", "ws://localhost:8080/mcp")
        client.websocket = mock_websocket
        client.running = True
        return client

    @pytest.mark.asyncio
    async def test_websocket_send_error(self, connected_client, mock_websocket):
        """Test handling of websocket send errors."""
        mock_websocket.send.side_effect = Exception("Send failed")
        connected_client.available_tools = [{"name": "test_tool"}]
        
        with pytest.raises(Exception, match="Send failed"):
            await connected_client.call_tool("test_tool")

    @pytest.mark.asyncio
    async def test_websocket_recv_error(self, connected_client, mock_websocket):
        """Test handling of websocket receive errors."""
        mock_websocket.recv.side_effect = Exception("Receive failed")
        connected_client.available_tools = [{"name": "test_tool"}]
        
        with pytest.raises(Exception, match="Receive failed"):
            await connected_client.call_tool("test_tool")

    @pytest.mark.asyncio
    async def test_invalid_json_response(self, connected_client, mock_websocket):
        """Test handling of invalid JSON responses."""
        mock_websocket.recv.return_value = "invalid json"
        connected_client.available_tools = [{"name": "test_tool"}]
        
        with pytest.raises(json.JSONDecodeError):
            await connected_client.call_tool("test_tool")

    @pytest.mark.asyncio
    async def test_unexpected_response_format(self, connected_client, mock_websocket):
        """Test handling of responses with unexpected format."""
        mock_websocket.recv.return_value = json.dumps({
            "not_jsonrpc": "2.0",
            "missing_id": True
        })
        connected_client.available_tools = [{"name": "test_tool"}]
        
        # The client should handle this gracefully or raise appropriate error
        # Implementation detail depends on how robust error handling is implemented
        try:
            await connected_client.call_tool("test_tool")
        except (KeyError, AttributeError) as e:
            # Expected behavior for malformed responses
            assert "id" in str(e) or "jsonrpc" in str(e)


class TestMCPClientConcurrency:
    """Test concurrent operations with MCP client."""

    @pytest.fixture
    def connected_client(self, mock_websocket):
        """Create a connected MCP client for testing."""
        client = MCPClient("test_server", "ws://localhost:8080/mcp")
        client.websocket = mock_websocket
        client.running = True
        client.available_tools = [{"name": "test_tool"}]
        return client

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, connected_client, mock_websocket):
        """Test concurrent tool calls with different request IDs."""
        # Mock responses for different request IDs
        responses = [
            json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"output": "result1"}}),
            json.dumps({"jsonrpc": "2.0", "id": 2, "result": {"output": "result2"}}),
            json.dumps({"jsonrpc": "2.0", "id": 3, "result": {"output": "result3"}})
        ]
        
        mock_websocket.recv.side_effect = responses
        
        # Start multiple concurrent tool calls
        tasks = [
            connected_client.call_tool("test_tool", {"param": f"value{i}"})
            for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        assert all("output" in result for result in results)
        assert mock_websocket.send.call_count == 3

    @pytest.mark.asyncio
    async def test_request_id_uniqueness(self, connected_client):
        """Test that request IDs are unique across concurrent requests."""
        request_ids = set()
        
        # Generate multiple request IDs
        for _ in range(10):
            request_id = connected_client._get_request_id()
            assert request_id not in request_ids
            request_ids.add(request_id)
        
        assert len(request_ids) == 10
