"""
Base MCP server implementation
"""
import asyncio
import logging
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
from abc import ABC, abstractmethod

class BaseMCPServer(ABC):
    """Base class for MCP servers"""
    
    def __init__(self, server_id: str, name: str, capabilities: List[str],
                 tools: List[str], resources: List[str]):
        self.server_id = server_id
        self.name = name
        self.capabilities = capabilities
        self.tools = tools
        self.resources = resources
        self.running = False
        self.logger = logging.getLogger(f"MCP.{name}")
        
        # Tool and resource handlers
        self.tool_handlers = {}
        self.resource_handlers = {}
        
        # Context management
        self.context = {}
        self.last_activity = None
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default MCP handlers"""
        # Standard MCP methods
        self.tool_handlers.update({
            'initialize': self._handle_initialize,
            'list_tools': self._handle_list_tools,
            'list_resources': self._handle_list_resources,
            'call_tool': self._handle_call_tool,
            'get_resource': self._handle_get_resource
        })
    
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming MCP message"""
        self.last_activity = datetime.now()
        
        try:
            method = message.get('method')
            params = message.get('params', {})
            request_id = message.get('id')
            
            if method in self.tool_handlers:
                result = await self.tool_handlers[method](params)
                
                if request_id is not None:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": result
                    }
            else:
                if request_id is not None:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                    
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            
            if message.get('id') is not None:
                return {
                    "jsonrpc": "2.0",
                    "id": message.get('id'),
                    "error": {
                        "code": -32000,
                        "message": str(e)
                    }
                }
        
        return None
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialization"""
        return {
            "protocolVersion": "1.0",
            "serverInfo": {
                "name": self.name,
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True}
            }
        }
    
    async def _handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list tools request"""
        tool_definitions = []
        
        for tool_name in self.tools:
            tool_def = await self._get_tool_definition(tool_name)
            if tool_def:
                tool_definitions.append(tool_def)
        
        return {"tools": tool_definitions}
    
    async def _handle_list_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list resources request"""
        resource_definitions = []
        
        for resource_uri in self.resources:
            resource_def = await self._get_resource_definition(resource_uri)
            if resource_def:
                resource_definitions.append(resource_def)
        
        return {"resources": resource_definitions}
    
    async def _handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call request"""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        return await self.call_tool(tool_name, arguments)
    
    async def _handle_get_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get resource request"""
        resource_uri = params.get('uri')
        
        if resource_uri not in self.resources:
            raise ValueError(f"Unknown resource: {resource_uri}")
        
        return await self.get_resource(resource_uri)
    
    @abstractmethod
    async def start(self):
        """Start the MCP server"""
        pass
    
    async def stop(self):
        """Stop the MCP server"""
        self.running = False
        self.logger.info(f"MCP server {self.name} stopped")
    
    async def set_context(self, context: Dict[str, Any]):
        """Set context for this server"""
        self.context.update(context)
        self.logger.debug(f"Context updated for {self.name}")
    
    # Methods to be implemented by specific servers
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement call_tool")
    
    async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
        """Get a specific resource - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement get_resource")
    
    async def _get_tool_definition(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool definition - to be implemented by subclasses"""
        return {
            "name": tool_name,
            "description": f"Tool: {tool_name}",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    
    async def _get_resource_definition(self, resource_uri: str) -> Optional[Dict[str, Any]]:
        """Get resource definition - to be implemented by subclasses"""
        return {
            "uri": resource_uri,
            "name": resource_uri.split('/')[-1],
            "description": f"Resource: {resource_uri}",
            "mimeType": "application/json"
        }
