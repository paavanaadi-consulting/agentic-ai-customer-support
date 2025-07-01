"""
MCP Client for connecting to MCP servers
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import websockets

class MCPClient:
    """Client for connecting to MCP servers"""
    
    def __init__(self, server_id: str, connection_uri: str):
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
        """Connect to the MCP server"""
        try:
            self.websocket = await websockets.connect(self.connection_uri)
            self.running = True
            
            # Initialize connection
            await self._initialize_connection()
            
            self.logger.info(f"Connected to MCP server: {self.server_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server {self.server_id}: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        self.running = False
        self.logger.info(f"Disconnected from MCP server: {self.server_id}")
    
    async def _initialize_connection(self):
        """Initialize the MCP connection"""
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
        """List available tools from the server"""
        message = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "tools/list"
        }
        
        response = await self._send_request(message)
        if response.get('result') and 'tools' in response['result']:
            self.available_tools = response['result']['tools']
    
    async def _list_resources(self):
        """List available resources from the server"""
        message = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "resources/list"
        }
        
        response = await self._send_request(message)
        if response.get('result') and 'resources' in response['result']:
            self.available_resources = response['result']['resources']
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
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
        """Get a resource from the MCP server"""
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
        """Send a request to the MCP server and wait for response"""
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
        """Get next request ID"""
        self.request_counter += 1
        return self.request_counter
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            'server_id': self.server_id,
            'connection_uri': self.connection_uri,
            'server_info': self.server_info,
            'available_tools': self.available_tools,
            'available_resources': self.available_resources,
            'connected': self.running
        }


class MCPClientManager:
    """Manager for multiple MCP clients"""
    
    def __init__(self):
        self.clients = {}
        self.logger = logging.getLogger("MCP.ClientManager")
    
    async def add_client(self, server_id: str, connection_uri: str) -> bool:
        """Add and connect a new MCP client"""
        if server_id in self.clients:
            self.logger.warning(f"Client {server_id} already exists")
            return False
        
        client = MCPClient(server_id, connection_uri)
        success = await client.connect()
        
        if success:
            self.clients[server_id] = client
            self.logger.info(f"Added MCP client: {server_id}")
            return True
        else:
            self.logger.error(f"Failed to add MCP client: {server_id}")
            return False
    
    async def remove_client(self, server_id: str):
        """Remove and disconnect an MCP client"""
        if server_id in self.clients:
            await self.clients[server_id].disconnect()
            del self.clients[server_id]
            self.logger.info(f"Removed MCP client: {server_id}")
    
    def get_client(self, server_id: str) -> Optional[MCPClient]:
        """Get an MCP client by server ID"""
        return self.clients.get(server_id)
    
    async def call_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a tool on a specific MCP server"""
        client = self.get_client(server_id)
        if not client:
            raise ValueError(f"MCP client '{server_id}' not found")
        
        return await client.call_tool(tool_name, arguments)
    
    async def get_resource(self, server_id: str, resource_uri: str) -> Dict[str, Any]:
        """Get a resource from a specific MCP server"""
        client = self.get_client(server_id)
        if not client:
            raise ValueError(f"MCP client '{server_id}' not found")
        
        return await client.get_resource(resource_uri)
    
    def list_clients(self) -> List[Dict[str, Any]]:
        """List all connected clients"""
        return [client.get_server_info() for client in self.clients.values()]
    
    async def disconnect_all(self):
        """Disconnect all clients"""
        for client in self.clients.values():
            await client.disconnect()
        self.clients.clear()
        self.logger.info("Disconnected all MCP clients")
