
"""
# FILE: data_sources/kafka_consumer.py
Kafka consumer for real-time customer query processing
"""
import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from kafka import KafkaConsumer, KafkaProducer
import logging
from datetime import datetime

class KafkaConsumer:
    """Kafka consumer for processing customer support events"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.consumer = None
        self.producer = None
        self.logger = logging.getLogger("KafkaConsumer")
        self.running = False
        self.message_handlers = {}
        self.status = "disconnected"
    
    async def start(self):
        """Start Kafka consumer and producer"""
        try:
            # Initialize consumer
            self.consumer = KafkaConsumer(
                *self.config.topics,
                bootstrap_servers=self.config.bootstrap_servers,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='genetic-ai-support',
                value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else None,
                consumer_timeout_ms=1000
            )
            
            # Initialize producer
            self.producer = KafkaProducer(
                bootstrap_servers=self.config.bootstrap_servers,
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            
            self.running = True
            self.status = "connected"
            self.logger.info("Kafka consumer and producer started")
            
            # Start consuming in background
            asyncio.create_task(self._consume_messages())
            
        except Exception as e:
            self.logger.error(f"Failed to start Kafka consumer: {str(e)}")
            self.status = "error"
            raise
    
    async def _consume_messages(self):
        """Background task to consume Kafka messages"""
        while self.running:
            try:
                message_pack = self.consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_pack.items():
                    for message in messages:
                        await self._process_message(
                            topic_partition.topic,
                            message.value,
                            message.offset,
                            message.timestamp
                        )
                
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                self.logger.error(f"Error consuming messages: {str(e)}")
                await asyncio.sleep(1)  # Wait before retrying
    
    async def _process_message(self, topic: str, message_data: Dict[str, Any], 
                             offset: int, timestamp: int):
        """Process individual Kafka message"""
        try:
            if topic in self.message_handlers:
                handler = self.message_handlers[topic]
                await handler(message_data, offset, timestamp)
            else:
                self.logger.debug(f"No handler for topic: {topic}")
                
        except Exception as e:
            self.logger.error(f"Error processing message from {topic}: {str(e)}")
    
    def register_handler(self, topic: str, handler: Callable):
        """Register message handler for specific topic"""
        self.message_handlers[topic] = handler
        self.logger.info(f"Registered handler for topic: {topic}")
    
    async def publish_message(self, topic: str, message: Dict[str, Any]) -> bool:
        """Publish message to Kafka topic"""
        try:
            if not self.producer:
                self.logger.error("Producer not initialized")
                return False
            
            # Add timestamp if not present
            if 'timestamp' not in message:
                message['timestamp'] = datetime.now().isoformat()
            
            # Send message
            future = self.producer.send(topic, value=message)
            record_metadata = future.get(timeout=10)
            
            self.logger.debug(f"Message sent to {topic} at offset {record_metadata.offset}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error publishing message to {topic}: {str(e)}")
            return False
    
    async def publish_query_event(self, query_data: Dict[str, Any]) -> bool:
        """Publish customer query event"""
        event = {
            'event_type': 'customer_query',
            'query_id': query_data.get('query_id'),
            'customer_id': query_data.get('customer_id'),
            'query_text': query_data.get('query'),
            'timestamp': datetime.now().isoformat(),
            'metadata': query_data.get('context', {})
        }
        
        return await self.publish_message('customer-queries', event)
    
    async def publish_feedback_event(self, feedback_data: Dict[str, Any]) -> bool:
        """Publish customer feedback event"""
        event = {
            'event_type': 'customer_feedback',
            'query_id': feedback_data.get('query_id'),
            'customer_id': feedback_data.get('customer_id'),
            'satisfaction_score': feedback_data.get('satisfaction_score'),
            'feedback_text': feedback_data.get('feedback_text', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        return await self.publish_message('feedback-events', event)
    
    async def publish_agent_performance_event(self, performance_data: Dict[str, Any]) -> bool:
        """Publish agent performance event"""
        event = {
            'event_type': 'agent_performance',
            'agent_id': performance_data.get('agent_id'),
            'generation': performance_data.get('generation'),
            'fitness_score': performance_data.get('fitness_score'),
            'performance_metrics': performance_data.get('performance_metrics', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        return await self.publish_message('agent-performance', event)
    
    async def get_recent_messages(self, topic: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages from a topic (for monitoring purposes)"""
        try:
            # This is a simplified implementation
            # In practice, you might want to use a separate consumer with specific offset management
            temp_consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.config.bootstrap_servers,
                auto_offset_reset='latest',
                enable_auto_commit=False,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else None,
                consumer_timeout_ms=5000
            )
            
            messages = []
            try:
                for message in temp_consumer:
                    messages.append({
                        'value': message.value,
                        'offset': message.offset,
                        'timestamp': message.timestamp,
                        'partition': message.partition
                    })
                    
                    if len(messages) >= count:
                        break
                        
            finally:
                temp_consumer.close()
            
            return messages
            
        except Exception as e:
            self.logger.error(f"Error getting recent messages: {str(e)}")
            return []
    
    async def stop(self):
        """Stop Kafka consumer and producer"""
        self.running = False
        
        if self.consumer:
            self.consumer.close()
        
        if self.producer:
            self.producer.close()
        
        self.status = "disconnected"
        self.logger.info("Kafka consumer and producer stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of Kafka connection"""
        return {
            'status': self.status,
            'running': self.running,
            'topics': self.config.topics,
            'bootstrap_servers': self.config.bootstrap_servers,
            'registered_handlers': list(self.message_handlers.keys())
        }
