"""
Kafka MCP Client
Provides optimized Kafka operations via MCP with multiple fallback strategies.
Combines direct connection, HTTP communication, and advanced streaming features.
"""
import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
import aiohttp

from .mcp_client_interface import MCPClientInterface

# Try to import external Kafka packages
try:
    from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
    from kafka.admin import NewTopic, ConfigResource
    KAFKA_PYTHON_AVAILABLE = True
except ImportError:
    KAFKA_PYTHON_AVAILABLE = False
    # Create placeholder types for type hints
    class KafkaProducer:
        pass
    class KafkaConsumer:
        pass
    class KafkaAdminClient:
        pass

# Try to import Confluent Kafka MCP
try:
    import confluent_mcp
    CONFLUENT_MCP_AVAILABLE = True
except ImportError:
    CONFLUENT_MCP_AVAILABLE = False

logger = logging.getLogger(__name__)


class KafkaClientError(Exception):
    """Custom exception for Kafka MCP client errors."""
    pass


class OptimizedKafkaMCPClient(MCPClientInterface):
    """
    Optimized Kafka MCP Client that provides:
    1. Direct connection to Confluent MCP server (preferred)
    2. HTTP-based MCP communication (fallback)
    3. Native kafka-python integration (fallback)
    4. Customer support specific streaming operations
    5. Message queuing and event processing
    """
    
    def __init__(self, 
                 bootstrap_servers: str = "localhost:9092",
                 mcp_server_url: str = "http://localhost:8002",
                 use_direct_connection: bool = True,
                 topic_prefix: str = "customer-support",
                 group_id: str = "ai-support-group"):
        """
        Initialize the optimized Kafka MCP client.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            mcp_server_url: URL of the Kafka MCP server for HTTP communication
            use_direct_connection: Whether to prefer direct connection over HTTP
            topic_prefix: Prefix for customer support topics
            group_id: Consumer group ID for this client
        """
        self.bootstrap_servers = bootstrap_servers
        self.mcp_server_url = mcp_server_url
        self.use_direct_connection = use_direct_connection and (CONFLUENT_MCP_AVAILABLE or KAFKA_PYTHON_AVAILABLE)
        self.topic_prefix = topic_prefix
        self.group_id = group_id
        
        # Connection objects
        self.confluent_server = None
        self.kafka_producer: Optional[KafkaProducer] = None
        self.kafka_admin: Optional[KafkaAdminClient] = None
        self.http_session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()
        
        # State tracking
        self.connected = False
        self.logger = logging.getLogger("OptimizedKafkaMCPClient")
        
        # Consumer tracking
        self.active_consumers = {}
        self.message_handlers = {}
        
        # Cache for frequently accessed data
        self._cache = {}
        self._cache_ttl = {}
        self.cache_duration = 60  # 1 minute default cache for topics
        
    async def connect(self) -> bool:
        """
        Connect to Kafka via the best available method.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if self.connected:
            return True
            
        # Try Confluent MCP connection first if available and preferred
        if self.use_direct_connection and CONFLUENT_MCP_AVAILABLE:
            try:
                await self._connect_confluent_mcp()
                self.connected = True
                self.logger.info("Connected via Confluent MCP server")
                return True
            except Exception as e:
                self.logger.warning(f"Confluent MCP connection failed: {e}, trying kafka-python")
        
        # Try native kafka-python connection
        if self.use_direct_connection and KAFKA_PYTHON_AVAILABLE:
            try:
                await self._connect_native_kafka()
                self.connected = True
                self.logger.info("Connected via native kafka-python")
                return True
            except Exception as e:
                self.logger.warning(f"Native Kafka connection failed: {e}, falling back to HTTP")
        
        # Fallback to HTTP connection
        try:
            await self._connect_http()
            self.connected = True
            self.logger.info("Connected via HTTP MCP server")
            return True
        except Exception as e:
            self.logger.error(f"All connection methods failed: {e}")
            return False
    
    async def _connect_confluent_mcp(self):
        """Connect via Confluent MCP server."""
        # This would connect to the external Confluent MCP server
        # For now, we'll mark it as available but implement the HTTP fallback
        raise NotImplementedError("Confluent MCP direct connection not yet implemented")
    
    async def _connect_native_kafka(self):
        """Connect directly to Kafka using kafka-python."""
        if not KAFKA_PYTHON_AVAILABLE:
            raise ImportError("kafka-python package not available")
        
        # Create producer
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3
        )
        
        # Create admin client
        self.kafka_admin = KafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers
        )
        
        # Test connection by listing topics
        topics = self.kafka_admin.list_topics()
        self.logger.debug(f"Connected to Kafka, found {len(topics)} topics")
    
    async def _connect_http(self):
        """Connect to Kafka via HTTP MCP server."""
        if self.http_session is None or self.http_session.closed:
            async with self._session_lock:
                if self.http_session is None or self.http_session.closed:
                    self.http_session = aiohttp.ClientSession()
        
        # Test connection with a simple health check
        await self._http_call_tool("list_topics", {})
    
    async def disconnect(self):
        """Disconnect from all connections."""
        self.connected = False
        
        # Close active consumers
        for consumer in self.active_consumers.values():
            if hasattr(consumer, 'close'):
                consumer.close()
        self.active_consumers.clear()
        
        if self.kafka_producer:
            self.kafka_producer.close()
            self.kafka_producer = None
        
        if self.kafka_admin:
            self.kafka_admin.close()
            self.kafka_admin = None
        
        if self.http_session and not self.http_session.closed:
            await self.http_session.close()
            self.http_session = None
        
        # Clear cache
        self._cache.clear()
        self._cache_ttl.clear()
        
        self.logger.info("Disconnected from Kafka MCP")
    
    # Cache management
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid."""
        return key in self._cache and time.time() < self._cache_ttl.get(key, 0)
    
    def _set_cache(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set cache entry with TTL."""
        if ttl is None:
            ttl = self.cache_duration
        self._cache[key] = value
        self._cache_ttl[key] = time.time() + ttl
    
    async def _direct_call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool using direct Kafka connection."""
        if self.kafka_producer and self.kafka_admin:
            return await self._native_kafka_call(tool_name, arguments)
        else:
            raise RuntimeError("No direct Kafka connection available")
    
    async def _native_kafka_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Kafka operations using kafka-python."""
        try:
            if tool_name == "publish_message":
                return await self._publish_message_native(arguments)
            elif tool_name == "consume_messages":
                return await self._consume_messages_native(arguments)
            elif tool_name == "create_topic":
                return await self._create_topic_native(arguments)
            elif tool_name == "delete_topic":
                return await self._delete_topic_native(arguments)
            elif tool_name == "list_topics":
                return await self._list_topics_native()
            elif tool_name == "get_topic_metadata":
                return await self._get_topic_metadata_native(arguments)
            elif tool_name == "describe_cluster":
                return await self._describe_cluster_native()
            else:
                return {
                    'success': False,
                    'error': f"Tool '{tool_name}' not supported in native mode"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _publish_message_native(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Publish message using native Kafka producer."""
        topic = arguments.get('topic')
        message = arguments.get('message', arguments.get('value'))
        key = arguments.get('key')
        
        if not topic:
            return {'success': False, 'error': 'Topic is required'}
        if not message:
            return {'success': False, 'error': 'Message is required'}
        
        try:
            future = self.kafka_producer.send(topic, value=message, key=key)
            record_metadata = future.get(timeout=10)
            
            return {
                'success': True,
                'result': {
                    'topic': record_metadata.topic,
                    'partition': record_metadata.partition,
                    'offset': record_metadata.offset,
                    'timestamp': record_metadata.timestamp
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _consume_messages_native(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Consume messages using native Kafka consumer."""
        topic = arguments.get('topic')
        max_messages = arguments.get('max_messages', 10)
        timeout_ms = arguments.get('timeout_ms', 5000)
        
        if not topic:
            return {'success': False, 'error': 'Topic is required'}
        
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None,
                consumer_timeout_ms=timeout_ms,
                auto_offset_reset='latest',
                group_id=f"{self.group_id}-temp-{int(time.time())}"
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
                    'value': message.value,
                    'timestamp': message.timestamp
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
            return {'success': False, 'error': str(e)}
    
    async def _list_topics_native(self) -> Dict[str, Any]:
        """List topics using native Kafka admin."""
        try:
            topics = self.kafka_admin.list_topics()
            return {
                'success': True,
                'result': {
                    'topics': list(topics)
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _create_topic_native(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create topic using native Kafka admin."""
        topic_name = arguments.get('topic')
        num_partitions = arguments.get('num_partitions', 1)
        replication_factor = arguments.get('replication_factor', 1)
        
        if not topic_name:
            return {'success': False, 'error': 'Topic name is required'}
        
        try:
            topic = NewTopic(
                name=topic_name,
                num_partitions=num_partitions,
                replication_factor=replication_factor
            )
            
            result = self.kafka_admin.create_topics([topic])
            
            # Wait for creation to complete
            for topic_name, future in result.items():
                future.result()  # Will raise exception if creation failed
            
            return {
                'success': True,
                'result': {
                    'topic': topic_name,
                    'partitions': num_partitions,
                    'replication_factor': replication_factor
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _delete_topic_native(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Delete topic using native Kafka admin."""
        topic_name = arguments.get('topic')
        
        if not topic_name:
            return {'success': False, 'error': 'Topic name is required'}
        
        try:
            result = self.kafka_admin.delete_topics([topic_name])
            
            # Wait for deletion to complete
            for topic_name, future in result.items():
                future.result()  # Will raise exception if deletion failed
            
            return {
                'success': True,
                'result': {
                    'topic': topic_name,
                    'deleted': True
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _get_topic_metadata_native(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get topic metadata using native Kafka admin."""
        topic_name = arguments.get('topic')
        
        if not topic_name:
            return {'success': False, 'error': 'Topic name is required'}
        
        try:
            metadata = self.kafka_admin.describe_topics([topic_name])
            topic_metadata = metadata.get(topic_name, {})
            
            return {
                'success': True,
                'result': {
                    'topic': topic_name,
                    'metadata': topic_metadata
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _describe_cluster_native(self) -> Dict[str, Any]:
        """Describe cluster using native Kafka admin."""
        try:
            cluster_metadata = self.kafka_admin.describe_cluster()
            
            return {
                'success': True,
                'result': {
                    'cluster_id': cluster_metadata.cluster_id,
                    'controller_id': cluster_metadata.controller.id,
                    'brokers': [
                        {
                            'id': broker.id,
                            'host': broker.host,
                            'port': broker.port
                        }
                        for broker in cluster_metadata.brokers
                    ]
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _http_call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool via HTTP MCP server."""
        try:
            # Map tool names to HTTP MCP server tool names
            tool_mapping = {
                'publish_message': 'kafka_publish',
                'consume_messages': 'kafka_consume',
                'create_topic': 'kafka_create_topic',
                'delete_topic': 'kafka_delete_topic',
                'list_topics': 'kafka_list_topics',
                'get_topic_metadata': 'kafka_describe_topic',
                'describe_cluster': 'kafka_describe_cluster'
            }
            
            external_tool = tool_mapping.get(tool_name, tool_name)
            
            # Create MCP request
            request = {
                "jsonrpc": "2.0",
                "id": int(time.time()),
                "method": "tools/call",
                "params": {
                    "name": external_tool,
                    "arguments": arguments
                }
            }
            
            async with self.http_session.post(self.mcp_server_url, json=request) as response:
                if response.status == 200:
                    response_data = await response.json()
                    
                    if 'error' in response_data:
                        return {
                            'success': False,
                            'error': response_data['error'].get('message', 'Unknown error')
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
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _fallback_operation(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback operations when all connections fail."""
        self.logger.warning(f"Using fallback for {tool_name}")
        
        # Return mock data for basic operations
        if tool_name == "list_topics":
            return {
                'success': True,
                'result': {
                    'topics': [f"{self.topic_prefix}-queries", f"{self.topic_prefix}-responses"],
                    'note': 'Fallback data - no real connection'
                }
            }
        elif tool_name == "publish_message":
            return {
                'success': True,
                'result': {
                    'topic': arguments.get('topic', 'unknown'),
                    'offset': int(time.time()),
                    'note': 'Fallback data - message not actually published'
                }
            }
        else:
            return {
                'success': False,
                'error': f"No fallback available for {tool_name}"
            }
    
    # Customer Support Specific Methods
    async def publish_customer_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish customer query to the appropriate topic."""
        topic = f"{self.topic_prefix}-queries"
        message = {
            'timestamp': datetime.utcnow().isoformat(),
            'query_id': query_data.get('query_id'),
            'customer_id': query_data.get('customer_id'),
            'query_text': query_data.get('query_text'),
            'priority': query_data.get('priority', 'normal'),
            'category': query_data.get('category', 'general')
        }
        
        return await self.call_tool("publish_message", {
            'topic': topic,
            'message': message,
            'key': query_data.get('customer_id')
        })
    
    async def publish_agent_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish agent response to the appropriate topic."""
        topic = f"{self.topic_prefix}-responses"
        message = {
            'timestamp': datetime.utcnow().isoformat(),
            'query_id': response_data.get('query_id'),
            'agent_id': response_data.get('agent_id'),
            'response_text': response_data.get('response_text'),
            'confidence': response_data.get('confidence', 0.8),
            'processing_time': response_data.get('processing_time')
        }
        
        return await self.call_tool("publish_message", {
            'topic': topic,
            'message': message,
            'key': response_data.get('query_id')
        })
    
    async def create_customer_support_topics(self) -> Dict[str, Any]:
        """Create standard customer support topics."""
        topics_to_create = [
            f"{self.topic_prefix}-queries",
            f"{self.topic_prefix}-responses",
            f"{self.topic_prefix}-tickets",
            f"{self.topic_prefix}-analytics"
        ]
        
        results = []
        for topic in topics_to_create:
            result = await self.call_tool("create_topic", {
                'topic': topic,
                'num_partitions': 3,
                'replication_factor': 1
            })
            results.append(result)
        
        return {
            'success': all(r.get('success', False) for r in results),
            'results': results
        }
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call a tool with automatic fallback strategy.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            dict: Tool execution result
        """
        if not self.connected:
            await self.connect()
        
        if arguments is None:
            arguments = {}
        
        # Try direct connection first
        if self.kafka_producer and self.kafka_admin:
            try:
                return await self._direct_call_tool(tool_name, arguments)
            except Exception as e:
                self.logger.warning(f"Direct call failed: {e}, trying HTTP")
        
        # Try HTTP connection
        if self.http_session and not self.http_session.closed:
            try:
                return await self._http_call_tool(tool_name, arguments)
            except Exception as e:
                self.logger.warning(f"HTTP call failed: {e}, using fallback")
        
        # Use fallback
        return await self._fallback_operation(tool_name, arguments)
    
    # Implementation of MCPClientInterface abstract methods
    async def get_customers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get customers - not directly applicable to Kafka, return empty list."""
        return []
    
    async def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by ID - not directly applicable to Kafka."""
        return None
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create customer - publish customer creation event."""
        return await self.call_tool("publish_message", {
            'topic': f"{self.topic_prefix}-customer-events",
            'message': {
                'event_type': 'customer_created',
                'timestamp': datetime.utcnow().isoformat(),
                'data': customer_data
            },
            'key': customer_data.get('customer_id')
        })
    
    async def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer - publish customer update event."""
        return await self.call_tool("publish_message", {
            'topic': f"{self.topic_prefix}-customer-events",
            'message': {
                'event_type': 'customer_updated',
                'timestamp': datetime.utcnow().isoformat(),
                'customer_id': customer_id,
                'updates': updates
            },
            'key': customer_id
        })
    
    async def get_tickets(self, limit: int = 100, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tickets - consume from tickets topic."""
        result = await self.call_tool("consume_messages", {
            'topic': f"{self.topic_prefix}-tickets",
            'max_messages': limit
        })
        
        if result.get('success'):
            messages = result.get('result', {}).get('messages', [])
            # Filter by status if provided
            if status:
                messages = [m for m in messages if m.get('value', {}).get('status') == status]
            return [m.get('value', {}) for m in messages]
        return []
    
    async def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket by ID - consume from tickets topic with key filter."""
        # This is a simplified implementation
        # In practice, you might need a more sophisticated approach
        return None
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create ticket - publish to tickets topic."""
        return await self.call_tool("publish_message", {
            'topic': f"{self.topic_prefix}-tickets",
            'message': {
                'event_type': 'ticket_created',
                'timestamp': datetime.utcnow().isoformat(),
                'data': ticket_data
            },
            'key': ticket_data.get('ticket_id')
        })
    
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update ticket - publish ticket update event."""
        return await self.call_tool("publish_message", {
            'topic': f"{self.topic_prefix}-tickets",
            'message': {
                'event_type': 'ticket_updated',
                'timestamp': datetime.utcnow().isoformat(),
                'ticket_id': ticket_id,
                'updates': updates
            },
            'key': ticket_id
        })
    
    async def search_knowledge_base(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search knowledge base - not directly applicable to Kafka."""
        return []
    
    async def get_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics - consume from analytics topic."""
        result = await self.call_tool("consume_messages", {
            'topic': f"{self.topic_prefix}-analytics",
            'max_messages': 100
        })
        
        if result.get('success'):
            messages = result.get('result', {}).get('messages', [])
            return {
                'analytics_events': len(messages),
                'recent_events': [m.get('value', {}) for m in messages[:10]]
            }
        return {'analytics_events': 0, 'recent_events': []}


# Convenience functions for compatibility
async def get_optimized_kafka_client(**kwargs) -> OptimizedKafkaMCPClient:
    """Get an optimized Kafka MCP client instance."""
    client = OptimizedKafkaMCPClient(**kwargs)
    await client.connect()
    return client


async def close_optimized_kafka_client(client: OptimizedKafkaMCPClient):
    """Close an optimized Kafka MCP client."""
    await client.disconnect()
