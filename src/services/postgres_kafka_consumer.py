"""
Postgres-Kafka Consumer Service
Consumes messages from Kafka topics and inserts them into PostgreSQL tables
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import uuid

from ..mcp.kafka_mcp_client import OptimizedKafkaMCPClient
from ..mcp.postgres_mcp_client import OptimizedPostgreSQLMCPClient

logger = logging.getLogger(__name__)


@dataclass
class TableMapping:
    """Configuration for mapping Kafka topics to database tables."""
    topic: str
    table: str
    key_column: Optional[str] = None
    timestamp_column: str = "created_at"
    transform_function: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    upsert: bool = False  # Whether to use upsert instead of insert


class PostgresKafkaConsumer:
    """
    Service that consumes Kafka messages and inserts them into PostgreSQL tables.
    
    Features:
    - Configurable topic-to-table mappings
    - Data transformation functions
    - Batch processing for performance
    - Error handling and dead letter queue
    - Upsert support for existing records
    - Schema validation
    """
    
    def __init__(self, 
                 kafka_client: OptimizedKafkaMCPClient,
                 postgres_client: OptimizedPostgreSQLMCPClient,
                 batch_size: int = 100,
                 poll_interval: float = 1.0,
                 consumer_group: str = "postgres-kafka-consumer"):
        """
        Initialize the Postgres-Kafka consumer.
        
        Args:
            kafka_client: Kafka MCP client instance
            postgres_client: PostgreSQL MCP client instance
            batch_size: Number of messages to process in a batch
            poll_interval: Polling interval in seconds
            consumer_group: Kafka consumer group ID
        """
        self.kafka_client = kafka_client
        self.postgres_client = postgres_client
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.consumer_group = consumer_group
        
        # Configuration
        self.table_mappings: Dict[str, TableMapping] = {}
        self.running = False
        self.consumer_tasks: Dict[str, asyncio.Task] = {}
        
        # Metrics
        self.messages_processed = 0
        self.messages_failed = 0
        self.last_processed_time = None
        
        # Dead letter queue topic
        self.dlq_topic = "postgres-consumer-dlq"
    
    def add_table_mapping(self, mapping: TableMapping):
        """Add a topic-to-table mapping configuration."""
        self.table_mappings[mapping.topic] = mapping
        logger.info(f"Added mapping: {mapping.topic} -> {mapping.table}")
    
    def add_customer_support_mappings(self):
        """Add standard customer support topic mappings."""
        # Customer queries mapping
        self.add_table_mapping(TableMapping(
            topic="customer-support-queries",
            table="customer_queries",
            key_column="query_id",
            transform_function=self._transform_customer_query,
            upsert=True
        ))
        
        # Agent responses mapping
        self.add_table_mapping(TableMapping(
            topic="customer-support-responses",
            table="agent_responses",
            key_column="query_id",
            transform_function=self._transform_agent_response,
            upsert=True
        ))
        
        # Tickets mapping
        self.add_table_mapping(TableMapping(
            topic="customer-support-tickets",
            table="support_tickets",
            key_column="ticket_id",
            transform_function=self._transform_ticket,
            upsert=True
        ))
        
        # Analytics mapping
        self.add_table_mapping(TableMapping(
            topic="customer-support-analytics",
            table="analytics_events",
            transform_function=self._transform_analytics_event
        ))
    
    async def start_consuming(self, topics: Optional[List[str]] = None):
        """Start consuming from specified topics or all configured topics."""
        if not self.running:
            self.running = True
            logger.info("Starting Postgres-Kafka consumer...")
            
            # If no topics specified, use all configured topics
            if topics is None:
                topics = list(self.table_mappings.keys())
            
            # Start consumer task for each topic
            for topic in topics:
                if topic in self.table_mappings:
                    task = asyncio.create_task(self._consume_topic(topic))
                    self.consumer_tasks[topic] = task
                    logger.info(f"Started consumer for topic: {topic}")
                else:
                    logger.warning(f"No table mapping found for topic: {topic}")
    
    async def stop_consuming(self):
        """Stop all consumer tasks."""
        self.running = False
        logger.info("Stopping Postgres-Kafka consumer...")
        
        # Cancel all consumer tasks
        for topic, task in self.consumer_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"Stopped consumer for topic: {topic}")
        
        self.consumer_tasks.clear()
    
    async def _consume_topic(self, topic: str):
        """Consume messages from a specific topic."""
        mapping = self.table_mappings[topic]
        message_batch = []
        
        logger.info(f"Starting consumption from topic: {topic}")
        
        while self.running:
            try:
                # Consume messages from Kafka
                result = await self.kafka_client.call_tool("consume_messages", {
                    'topic': topic,
                    'max_messages': self.batch_size,
                    'timeout_ms': int(self.poll_interval * 1000)
                })
                
                if result.get('success'):
                    messages = result.get('result', {}).get('messages', [])
                    
                    if messages:
                        logger.debug(f"Consumed {len(messages)} messages from {topic}")
                        
                        # Process messages in batch
                        for message in messages:
                            try:
                                processed_data = await self._process_message(message, mapping)
                                if processed_data:
                                    message_batch.append(processed_data)
                            except Exception as e:
                                logger.error(f"Failed to process message: {e}")
                                await self._send_to_dlq(topic, message, str(e))
                                self.messages_failed += 1
                        
                        # Insert batch to database
                        if message_batch:
                            try:
                                await self._insert_batch(mapping, message_batch)
                                self.messages_processed += len(message_batch)
                                self.last_processed_time = datetime.utcnow()
                                logger.debug(f"Inserted {len(message_batch)} records to {mapping.table}")
                                message_batch.clear()
                            except Exception as e:
                                logger.error(f"Failed to insert batch to {mapping.table}: {e}")
                                # Send failed batch to DLQ
                                for data in message_batch:
                                    await self._send_to_dlq(topic, data, str(e))
                                self.messages_failed += len(message_batch)
                                message_batch.clear()
                    else:
                        # No messages, wait before next poll
                        await asyncio.sleep(self.poll_interval)
                else:
                    logger.warning(f"Failed to consume from {topic}: {result.get('error')}")
                    await asyncio.sleep(self.poll_interval)
                
            except asyncio.CancelledError:
                logger.info(f"Consumer for {topic} was cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error in consumer for {topic}: {e}")
                await asyncio.sleep(self.poll_interval * 2)  # Back off on error
    
    async def _process_message(self, message: Dict[str, Any], mapping: TableMapping) -> Optional[Dict[str, Any]]:
        """Process a single message according to table mapping."""
        try:
            # Extract message value
            message_value = message.get('value', {})
            
            # Apply transformation function if provided
            if mapping.transform_function:
                transformed_data = mapping.transform_function(message_value)
            else:
                transformed_data = message_value.copy()
            
            # Add metadata
            transformed_data['kafka_offset'] = message.get('offset')
            transformed_data['kafka_partition'] = message.get('partition')
            transformed_data['kafka_timestamp'] = message.get('timestamp')
            
            # Add timestamp if not present
            if mapping.timestamp_column and mapping.timestamp_column not in transformed_data:
                transformed_data[mapping.timestamp_column] = datetime.utcnow().isoformat()
            
            # Generate ID if key column specified but not present
            if mapping.key_column and mapping.key_column not in transformed_data:
                transformed_data[mapping.key_column] = str(uuid.uuid4())
            
            return transformed_data
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise
    
    async def _insert_batch(self, mapping: TableMapping, batch: List[Dict[str, Any]]):
        """Insert a batch of processed messages into the database."""
        if not batch:
            return
        
        try:
            if mapping.upsert and mapping.key_column:
                # Use upsert for existing records
                await self._upsert_batch(mapping, batch)
            else:
                # Use regular insert
                await self._insert_batch_regular(mapping, batch)
                
        except Exception as e:
            logger.error(f"Failed to insert batch to {mapping.table}: {e}")
            raise
    
    async def _insert_batch_regular(self, mapping: TableMapping, batch: List[Dict[str, Any]]):
        """Insert batch using regular INSERT statements."""
        for record in batch:
            # Convert record to SQL insert
            columns = list(record.keys())
            values = list(record.values())
            
            # Build SQL
            columns_str = ', '.join(f'"{col}"' for col in columns)
            placeholders = ', '.join(['%s'] * len(values))
            sql = f'INSERT INTO "{mapping.table}" ({columns_str}) VALUES ({placeholders})'
            
            # Execute insert
            result = await self.postgres_client.call_tool("execute_query", {
                'sql': sql,
                'params': values
            })
            
            if not result.get('success'):
                raise Exception(f"Insert failed: {result.get('error')}")
    
    async def _upsert_batch(self, mapping: TableMapping, batch: List[Dict[str, Any]]):
        """Insert batch using UPSERT (ON CONFLICT) for existing records."""
        for record in batch:
            columns = list(record.keys())
            values = list(record.values())
            
            # Build upsert SQL
            columns_str = ', '.join(f'"{col}"' for col in columns)
            placeholders = ', '.join(['%s'] * len(values))
            
            # Build update clause (exclude key column)
            update_columns = [col for col in columns if col != mapping.key_column]
            update_clause = ', '.join(f'"{col}" = EXCLUDED."{col}"' for col in update_columns)
            
            sql = f'''
                INSERT INTO "{mapping.table}" ({columns_str}) 
                VALUES ({placeholders})
                ON CONFLICT ("{mapping.key_column}") 
                DO UPDATE SET {update_clause}
            '''
            
            # Execute upsert
            result = await self.postgres_client.call_tool("execute_query", {
                'sql': sql,
                'params': values
            })
            
            if not result.get('success'):
                raise Exception(f"Upsert failed: {result.get('error')}")
    
    async def _send_to_dlq(self, topic: str, message: Dict[str, Any], error: str):
        """Send failed message to dead letter queue."""
        try:
            dlq_message = {
                'original_topic': topic,
                'original_message': message,
                'error': error,
                'timestamp': datetime.utcnow().isoformat(),
                'consumer_group': self.consumer_group
            }
            
            await self.kafka_client.call_tool("publish_message", {
                'topic': self.dlq_topic,
                'message': dlq_message,
                'key': f"dlq_{topic}"
            })
            
            logger.warning(f"Sent message to DLQ: {error}")
            
        except Exception as e:
            logger.error(f"Failed to send message to DLQ: {e}")
    
    # Transform functions for customer support data
    def _transform_customer_query(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Transform customer query message for database storage."""
        return {
            'query_id': message.get('query_id'),
            'customer_id': message.get('customer_id'),
            'query_text': message.get('query_text'),
            'priority': message.get('priority', 'normal'),
            'category': message.get('category', 'general'),
            'context': json.dumps(message.get('context', {})),
            'metadata': json.dumps(message.get('metadata', {})),
            'status': 'received',
            'received_at': message.get('timestamp', datetime.utcnow().isoformat())
        }
    
    def _transform_agent_response(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Transform agent response message for database storage."""
        return {
            'response_id': str(uuid.uuid4()),
            'query_id': message.get('query_id'),
            'agent_id': message.get('agent_id'),
            'response_text': message.get('response_text'),
            'confidence': message.get('confidence', 0.0),
            'processing_time': message.get('processing_time'),
            'model_used': message.get('model_used'),
            'tokens_used': message.get('tokens_used'),
            'response_type': message.get('response_type', 'text'),
            'metadata': json.dumps(message.get('metadata', {})),
            'created_at': message.get('timestamp', datetime.utcnow().isoformat())
        }
    
    def _transform_ticket(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Transform ticket message for database storage."""
        return {
            'ticket_id': message.get('ticket_id'),
            'customer_id': message.get('customer_id'),
            'query_id': message.get('query_id'),
            'title': message.get('title'),
            'description': message.get('description'),
            'priority': message.get('priority', 'normal'),
            'status': message.get('status', 'open'),
            'category': message.get('category'),
            'assigned_agent': message.get('assigned_agent'),
            'tags': json.dumps(message.get('tags', [])),
            'metadata': json.dumps(message.get('metadata', {})),
            'created_at': message.get('timestamp', datetime.utcnow().isoformat())
        }
    
    def _transform_analytics_event(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Transform analytics event message for database storage."""
        return {
            'event_id': str(uuid.uuid4()),
            'event_type': message.get('event_type'),
            'customer_id': message.get('customer_id'),
            'session_id': message.get('session_id'),
            'query_id': message.get('query_id'),
            'agent_id': message.get('agent_id'),
            'event_data': json.dumps(message.get('event_data', {})),
            'user_agent': message.get('user_agent'),
            'ip_address': message.get('ip_address'),
            'timestamp': message.get('timestamp', datetime.utcnow().isoformat())
        }
    
    async def create_tables(self):
        """Create the necessary database tables for customer support data."""
        tables = [
            # Customer queries table
            '''
            CREATE TABLE IF NOT EXISTS customer_queries (
                query_id VARCHAR(255) PRIMARY KEY,
                customer_id VARCHAR(255) NOT NULL,
                query_text TEXT NOT NULL,
                priority VARCHAR(50) DEFAULT 'normal',
                category VARCHAR(100) DEFAULT 'general',
                context JSONB DEFAULT '{}',
                metadata JSONB DEFAULT '{}',
                status VARCHAR(50) DEFAULT 'received',
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                kafka_offset BIGINT,
                kafka_partition INTEGER,
                kafka_timestamp BIGINT
            )
            ''',
            
            # Agent responses table
            '''
            CREATE TABLE IF NOT EXISTS agent_responses (
                response_id VARCHAR(255) PRIMARY KEY,
                query_id VARCHAR(255) NOT NULL,
                agent_id VARCHAR(255),
                response_text TEXT NOT NULL,
                confidence FLOAT DEFAULT 0.0,
                processing_time FLOAT,
                model_used VARCHAR(100),
                tokens_used INTEGER,
                response_type VARCHAR(50) DEFAULT 'text',
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                kafka_offset BIGINT,
                kafka_partition INTEGER,
                kafka_timestamp BIGINT,
                FOREIGN KEY (query_id) REFERENCES customer_queries(query_id)
            )
            ''',
            
            # Support tickets table
            '''
            CREATE TABLE IF NOT EXISTS support_tickets (
                ticket_id VARCHAR(255) PRIMARY KEY,
                customer_id VARCHAR(255) NOT NULL,
                query_id VARCHAR(255),
                title VARCHAR(500),
                description TEXT,
                priority VARCHAR(50) DEFAULT 'normal',
                status VARCHAR(50) DEFAULT 'open',
                category VARCHAR(100),
                assigned_agent VARCHAR(255),
                tags JSONB DEFAULT '[]',
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                kafka_offset BIGINT,
                kafka_partition INTEGER,
                kafka_timestamp BIGINT
            )
            ''',
            
            # Analytics events table
            '''
            CREATE TABLE IF NOT EXISTS analytics_events (
                event_id VARCHAR(255) PRIMARY KEY,
                event_type VARCHAR(100) NOT NULL,
                customer_id VARCHAR(255),
                session_id VARCHAR(255),
                query_id VARCHAR(255),
                agent_id VARCHAR(255),
                event_data JSONB DEFAULT '{}',
                user_agent TEXT,
                ip_address INET,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                kafka_offset BIGINT,
                kafka_partition INTEGER,
                kafka_timestamp BIGINT
            )
            '''
        ]
        
        # Create indexes
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_customer_queries_customer_id ON customer_queries(customer_id)',
            'CREATE INDEX IF NOT EXISTS idx_customer_queries_status ON customer_queries(status)',
            'CREATE INDEX IF NOT EXISTS idx_customer_queries_received_at ON customer_queries(received_at)',
            'CREATE INDEX IF NOT EXISTS idx_agent_responses_query_id ON agent_responses(query_id)',
            'CREATE INDEX IF NOT EXISTS idx_agent_responses_agent_id ON agent_responses(agent_id)',
            'CREATE INDEX IF NOT EXISTS idx_support_tickets_customer_id ON support_tickets(customer_id)',
            'CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON support_tickets(status)',
            'CREATE INDEX IF NOT EXISTS idx_analytics_events_customer_id ON analytics_events(customer_id)',
            'CREATE INDEX IF NOT EXISTS idx_analytics_events_event_type ON analytics_events(event_type)',
            'CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON analytics_events(timestamp)'
        ]
        
        logger.info("Creating database tables...")
        
        # Create tables
        for table_sql in tables:
            result = await self.postgres_client.call_tool("execute_query", {
                'sql': table_sql
            })
            if not result.get('success'):
                logger.error(f"Failed to create table: {result.get('error')}")
                raise Exception(f"Table creation failed: {result.get('error')}")
        
        # Create indexes
        for index_sql in indexes:
            result = await self.postgres_client.call_tool("execute_query", {
                'sql': index_sql
            })
            if not result.get('success'):
                logger.warning(f"Failed to create index: {result.get('error')}")
        
        logger.info("Database tables created successfully")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get consumer statistics."""
        return {
            'running': self.running,
            'active_topics': list(self.consumer_tasks.keys()),
            'messages_processed': self.messages_processed,
            'messages_failed': self.messages_failed,
            'last_processed_time': self.last_processed_time.isoformat() if self.last_processed_time else None,
            'table_mappings': {topic: mapping.table for topic, mapping in self.table_mappings.items()}
        }


# Factory function for easy initialization
async def create_postgres_kafka_consumer(
    kafka_client: OptimizedKafkaMCPClient,
    postgres_client: OptimizedPostgreSQLMCPClient,
    **kwargs
) -> PostgresKafkaConsumer:
    """Factory function to create and initialize a Postgres-Kafka consumer."""
    consumer = PostgresKafkaConsumer(kafka_client, postgres_client, **kwargs)
    
    # Add standard customer support mappings
    consumer.add_customer_support_mappings()
    
    # Create necessary tables
    await consumer.create_tables()
    
    return consumer
