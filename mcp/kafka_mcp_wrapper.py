"""
Kafka MCP Wrapper for External Kafka MCP Server
Provides unified interface for external Kafka MCP server with fallback to custom implementation
"""
import os
import json
import subprocess
import asyncio
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ExternalKafkaMCPConfig:
    """Configuration for external Kafka MCP server"""
    bootstrap_servers: str = "localhost:9092"
    topic_name: str = "default-topic"
    group_id: str = "kafka-mcp-group"
    use_uvx: bool = True  # Use uvx for package management
    fallback_to_custom: bool = True

class KafkaMCPWrapper:
    """
    Wrapper for external Kafka MCP server with fallback to custom implementation
    """
    
    def __init__(self, config: ExternalKafkaMCPConfig = None):
        self.config = config or ExternalKafkaMCPConfig()
        self.logger = logging.getLogger("KafkaMCPWrapper")
        self.external_available = False
        self.external_process = None
        self.custom_server = None
        
        # Environment variables for external server
        self.env_vars = {
            "KAFKA_BOOTSTRAP_SERVERS": self.config.bootstrap_servers,
            "TOPIC_NAME": self.config.topic_name,
            "DEFAULT_GROUP_ID_FOR_CONSUMER": self.config.group_id,
            "IS_TOPIC_READ_FROM_BEGINNING": "False"
        }

    async def initialize(self):
        """Initialize the Kafka MCP wrapper"""
        try:
            # Check if external Kafka MCP server is available
            await self._check_external_availability()
            
            if self.external_available:
                self.logger.info("Using external Kafka MCP server")
                await self._setup_external_server()
            elif self.config.fallback_to_custom:
                self.logger.info("External Kafka MCP server not available, falling back to custom implementation")
                await self._setup_custom_fallback()
            else:
                raise RuntimeError("External Kafka MCP server not available and fallback disabled")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Kafka MCP wrapper: {e}")
            if self.config.fallback_to_custom:
                await self._setup_custom_fallback()
            else:
                raise

    async def _check_external_availability(self):
        """Check if external Kafka MCP server package is available"""
        try:
            if self.config.use_uvx:
                # Check if uvx is available and can install the package
                result = await asyncio.create_subprocess_exec(
                    'uvx', '--help',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await result.communicate()
                
                if result.returncode != 0:
                    self.logger.warning("uvx not available, trying pip install")
                    return await self._check_pip_availability()
                
                # Try to install/check external package with uvx
                result = await asyncio.create_subprocess_exec(
                    'uvx', 'run', '--from', 'git+https://github.com/pavanjava/kafka_mcp_server.git',
                    'kafka-mcp-server', '--help',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await result.communicate()
                
                self.external_available = (result.returncode == 0)
            else:
                return await self._check_pip_availability()
                
        except Exception as e:
            self.logger.warning(f"Failed to check external Kafka MCP availability: {e}")
            self.external_available = False

    async def _check_pip_availability(self):
        """Check if external package can be installed via pip"""
        try:
            # Try installing the external package
            result = await asyncio.create_subprocess_exec(
                'pip', 'install', '-q', 'git+https://github.com/pavanjava/kafka_mcp_server.git',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            
            if result.returncode == 0:
                # Test if we can import it
                result = await asyncio.create_subprocess_exec(
                    'python', '-c', 'from kafka_mcp_server.main import main',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await result.communicate()
                
                self.external_available = (result.returncode == 0)
            
        except Exception as e:
            self.logger.warning(f"Failed to check pip installation: {e}")
            self.external_available = False

    async def _setup_external_server(self):
        """Setup external Kafka MCP server"""
        # Set environment variables
        env = os.environ.copy()
        env.update(self.env_vars)
        
        if self.config.use_uvx:
            # Start external server with uvx
            cmd = [
                'uvx', 'run', '--from', 'git+https://github.com/pavanjava/kafka_mcp_server.git',
                'kafka-mcp-server', '--transport', 'stdio'
            ]
        else:
            # Start external server with python
            cmd = ['python', '-c', 'from kafka_mcp_server.main import main; main()']
        
        self.external_process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        self.logger.info("External Kafka MCP server started")

    async def _setup_custom_fallback(self):
        """Setup custom Kafka MCP server as fallback"""
        from mcp.kafka_mcp_server import KafkaMCPServer
        
        self.custom_server = KafkaMCPServer(self.config.bootstrap_servers)
        await self.custom_server.start()
        self.logger.info("Custom Kafka MCP server started as fallback")

    async def start(self):
        """Start the Kafka MCP service"""
        if not hasattr(self, 'external_available'):
            await self.initialize()

    async def stop(self):
        """Stop the Kafka MCP service"""
        if self.external_process:
            self.external_process.terminate()
            await self.external_process.wait()
            self.logger.info("External Kafka MCP server stopped")
            
        if self.custom_server:
            await self.custom_server.stop()
            self.logger.info("Custom Kafka MCP server stopped")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the Kafka MCP server"""
        if self.external_available and self.external_process:
            return await self._call_external_tool(tool_name, arguments)
        elif self.custom_server:
            return await self.custom_server.call_tool(tool_name, arguments)
        else:
            raise RuntimeError("No Kafka MCP server available")

    async def _call_external_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool on external MCP server"""
        try:
            # Map our tool names to external server tool names
            tool_mapping = {
                'publish_message': 'kafka-publish',
                'consume_messages': 'kafka-consume',
                'create_topic': 'create-topic',
                'delete_topic': 'delete-topic',
                'list_topics': 'list-topics',
                'get_topic_metadata': 'cluster-metadata',
                'get_topic_config': 'topic-config',
                'cluster_health': 'cluster-health'
            }
            
            external_tool = tool_mapping.get(tool_name, tool_name)
            
            # Create MCP request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": external_tool,
                    "arguments": arguments
                }
            }
            
            # Send request to external server
            request_json = json.dumps(request) + '\n'
            self.external_process.stdin.write(request_json.encode())
            await self.external_process.stdin.drain()
            
            # Read response
            response_line = await self.external_process.stdout.readline()
            response_data = json.loads(response_line.decode().strip())
            
            if 'error' in response_data:
                return {
                    'success': False,
                    'error': response_data['error']['message']
                }
            else:
                return {
                    'success': True,
                    'result': response_data.get('result', {})
                }
                
        except Exception as e:
            self.logger.error(f"External tool call failed: {e}")
            # Fallback to custom server if available
            if self.custom_server and self.config.fallback_to_custom:
                return await self.custom_server.call_tool(tool_name, arguments)
            else:
                return {
                    'success': False,
                    'error': str(e)
                }

    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        if self.external_available:
            return [
                'publish_message',
                'consume_messages', 
                'create_topic',
                'delete_topic',
                'list_topics',
                'get_topic_metadata',
                'get_topic_config',
                'cluster_health'
            ]
        elif self.custom_server:
            return [
                'publish_message',
                'consume_messages',
                'get_topic_metadata',
                'list_topics'
            ]
        else:
            return []

    async def start_as_server(self):
        """Start as standalone MCP server (for Docker compatibility)"""
        await self.initialize()
        
        if self.external_available and self.external_process:
            # Forward stdin/stdout to external process
            while True:
                try:
                    # Read from stdin and forward to external process
                    line = await asyncio.get_event_loop().run_in_executor(None, input)
                    if self.external_process.stdin:
                        self.external_process.stdin.write((line + '\n').encode())
                        await self.external_process.stdin.drain()
                    
                    # Read from external process and forward to stdout
                    if self.external_process.stdout:
                        response = await self.external_process.stdout.readline()
                        if response:
                            print(response.decode().strip())
                            
                except (EOFError, KeyboardInterrupt):
                    break
                except Exception as e:
                    self.logger.error(f"Server forwarding error: {e}")
                    break
        elif self.custom_server:
            # Use custom server in server mode
            import sys
            import json
            
            while True:
                try:
                    line = sys.stdin.readline().strip()
                    if not line:
                        continue
                        
                    request = json.loads(line)
                    response = await self.custom_server.process_message(request)
                    
                    if response:
                        print(json.dumps(response))
                        
                except (EOFError, KeyboardInterrupt):
                    break
                except Exception as e:
                    self.logger.error(f"Custom server error: {e}")
                    break

    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration information"""
        return {
            'external_available': self.external_available,
            'using_custom_fallback': self.custom_server is not None,
            'bootstrap_servers': self.config.bootstrap_servers,
            'topic_name': self.config.topic_name,
            'group_id': self.config.group_id
        }
