"""
MCP WebSocket Client Implementation
Provides concrete implementation for connecting to MCP servers using WebSocket protocol.
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .mcp_client_interface import MCPClientInterface


class MCPClient(MCPClientInterface):
    """
    WebSocket-based MCP client implementation.
    
    Provides concrete implementation for connecting to MCP servers using
    WebSocket protocol and JSON-RPC communication. Handles tool calls,
    resource access, and connection lifecycle management.
    """
    
    def __init__(self, server_id: str, connection_uri: str):
        """
        Initialize MCP client.
        
        Args:
            server_id: Unique identifier for the MCP server
            connection_uri: WebSocket URI for connecting to the server
        """
        self.server_id = server_id
        self.connection_uri = connection_uri
        self.websocket = None
        self.running = False
        self.logger = logging.getLogger(f"MCP.Client.{server_id}")
        
        # Server capabilities
        self.server_info = {}
        self.available_tools = []
        self.available_resources = []
        
        # Request tracking
        self.pending_requests = {}
        self.request_counter = 0
    
    async def connect(self) -> bool:
        """
        Connect to the MCP server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Note: websockets import would be needed for actual implementation
            # For now, this is a placeholder that would work with proper dependencies
            import websockets
            self.websocket = await websockets.connect(self.connection_uri)
            self.running = True
            
            # Initialize connection
            await self._initialize_connection()
            
            self.logger.info(f"Connected to MCP server: {self.server_id}")
            return True
            
        except ImportError:
            self.logger.error("websockets package not available. Install with: pip install websockets")
            return False
        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server {self.server_id}: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        self.running = False
        self.logger.info(f"Disconnected from MCP server: {self.server_id}")
    
    async def _initialize_connection(self):
        """Initialize the MCP connection with handshake and capability discovery."""
        # Send initialization message
        init_message = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "clientInfo": {
                    "name": "Customer Support MCP Client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await self._send_request(init_message)
        if response.get('result'):
            self.server_info = response['result']
            
        # List available tools
        await self._list_tools()
        
        # List available resources
        await self._list_resources()
    
    async def _list_tools(self):
        """Discover available tools from the server."""
        message = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "tools/list"
        }
        
        response = await self._send_request(message)
        if response.get('result') and 'tools' in response['result']:
            self.available_tools = response['result']['tools']
    
    async def _list_resources(self):
        """Discover available resources from the server."""
        message = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "resources/list"
        }
        
        response = await self._send_request(message)
        if response.get('result') and 'resources' in response['result']:
            self.available_resources = response['result']['resources']
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            dict: Tool execution result
            
        Raises:
            RuntimeError: If client not connected
            ValueError: If tool not available
        """
        if not self.running:
            raise RuntimeError("Client not connected to server")
        
        if tool_name not in [tool['name'] for tool in self.available_tools]:
            raise ValueError(f"Tool '{tool_name}' not available on server")
        
        message = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }
        
        response = await self._send_request(message)
        return response.get('result', {})
    
    async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
        """
        Get a resource from the MCP server.
        
        Args:
            resource_uri: URI of the resource to retrieve
            
        Returns:
            dict: Resource data
            
        Raises:
            RuntimeError: If client not connected
        """
        if not self.running:
            raise RuntimeError("Client not connected to server")
        
        message = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "resources/read",
            "params": {
                "uri": resource_uri
            }
        }
        
        response = await self._send_request(message)
        return response.get('result', {})
    
    async def _send_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a JSON-RPC request to the MCP server and wait for response.
        
        Args:
            message: JSON-RPC message to send
            
        Returns:
            dict: Server response
            
        Raises:
            Exception: If server returns error
        """
        request_id = message['id']
        
        # Send message
        await self.websocket.send(json.dumps(message))
        
        # Wait for response
        while True:
            response_text = await self.websocket.recv()
            response = json.loads(response_text)
            
            if response.get('id') == request_id:
                if 'error' in response:
                    raise Exception(f"MCP Error: {response['error']}")
                return response
    
    def _get_request_id(self) -> int:
        """Generate next unique request ID."""
        self.request_counter += 1
        return self.request_counter
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get comprehensive server information.
        
        Returns:
            dict: Server info including capabilities and connection status
        """
        return {
            'server_id': self.server_id,
            'connection_uri': self.connection_uri,
            'server_info': self.server_info,
            'available_tools': self.available_tools,
            'available_resources': self.available_resources,
            'connected': self.running
        }
    
    # Implementation of MCPClientInterface abstract methods
    async def get_customers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get customers from the database via MCP tool."""
        return await self.call_tool("get_customers", {"limit": limit})
    
    async def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific customer by ID via MCP tool."""
        result = await self.call_tool("get_customer_by_id", {"customer_id": customer_id})
        return result if result else None
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer via MCP tool."""
        return await self.call_tool("create_customer", customer_data)
    
    async def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer information via MCP tool."""
        return await self.call_tool("update_customer", {"customer_id": customer_id, "updates": updates})
    
    async def get_tickets(self, limit: int = 100, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tickets from the database via MCP tool."""
        params = {"limit": limit}
        if status:
            params["status"] = status
        return await self.call_tool("get_tickets", params)
    
    async def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific ticket by ID via MCP tool."""
        result = await self.call_tool("get_ticket_by_id", {"ticket_id": ticket_id})
        return result if result else None
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new ticket via MCP tool."""
        return await self.call_tool("create_ticket", ticket_data)
    
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update ticket information via MCP tool."""
        return await self.call_tool("update_ticket", {"ticket_id": ticket_id, "updates": updates})
    
    async def search_knowledge_base(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the knowledge base via MCP tool."""
        return await self.call_tool("search_knowledge_base", {"search_term": search_term, "limit": limit})
    
    async def get_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics data via MCP tool."""
        return await self.call_tool("get_analytics", {"days": days})
