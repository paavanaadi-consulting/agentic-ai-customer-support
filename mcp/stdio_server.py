"""
STDIO-based MCP server implementation
"""
import asyncio
import json
import sys
from typing import Dict, Any, List, Callable
from mcp.base_mcp_server import BaseMCPServer

class MCPStdioServer(BaseMCPServer):
    """STDIO-based MCP server for process communication"""
    
    def __init__(self, server_id: str, name: str, capabilities: List[str],
                 tools: List[str], resources: List[str]):
        super().__init__(server_id, name, capabilities, tools, resources)
        self.stdin_reader = None
        self.stdout_writer = None
        
    async def start(self):
        """Start the STDIO server"""
        try:
            # Set up STDIO streams
            self.stdin_reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(self.stdin_reader)
            await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
            
            self.stdout_writer = sys.stdout
            
            self.running = True
            self.logger.info(f"STDIO MCP server {self.name} started")
            
            # Start message handling
            asyncio.create_task(self._handle_messages())
            
        except Exception as e:
            self.logger.error(f"Failed to start STDIO server: {e}")
            raise
    
    async def _handle_messages(self):
        """Handle incoming messages from STDIN"""
        while self.running:
            try:
                line = await self.stdin_reader.readline()
                if not line:
                    break
                
                message = json.loads(line.decode().strip())
                response = await self.process_message(message)
                
                if response:
                    await self._send_response(response)
                    
            except json.JSONDecodeError:
                await self._send_error("Invalid JSON received")
            except Exception as e:
                await self._send_error(f"Message processing error: {e}")
    
    async def _send_response(self, response: Dict[str, Any]):
        """Send response through STDOUT"""
        try:
            json_response = json.dumps(response)
            self.stdout_writer.write(json_response + '\n')
            self.stdout_writer.flush()
            
        except Exception as e:
            self.logger.error(f"Error sending response: {e}")
    
    async def _send_error(self, error_message: str):
        """Send error response"""
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32000,
                "message": error_message
            }
        }
        await self._send_response(error_response)
