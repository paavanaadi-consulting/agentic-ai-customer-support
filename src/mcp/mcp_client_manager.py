"""
MCP Client Manager
Provides centralized management of multiple MCP client connections.
"""
import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING

from .mcp_client_interface import MCPClientInterface

if TYPE_CHECKING:
    from .mcp_client import MCPClient


class MCPClientManager:
    """
    Manager for multiple MCP clients.
    
    Provides centralized management of multiple MCP client connections,
    including lifecycle management, tool routing, and resource access
    across different MCP servers.
    """
    
    def __init__(self):
        """Initialize the MCP client manager."""
        self.clients = {}
        self.logger = logging.getLogger("MCP.ClientManager")
    
    async def add_client(self, server_id: str, connection_uri: str) -> bool:
        """
        Add and connect a new MCP client.
        
        Args:
            server_id: Unique identifier for the server
            connection_uri: WebSocket URI for the server
            
        Returns:
            bool: True if client added successfully, False otherwise
        """
        if server_id in self.clients:
            self.logger.warning(f"Client {server_id} already exists")
            return False
        
        # Import here to avoid circular imports
        from .mcp_client import MCPClient
        
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
        """
        Remove and disconnect an MCP client.
        
        Args:
            server_id: ID of the client to remove
        """
        if server_id in self.clients:
            await self.clients[server_id].disconnect()
            del self.clients[server_id]
            self.logger.info(f"Removed MCP client: {server_id}")
    
    def get_client(self, server_id: str) -> Optional['MCPClient']:
        """
        Get an MCP client by server ID.
        
        Args:
            server_id: ID of the client to retrieve
            
        Returns:
            MCPClient or None: The client instance if found
        """
        return self.clients.get(server_id)
    
    async def call_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call a tool on a specific MCP server.
        
        Args:
            server_id: ID of the server to call tool on
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            dict: Tool execution result
            
        Raises:
            ValueError: If client not found
        """
        client = self.get_client(server_id)
        if not client:
            raise ValueError(f"MCP client '{server_id}' not found")
        
        return await client.call_tool(tool_name, arguments)
    
    async def get_resource(self, server_id: str, resource_uri: str) -> Dict[str, Any]:
        """
        Get a resource from a specific MCP server.
        
        Args:
            server_id: ID of the server to get resource from
            resource_uri: URI of the resource to retrieve
            
        Returns:
            dict: Resource data
            
        Raises:
            ValueError: If client not found
        """
        client = self.get_client(server_id)
        if not client:
            raise ValueError(f"MCP client '{server_id}' not found")
        
        return await client.get_resource(resource_uri)
    
    def list_clients(self) -> List[Dict[str, Any]]:
        """
        List all connected clients with their information.
        
        Returns:
            list: List of client information dictionaries
        """
        return [client.get_server_info() for client in self.clients.values()]
    
    async def disconnect_all(self):
        """Disconnect all managed clients and clear the client registry."""
        for client in self.clients.values():
            await client.disconnect()
        self.clients.clear()
        self.logger.info("Disconnected all MCP clients")
