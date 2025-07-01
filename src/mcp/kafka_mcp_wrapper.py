"""
Kafka MCP Wrapper for Confluent MCP Kafka Server
Provides unified interface for Confluent MCP Kafka server with fallback to custom implementation
"""
import os
import json
import subprocess
import asyncio
import logging
import sys
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ExternalKafkaMCPConfig:
    """Configuration for Confluent MCP Kafka server"""
    bootstrap_servers: str = "localhost:9092"
    topic_name: str = "default-topic"
    group_id: str = "kafka-mcp-group"
    use_uvx: bool = True  # Use uvx for package management
    fallback_to_custom: bool = True

class BasicKafkaWrapper:
    """Basic Kafka wrapper for fallback functionality"""
    
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.admin_client = None
        self.logger = logging.getLogger("BasicKafkaWrapper")
    
    async def initialize(self):
        """Initialize Kafka connections"""
        try:
            from kafka import KafkaProducer, KafkaAdminClient
            import json
            
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            
            self.admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers
            )
            
            self.logger.info("Basic Kafka wrapper initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize basic Kafka wrapper: {e}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool with basic Kafka operations"""
        try:
            if tool_name == 'publish_message':
                return await self._publish_message(arguments)
            elif tool_name == 'list_topics':
                return await self._list_topics()
            elif tool_name == 'get_topic_metadata':
                return await self._get_topic_metadata(arguments)
            elif tool_name == 'consume_messages':
                return await self._consume_messages(arguments)
            else:
                return {
                    'success': False,
                    'error': f"Tool '{tool_name}' not supported in basic fallback"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _publish_message(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Publish message to Kafka topic"""
        topic = arguments.get('topic')
        message = arguments.get('message', arguments.get('value'))
        key = arguments.get('key')
        
        try:
            future = self.producer.send(topic, value=message, key=key)
            record_metadata = future.get(timeout=10)
            
            return {
                'success': True,
                'result': {
                    'topic': record_metadata.topic,
                    'partition': record_metadata.partition,
                    'offset': record_metadata.offset
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _list_topics(self) -> Dict[str, Any]:
        """List available topics"""
        try:
            metadata = self.admin_client.describe_topics()
            topics = list(metadata.keys())
            
            return {
                'success': True,
                'result': {
                    'topics': topics
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _get_topic_metadata(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get topic metadata"""
        topic = arguments.get('topic')
        
        try:
            metadata = self.admin_client.describe_topics([topic])
            topic_metadata = metadata.get(topic, {})
            
            return {
                'success': True,
                'result': {
                    'topic': topic,
                    'metadata': topic_metadata
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _consume_messages(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Consume messages from topic (basic implementation)"""
        topic = arguments.get('topic')
        max_messages = arguments.get('max_messages', 10)
        
        try:
            from kafka import KafkaConsumer
            import json
            
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                consumer_timeout_ms=5000,
                auto_offset_reset='earliest'
            )
            
            messages = []
            for i, message in enumerate(consumer):
                if i >= max_messages:
                    break
                messages.append({
                    'topic': message.topic,
                    'partition': message.partition,
                    'offset': message.offset,
                    'key': message.key.decode('utf-8') if message.key else None,
                    'value': message.value
                })
            
            consumer.close()
            
            return {
                'success': True,
                'result': {
                    'messages': messages,
                    'count': len(messages)
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def stop(self):
        """Stop the basic Kafka wrapper"""
        if self.producer:
            self.producer.close()
        self.logger.info("Basic Kafka wrapper stopped")

class KafkaMCPWrapper:
    """
    Wrapper for Confluent MCP Kafka server with fallback to custom implementation
    """
    
    def __init__(self, config: ExternalKafkaMCPConfig = None):
        self.config = config or ExternalKafkaMCPConfig()
        self.logger = logging.getLogger("KafkaMCPWrapper")
        self.external_available = False
        self.external_process = None
        self.custom_server = None
        
        # Environment variables for Confluent server
        self.env_vars = {
            "KAFKA_BOOTSTRAP_SERVERS": self.config.bootstrap_servers,
            "KAFKA_TOPIC_NAME": self.config.topic_name,
            "KAFKA_GROUP_ID": self.config.group_id,
            "KAFKA_AUTO_OFFSET_RESET": "earliest"
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
        """Check if Confluent MCP Kafka server package is available"""
        try:
            # First try to import the package directly
            try:
                import confluent_mcp
                self.external_available = True
                self.logger.info("Confluent MCP package found")
                return
            except ImportError:
                self.logger.info("Confluent MCP package not found, attempting installation")
            
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
                
                # Try to install Confluent MCP package with uvx
                result = await asyncio.create_subprocess_exec(
                    'uvx', 'install', 'git+https://github.com/confluentinc/mcp-confluent.git',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await result.communicate()
                
                self.external_available = (result.returncode == 0)
                if self.external_available:
                    self.logger.info("Confluent MCP installed via uvx")
            else:
                return await self._check_pip_availability()
                
        except Exception as e:
            self.logger.warning(f"Failed to check official MCP Kafka availability: {e}")
            self.external_available = False

    async def _check_pip_availability(self):
        """Check if official package can be installed via pip"""
        try:
            # Try installing the official package
            result = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'pip', 'install', 
                'git+https://github.com/modelcontextprotocol/kafka-mcp.git',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                self.external_available = True
                self.logger.info("Official kafka-mcp installed via pip")
                # Try to import after installation
                try:
                    import kafka_mcp
                    return True
                except ImportError as e:
                    self.logger.warning(f"Installation succeeded but import failed: {e}")
                    self.external_available = False
            else:
                self.logger.warning(f"pip install failed: {stderr.decode()}")
                self.external_available = False
            
        except Exception as e:
            self.logger.warning(f"Failed to check pip installation: {e}")
            self.external_available = False

    async def _setup_external_server(self):
        """Setup external Kafka MCP server (Confluent MCP)"""
        # Set environment variables
        env = os.environ.copy()
        env.update(self.env_vars)
        
        # Check if we're running in Docker and can connect to external Confluent MCP server
        external_host = os.getenv('EXTERNAL_KAFKA_MCP_HOST', 'localhost')
        external_port = os.getenv('EXTERNAL_KAFKA_MCP_PORT', '8002')
        
        self.logger.info(f"Connecting to external Confluent MCP server at {external_host}:{external_port}")
        
        # Note: In this setup, the external Confluent MCP server is managed by Docker Compose
        # We don't start it here, just mark that it's available for use
        self.external_available = True
        self.external_host = external_host
        self.external_port = external_port
        
        self.logger.info("External Confluent Kafka MCP server connection configured")

    async def _setup_custom_fallback(self):
        """Setup custom Kafka MCP server as fallback"""
        try:
            # Try to import basic Kafka functionality as fallback
            from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
            from kafka.admin import ConfigResource, NewTopic
            
            # Create a simple wrapper for basic Kafka operations
            self.custom_server = BasicKafkaWrapper(self.config.bootstrap_servers)
            await self.custom_server.initialize()
            self.logger.info("Basic Kafka wrapper started as fallback")
        except ImportError:
            self.logger.error("No Kafka libraries available for fallback. Please install kafka-python or the official MCP package")
            raise RuntimeError("No Kafka implementation available")

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
        """Call tool on external Confluent MCP server"""
        try:
            import aiohttp
            
            # Map our tool names to Confluent MCP server tool names
            tool_mapping = {
                'publish_message': 'kafka_publish',
                'consume_messages': 'kafka_consume',
                'create_topic': 'kafka_create_topic',
                'delete_topic': 'kafka_delete_topic',
                'list_topics': 'kafka_list_topics',
                'get_topic_metadata': 'kafka_describe_topic',
                'describe_cluster': 'kafka_describe_cluster',
                'consumer_groups': 'kafka_consumer_groups'
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
            
            # Send HTTP request to external Confluent MCP server
            url = f"http://{self.external_host}:{self.external_port}/mcp"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=request) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        
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
                    else:
                        return {
                            'success': False,
                            'error': f"HTTP {response.status}: {await response.text()}"
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
                'describe_cluster',
                'consumer_groups'
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
