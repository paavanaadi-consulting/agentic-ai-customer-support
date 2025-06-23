"""
MCP server for Kafka operations
"""
import json
import asyncio
from typing import Dict, Any, List, Optional
from kafka import KafkaProducer, KafkaConsumer
from mcp.base_mcp_server import BaseMCPServer

class KafkaMCPServer(BaseMCPServer):
    """MCP server for Kafka operations"""
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        tools = [
            'publish_message',
            'consume_messages',
            'get_topic_metadata',
            'create_topic',
            'list_topics'
        ]
        
        resources = [
            'kafka://topics',
            'kafka://consumer-groups',
            'kafka://brokers'
        ]
        
        super().__init__(
            server_id="mcp_kafka",
            name="Kafka MCP Server",
            capabilities=['tools', 'resources', 'streaming'],
            tools=tools,
            resources=resources
        )
        
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.consumers = {}
    
    async def start(self):
        """Start the Kafka MCP server"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            self.running = True
            self.logger.info("Kafka MCP server started")
        except Exception as e:
            self.logger.error(f"Failed to start Kafka MCP server: {e}")
            raise
    
    async def stop(self):
        """Stop the Kafka MCP server"""
        if self.producer:
            self.producer.close()
        
        for consumer in self.consumers.values():
            consumer.close()
        
        await super().stop()
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Kafka operations"""
        try:
            if tool_name == 'publish_message':
                topic = arguments.get('topic')
                message = arguments.get('message')
                key = arguments.get('key')
                
                future = self.producer.send(topic, value=message, key=key)
                record_metadata = future.get(timeout=10)
                
                return {
                    'success': True,
                    'topic': record_metadata.topic,
                    'partition': record_metadata.partition,
                    'offset': record_metadata.offset
                }
                
            elif tool_name == 'consume_messages':
                topic = arguments.get('topic')
                group_id = arguments.get('group_id', 'mcp-consumer')
                max_messages = arguments.get('max_messages', 10)
                timeout_ms = arguments.get('timeout_ms', 5000)
                
                consumer = KafkaConsumer(
                    topic,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=group_id,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    consumer_timeout_ms=timeout_ms
                )
                
                messages = []
                for message in consumer:
                    messages.append({
                        'topic': message.topic,
                        'partition': message.partition,
                        'offset': message.offset,
                        'key': message.key.decode('utf-8') if message.key else None,
                        'value': message.value,
                        'timestamp': message.timestamp
                    })
                    
                    if len(messages) >= max_messages:
                        break
                
                consumer.close()
                
                return {
                    'success': True,
                    'messages': messages,
                    'count': len(messages)
                }
                
            elif tool_name == 'get_topic_metadata':
                topic = arguments.get('topic')
                
                metadata = self.producer.client.cluster.topics()
                topic_metadata = metadata.get(topic)
                
                if topic_metadata:
                    return {
                        'success': True,
                        'topic': topic,
                        'partitions': len(topic_metadata.partitions),
                        'partition_details': [
                            {
                                'partition': p.partition,
                                'leader': p.leader,
                                'replicas': p.replicas,
                                'isr': p.isr
                            }
                            for p in topic_metadata.partitions.values()
                        ]
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Topic {topic} not found'
                    }
                    
            elif tool_name == 'list_topics':
                metadata = self.producer.client.cluster.topics()
                
                return {
                    'success': True,
                    'topics': list(metadata.keys())
                }
                
            else:
                return {
                    'success': False,
                    'error': f'Unknown tool: {tool_name}'
                }
                
        except Exception as e:
            self.logger.error(f"Kafka tool error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
        """Get Kafka resource"""
        try:
            if resource_uri == 'kafka://topics':
                metadata = self.producer.client.cluster.topics()
                topics_info = []
                
                for topic_name, topic_metadata in metadata.items():
                    topics_info.append({
                        'name': topic_name,
                        'partitions': len(topic_metadata.partitions)
                    })
                
                return {
                    'success': True,
                    'contents': [
                        {
                            'uri': resource_uri,
                            'mimeType': 'application/json',
                            'text': json.dumps(topics_info, indent=2)
                        }
                    ]
                }
                
            elif resource_uri == 'kafka://brokers':
                brokers = self.producer.client.cluster.brokers()
                broker_info = [
                    {
                        'id': broker.nodeId,
                        'host': broker.host,
                        'port': broker.port
                    }
                    for broker in brokers
                ]
                
                return {
                    'success': True,
                    'contents': [
                        {
                            'uri': resource_uri,
                            'mimeType': 'application/json',
                            'text': json.dumps(broker_info, indent=2)
                        }
                    ]
                }
                
            else:
                return {
                    'success': False,
                    'error': f'Unknown resource: {resource_uri}'
                }
                
        except Exception as e:
            self.logger.error(f"Kafka resource error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _get_tool_definition(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed tool definitions"""
        definitions = {
            'publish_message': {
                "name": "publish_message",
                "description": "Publish a message to a Kafka topic",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Kafka topic name"},
                        "message": {"type": "object", "description": "Message to publish"},
                        "key": {"type": "string", "description": "Message key (optional)"}
                    },
                    "required": ["topic", "message"]
                }
            },
            'consume_messages': {
                "name": "consume_messages",
                "description": "Consume messages from a Kafka topic",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Kafka topic name"},
                        "group_id": {"type": "string", "description": "Consumer group ID"},
                        "max_messages": {"type": "integer", "description": "Maximum messages to consume"},
                        "timeout_ms": {"type": "integer", "description": "Timeout in milliseconds"}
                    },
                    "required": ["topic"]
                }
            }
        }
        
        return definitions.get(tool_name, await super()._get_tool_definition(tool_name))
