"""
MCP Server Manager for coordinating multiple MCP servers
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    server_id: str
    name: str
    description: str
    transport: str  # "stdio", "websocket", "http"
    connection_params: Dict[str, Any]
    capabilities: List[str]
    tools: List[str]
    resources: List[str]
    enabled: bool = True

class MCPServerManager:
    """Manages multiple MCP servers for different components"""
    
    def __init__(self):
        self.logger = logging.getLogger("MCPServerManager")
        self.servers = {}
        self.connections = {}
        self.message_handlers = {}
        self.tool_registry = {}
        self.resource_registry = {}
        self.context_store = {}
        
    async def initialize(self, server_configs: List[MCPServerConfig]):
        """Initialize all MCP servers"""
        self.logger.info("Initializing MCP Server Manager...")
        
        for config in server_configs:
            if config.enabled:
                try:
                    server = await self._create_mcp_server(config)
                    self.servers[config.server_id] = server
                    
                    # Register tools and resources
                    await self._register_server_capabilities(config)
                    
                    self.logger.info(f"Initialized MCP server: {config.name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to initialize MCP server {config.name}: {e}")
        
        self.logger.info(f"MCP Server Manager initialized with {len(self.servers)} servers")
    
    async def _create_mcp_server(self, config: MCPServerConfig):
        """Create and start an MCP server based on configuration"""
        if config.transport == "stdio":
            return await self._create_stdio_server(config)
        elif config.transport == "websocket":
            return await self._create_websocket_server(config)
        elif config.transport == "http":
            return await self._create_http_server(config)
        else:
            raise ValueError(f"Unsupported transport: {config.transport}")
    
    async def _create_stdio_server(self, config: MCPServerConfig):
        """Create STDIO-based MCP server"""
        from mcp.stdio_server import MCPStdioServer
        
        server = MCPStdioServer(
            server_id=config.server_id,
            name=config.name,
            capabilities=config.capabilities,
            tools=config.tools,
            resources=config.resources
        )
        
        await server.start()
        return server
    
    async def _create_websocket_server(self, config: MCPServerConfig):
        """Create WebSocket-based MCP server"""
        from mcp.websocket_server import MCPWebSocketServer
        
        server = MCPWebSocketServer(
            server_id=config.server_id,
            name=config.name,
            host=config.connection_params.get('host', 'localhost'),
            port=config.connection_params.get('port', 8080),
            capabilities=config.capabilities,
            tools=config.tools,
            resources=config.resources
        )
        
        await server.start()
        return server
    
    async def _register_server_capabilities(self, config: MCPServerConfig):
        """Register server tools and resources"""
        # Register tools
        for tool in config.tools:
            self.tool_registry[tool] = config.server_id
        
        # Register resources
        for resource in config.resources:
            self.resource_registry[resource] = config.server_id
        
        self.logger.info(f"Registered {len(config.tools)} tools and {len(config.resources)} resources for {config.name}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], 
                       context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call a tool through appropriate MCP server"""
        if tool_name not in self.tool_registry:
            raise ValueError(f"Tool {tool_name} not found in registry")
        
        server_id = self.tool_registry[tool_name]
        server = self.servers.get(server_id)
        
        if not server:
            raise RuntimeError(f"MCP server {server_id} not available")
        
        try:
            # Add context if provided
            if context:
                await self._set_context(server_id, context)
            
            # Call the tool
            result = await server.call_tool(tool_name, arguments)
            
            self.logger.debug(f"Tool {tool_name} executed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error calling tool {tool_name}: {e}")
            raise
    
    async def get_resource(self, resource_uri: str, 
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a resource through appropriate MCP server"""
        if resource_uri not in self.resource_registry:
            raise ValueError(f"Resource {resource_uri} not found in registry")
        
        server_id = self.resource_registry[resource_uri]
        server = self.servers.get(server_id)
        
        if not server:
            raise RuntimeError(f"MCP server {server_id} not available")
        
        try:
            # Add context if provided
            if context:
                await self._set_context(server_id, context)
            
            # Get the resource
            result = await server.get_resource(resource_uri)
            
            self.logger.debug(f"Resource {resource_uri} retrieved successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting resource {resource_uri}: {e}")
            raise
    
    async def _set_context(self, server_id: str, context: Dict[str, Any]):
        """Set context for an MCP server"""
        server = self.servers.get(server_id)
        if server and hasattr(server, 'set_context'):
            await server.set_context(context)
        
        # Store context locally as well
        self.context_store[server_id] = context
    
    async def broadcast_context_update(self, context: Dict[str, Any]):
        """Broadcast context update to all servers"""
        for server_id, server in self.servers.items():
            try:
                await self._set_context(server_id, context)
            except Exception as e:
                self.logger.warning(f"Failed to update context for server {server_id}: {e}")
    
    def get_available_tools(self) -> Dict[str, str]:
        """Get all available tools and their server assignments"""
        return self.tool_registry.copy()
    
    def get_available_resources(self) -> Dict[str, str]:
        """Get all available resources and their server assignments"""
        return self.resource_registry.copy()
    
    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all MCP servers"""
        status = {}
        for server_id, server in self.servers.items():
            try:
                status[server_id] = {
                    'running': getattr(server, 'running', False),
                    'tools': [tool for tool, sid in self.tool_registry.items() if sid == server_id],
                    'resources': [res for res, sid in self.resource_registry.items() if sid == server_id],
                    'last_activity': getattr(server, 'last_activity', None)
                }
            except Exception as e:
                status[server_id] = {'error': str(e)}
        
        return status