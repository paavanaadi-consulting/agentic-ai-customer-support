"""
WebSocket-based MCP server implementation
"""
import asyncio
import json
import websockets
from typing import Dict, Any, List
from mcp.base_mcp_server import BaseMCPServer

class MCPWebSocketServer(BaseMCPServer):
    """WebSocket-based MCP server for network communication"""
    
    def __init__(self, server_id: str, name: str, host: str, port: int,
                 capabilities: List[str], tools: List[str], resources: List[str]):
        super().__init__(server_id, name, capabilities, tools, resources)
        self.host = host
        self.port = port
        self.server = None
        self.clients = set()
        
    async def start(self):
        """Start the WebSocket server"""
        try:
            self.server = await websockets.serve(
                self._handle_client,
                self.host,
                self.port
            )
            
            self.running = True
            self.logger.info(f"WebSocket MCP server {self.name} started on {self.host}:{self.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start WebSocket server: {e}")
            raise
    
    async def _handle_client(self, websocket, path):
        """Handle WebSocket client connections"""
        self.clients.add(websocket)
        self.logger.info(f"New MCP client connected: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                try:
                    json_message = json.loads(message)
                    response = await self.process_message(json_message)
                    
                    if response:
                        await websocket.send(json.dumps(response))
                        
                except json.JSONDecodeError:
                    await self._send_error(websocket, "Invalid JSON received")
                except Exception as e:
                    await self._send_error(websocket, f"Message processing error: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"MCP client disconnected: {websocket.remote_address}")
        finally:
            self.clients.discard(websocket)
    
    async def _send_error(self, websocket, error_message: str):
        """Send error response to specific client"""
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32000,
                "message": error_message
            }
        }
        try:
            await websocket.send(json.dumps(error_response))
        except Exception:
            pass  # Client might have disconnected
    
    async def broadcast_to_clients(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients],
                return_exceptions=True
            )
