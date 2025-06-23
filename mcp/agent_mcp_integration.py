"""
MCP integration for AI agents (Claude, Gemini, GPT)
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from mcp.base_mcp_server import BaseMCPServer

class AgentMCPServer(BaseMCPServer):
    """MCP server for AI agent integration"""
    
    def __init__(self, agent_id: str, agent_type: str, model_name: str):
        tools = [
            'analyze_query',
            'extract_context',
            'generate_response',
            'get_capabilities',
            'update_strategy'
        ]
        
        resources = [
            f'agent://{agent_id}/status',
            f'agent://{agent_id}/metrics',
            f'agent://{agent_id}/context',
            f'agent://{agent_id}/strategy'
        ]
        
        super().__init__(
            server_id=f"mcp_{agent_id}",
            name=f"MCP Server for {agent_type.title()} Agent",
            capabilities=['tools', 'resources', 'context'],
            tools=tools,
            resources=resources
        )
        
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.model_name = model_name
        self.agent_instance = None
        
    def set_agent_instance(self, agent):
        """Set the actual agent instance"""
        self.agent_instance = agent
    
    async def start(self):
        """Start the agent MCP server"""
        self.running = True
        self.logger.info(f"Agent MCP server started for {self.agent_id}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call agent-specific tools"""
        if not self.agent_instance:
            raise RuntimeError("Agent instance not set")
        
        try:
            if tool_name == 'analyze_query':
                result = await self.agent_instance.process_input(arguments)
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            
            elif tool_name == 'extract_context':
                context = {
                    'agent_id': self.agent_id,
                    'agent_type': self.agent_type,
                    'model': self.model_name,
                    'current_context': getattr(self.agent_instance, 'context', {}),
                    'strategy': getattr(self.agent_instance, 'strategy', {}),
                    'metrics': getattr(self.agent_instance, 'performance_metrics', {})
                }
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(context, indent=2)
                        }
                    ]
                }
            
            elif tool_name == 'generate_response':
                if hasattr(self.agent_instance, 'generate_response'):
                    response = await self.agent_instance.generate_response(arguments)
                else:
                    response = await self.agent_instance.process_input(arguments)
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": response.get('response', str(response))
                        }
                    ]
                }
            
            elif tool_name == 'get_capabilities':
                capabilities = {
                    'agent_type': self.agent_type,
                    'model': self.model_name,
                    'supported_tasks': getattr(self.agent_instance, 'supported_tasks', []),
                    'tools': self.tools,
                    'resources': self.resources
                }
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(capabilities, indent=2)
                        }
                    ]
                }
            
            elif tool_name == 'update_strategy':
                if hasattr(self.agent_instance, 'update_strategy'):
                    self.agent_instance.update_strategy(arguments.get('strategy', {}))
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "Strategy updated successfully"
                            }
                        ]
                    }
                else:
                    raise ValueError("Agent does not support strategy updates")
            
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
                
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {e}")
            raise
    
    async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
        """Get agent-specific resources"""
        if not self.agent_instance:
            raise RuntimeError("Agent instance not set")
        
        try:
            if resource_uri.endswith('/status'):
                status = {
                    'agent_id': self.agent_id,
                    'agent_type': self.agent_type,
                    'model': self.model_name,
                    'running': getattr(self.agent_instance, 'running', True),
                    'last_activity': getattr(self.agent_instance, 'last_activity', None)
                }
                
            elif resource_uri.endswith('/metrics'):
                status = getattr(self.agent_instance, 'performance_metrics', {})
                
            elif resource_uri.endswith('/context'):
                status = {
                    'current_context': getattr(self.agent_instance, 'context', {}),
                    'strategy': getattr(self.agent_instance, 'strategy', {}),
                    'chromosome': getattr(self.agent_instance, 'chromosome', None)
                }
                
            elif resource_uri.endswith('/strategy'):
                status = getattr(self.agent_instance, 'strategy', {})
                
            else:
                raise ValueError(f"Unknown resource: {resource_uri}")
            
            return {
                "contents": [
                    {
                        "uri": resource_uri,
                        "mimeType": "application/json",
                        "text": json.dumps(status, indent=2, default=str)
                    }
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting resource {resource_uri}: {e}")
            raise
    
    async def _get_tool_definition(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed tool definitions for agents"""
        tool_definitions = {
            'analyze_query': {
                "name": "analyze_query",
                "description": "Analyze a customer query and extract insights",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The customer query to analyze"},
                        "context": {"type": "object", "description": "Additional context"},
                        "customer_id": {"type": "string", "description": "Customer identifier"}
                    },
                    "required": ["query"]
                }
            },
            'extract_context': {
                "name": "extract_context",
                "description": "Extract current agent context and state",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            'generate_response': {
                "name": "generate_response",
                "description": "Generate a response based on provided data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query_analysis": {"type": "object", "description": "Query analysis results"},
                        "knowledge_result": {"type": "object", "description": "Knowledge retrieval results"},
                        "customer_context": {"type": "object", "description": "Customer context"}
                    },
                    "required": []
                }
            },
            'get_capabilities': {
                "name": "get_capabilities",
                "description": "Get agent capabilities and supported operations",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            'update_strategy': {
                "name": "update_strategy",
                "description": "Update agent strategy parameters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "strategy": {"type": "object", "description": "New strategy parameters"}
                    },
                    "required": ["strategy"]
                }
            }
        }
        
        return tool_definitions.get(tool_name)
