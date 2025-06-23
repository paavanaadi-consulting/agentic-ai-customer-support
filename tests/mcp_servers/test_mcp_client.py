"""
Comprehensive unit tests for MCP Client
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from mcp.mcp_client import MCPClient, MCPClientManager

class TestMCPClient:
    """Test suite for MCP Client"""
    
    @pytest.fixture
    def mcp_client(self):
        return MCPClient("test_server", "ws://localhost:8080")
    
    @pytest.mark.asyncio
    async def test_initialization(self, mcp_client):
        """Test client initialization"""
        assert mcp_client.server_id == "test_server"
        assert mcp_client.connection_uri == "ws://localhost:8080"
        assert mcp_client.running is False
        assert len(mcp_client.available_tools) == 0
        assert len(mcp_client.available_resources) == 0
    
    @pytest.mark.asyncio
    @patch('websockets.connect')
    async def test_connect_success(self, mock_connect, mcp_client):
        """Test successful connection"""
        mock_websocket = AsyncMock()
        mock_connect.return_value = mock_websocket
        
        # Mock initialization responses
        mock_websocket.send = AsyncMock()
        mock_websocket.recv = AsyncMock(side_effect=[
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
        ])
        
        result = await mcp_client.connect()
        
        assert result is True
        assert mcp_client.running is True
        assert len(mcp_client.available_tools) == 1
        assert mcp_client.available_tools[0]["name"] == "test_tool"


class TestMCPClientManager:
    """Test suite for MCP Client Manager"""
    
    @pytest.fixture
    def client_manager(self):
        return MCPClientManager()
    
    @pytest.mark.asyncio
    async def test_initialization(self, client_manager):
        """Test manager initialization"""
        assert len(client_manager.clients) == 0
