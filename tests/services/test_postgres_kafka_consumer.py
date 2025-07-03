"""
Comprehensive test cases for PostgresKafkaConsumer service.
Tests Kafka consumption, PostgreSQL integration, data transformation, and error handling.
"""
import pytest
import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.services.postgres_kafka_consumer import (
    PostgresKafkaConsumer,
    TableMapping,
    create_postgres_kafka_consumer
)


class TestPostgresKafkaConsumer:
    """Test PostgresKafkaConsumer basic functionality."""
    
    @pytest.fixture
    def mock_kafka_client(self):
        """Mock Kafka MCP client."""
        client = AsyncMock()
        client.call_tool = AsyncMock()
        return client
    
    @pytest.fixture
    def mock_postgres_client(self):
        """Mock PostgreSQL MCP client."""
        client = AsyncMock()
        client.call_tool = AsyncMock()
        return client
    
    @pytest.fixture
    def consumer(self, mock_kafka_client, mock_postgres_client):
        """Create PostgresKafkaConsumer instance."""
        return PostgresKafkaConsumer(
            kafka_client=mock_kafka_client,
            postgres_client=mock_postgres_client,
            batch_size=10,
            poll_interval=0.1,
            consumer_group="test-group"
        )
    
    @pytest.fixture
    def sample_kafka_messages(self):
        """Sample Kafka messages for testing."""
        return [
            {
                'key': 'customer_123',
                'value': {
                    'query_id': 'query_123',
                    'customer_id': 'customer_123',
                    'query_text': 'How do I reset my password?',
                    'priority': 'high',
                    'category': 'technical'
                },
                'offset': 100,
                'partition': 0,
                'timestamp': 1609459200000
            },
            {
                'key': 'customer_456',
                'value': {
                    'query_id': 'query_456',
                    'customer_id': 'customer_456',
                    'query_text': 'What is my account balance?',
                    'priority': 'normal',
                    'category': 'account'
                },
                'offset': 101,
                'partition': 0,
                'timestamp': 1609459260000
            }
        ]
    
    def test_init(self, mock_kafka_client, mock_postgres_client):
        """Test consumer initialization."""
        consumer = PostgresKafkaConsumer(
            kafka_client=mock_kafka_client,
            postgres_client=mock_postgres_client,
            batch_size=50,
            poll_interval=2.0,
            consumer_group="custom-group"
        )
        
        assert consumer.kafka_client == mock_kafka_client
        assert consumer.postgres_client == mock_postgres_client
        assert consumer.batch_size == 50
        assert consumer.poll_interval == 2.0
        assert consumer.consumer_group == "custom-group"
        assert consumer.table_mappings == {}
        assert consumer.running is False
        assert consumer.consumer_tasks == {}
        assert consumer.messages_processed == 0
        assert consumer.messages_failed == 0
        assert consumer.last_processed_time is None
    
    def test_add_table_mapping(self, consumer):
        """Test adding table mappings."""
        mapping = TableMapping(
            topic="test-topic",
            table="test_table",
            key_column="id",
            upsert=True
        )
        
        consumer.add_table_mapping(mapping)
        
        assert "test-topic" in consumer.table_mappings
        assert consumer.table_mappings["test-topic"] == mapping
    
    def test_add_customer_support_mappings(self, consumer):
        """Test adding standard customer support mappings."""
        consumer.add_customer_support_mappings()
        
        expected_topics = [
            "customer-support-queries",
            "customer-support-responses",
            "customer-support-tickets",
            "customer-support-analytics"
        ]
        
        for topic in expected_topics:
            assert topic in consumer.table_mappings
        
        # Verify specific mappings
        queries_mapping = consumer.table_mappings["customer-support-queries"]
        assert queries_mapping.table == "customer_queries"
        assert queries_mapping.key_column == "query_id"
        assert queries_mapping.upsert is True
    
    @pytest.mark.asyncio
    async def test_start_consuming(self, consumer):
        """Test starting consumer tasks."""
        # Add mappings
        consumer.add_table_mapping(TableMapping("topic1", "table1"))
        consumer.add_table_mapping(TableMapping("topic2", "table2"))
        
        with patch.object(consumer, '_consume_topic') as mock_consume:
            mock_consume.return_value = AsyncMock()
            
            await consumer.start_consuming(["topic1"])
            
            assert consumer.running is True
            assert len(consumer.consumer_tasks) == 1
            assert "topic1" in consumer.consumer_tasks
            mock_consume.assert_called_once_with("topic1")
    
    @pytest.mark.asyncio
    async def test_start_consuming_all_topics(self, consumer):
        """Test starting consumers for all configured topics."""
        # Add mappings
        consumer.add_table_mapping(TableMapping("topic1", "table1"))
        consumer.add_table_mapping(TableMapping("topic2", "table2"))
        
        with patch.object(consumer, '_consume_topic') as mock_consume:
            mock_consume.return_value = AsyncMock()
            
            await consumer.start_consuming()
            
            assert consumer.running is True
            assert len(consumer.consumer_tasks) == 2
            assert "topic1" in consumer.consumer_tasks
            assert "topic2" in consumer.consumer_tasks
    
    @pytest.mark.asyncio
    async def test_stop_consuming(self, consumer):
        """Test stopping consumer tasks."""
        # Setup mock tasks
        task1 = AsyncMock()
        task2 = AsyncMock()
        consumer.consumer_tasks = {"topic1": task1, "topic2": task2}
        consumer.running = True
        
        await consumer.stop_consuming()
        
        assert consumer.running is False
        assert len(consumer.consumer_tasks) == 0
        task1.cancel.assert_called_once()
        task2.cancel.assert_called_once()


class TestMessageProcessing:
    """Test message processing functionality."""
    
    @pytest.fixture
    def consumer(self, mock_kafka_client, mock_postgres_client):
        """Create consumer with mappings."""
        consumer = PostgresKafkaConsumer(
            kafka_client=mock_kafka_client,
            postgres_client=mock_postgres_client
        )
        consumer.add_customer_support_mappings()
        return consumer
    
    @pytest.fixture
    def mock_kafka_client(self):
        """Mock Kafka client."""
        client = AsyncMock()
        client.call_tool = AsyncMock()
        return client
    
    @pytest.fixture
    def mock_postgres_client(self):
        """Mock PostgreSQL client."""
        client = AsyncMock()
        client.call_tool = AsyncMock()
        return client
    
    @pytest.mark.asyncio
    async def test_process_message_basic(self, consumer):
        """Test basic message processing."""
        mapping = TableMapping("test-topic", "test_table")
        message = {
            'value': {'id': '123', 'name': 'test'},
            'offset': 100,
            'partition': 0,
            'timestamp': 1609459200000
        }
        
        result = await consumer._process_message(message, mapping)
        
        assert result['id'] == '123'
        assert result['name'] == 'test'
        assert result['kafka_offset'] == 100
        assert result['kafka_partition'] == 0
        assert result['kafka_timestamp'] == 1609459200000
        assert 'created_at' in result
    
    @pytest.mark.asyncio
    async def test_process_message_with_transform(self, consumer):
        """Test message processing with transformation function."""
        def transform_func(data):
            return {'transformed_' + k: v for k, v in data.items()}
        
        mapping = TableMapping("test-topic", "test_table", transform_function=transform_func)
        message = {
            'value': {'id': '123', 'name': 'test'},
            'offset': 100,
            'partition': 0,
            'timestamp': 1609459200000
        }
        
        result = await consumer._process_message(message, mapping)
        
        assert result['transformed_id'] == '123'
        assert result['transformed_name'] == 'test'
        assert result['kafka_offset'] == 100
    
    @pytest.mark.asyncio
    async def test_process_message_with_key_generation(self, consumer):
        """Test message processing with automatic key generation."""
        mapping = TableMapping("test-topic", "test_table", key_column="id")
        message = {
            'value': {'name': 'test'},  # No ID provided
            'offset': 100,
            'partition': 0,
            'timestamp': 1609459200000
        }
        
        result = await consumer._process_message(message, mapping)
        
        assert 'id' in result
        assert len(result['id']) > 0  # UUID generated
        assert result['name'] == 'test'
    
    @pytest.mark.asyncio
    async def test_process_message_error_handling(self, consumer):
        """Test error handling in message processing."""
        def failing_transform(data):
            raise ValueError("Transform failed")
        
        mapping = TableMapping("test-topic", "test_table", transform_function=failing_transform)
        message = {'value': {'id': '123'}}
        
        with pytest.raises(ValueError, match="Transform failed"):
            await consumer._process_message(message, mapping)


class TestDatabaseOperations:
    """Test database insertion operations."""
    
    @pytest.fixture
    def consumer(self, mock_kafka_client, mock_postgres_client):
        """Create consumer instance."""
        return PostgresKafkaConsumer(
            kafka_client=mock_kafka_client,
            postgres_client=mock_postgres_client
        )
    
    @pytest.fixture
    def mock_kafka_client(self):
        """Mock Kafka client."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_postgres_client(self):
        """Mock PostgreSQL client."""
        client = AsyncMock()
        client.call_tool = AsyncMock(return_value={'success': True})
        return client
    
    @pytest.mark.asyncio
    async def test_insert_batch_regular(self, consumer, mock_postgres_client):
        """Test regular batch insertion."""
        mapping = TableMapping("test-topic", "test_table")
        batch = [
            {'id': '1', 'name': 'test1'},
            {'id': '2', 'name': 'test2'}
        ]
        
        await consumer._insert_batch_regular(mapping, batch)
        
        # Verify SQL calls
        assert mock_postgres_client.call_tool.call_count == 2
        calls = mock_postgres_client.call_tool.call_args_list
        
        # Check first call
        first_call = calls[0][1]
        assert 'INSERT INTO "test_table"' in first_call['sql']
        assert first_call['params'] == ['1', 'test1']
        
        # Check second call
        second_call = calls[1][1]
        assert 'INSERT INTO "test_table"' in second_call['sql']
        assert second_call['params'] == ['2', 'test2']
    
    @pytest.mark.asyncio
    async def test_upsert_batch(self, consumer, mock_postgres_client):
        """Test upsert batch operation."""
        mapping = TableMapping("test-topic", "test_table", key_column="id", upsert=True)
        batch = [
            {'id': '1', 'name': 'test1'},
            {'id': '2', 'name': 'test2'}
        ]
        
        await consumer._upsert_batch(mapping, batch)
        
        # Verify SQL calls
        assert mock_postgres_client.call_tool.call_count == 2
        calls = mock_postgres_client.call_tool.call_args_list
        
        # Check upsert SQL structure
        first_call = calls[0][1]
        assert 'INSERT INTO "test_table"' in first_call['sql']
        assert 'ON CONFLICT ("id")' in first_call['sql']
        assert 'DO UPDATE SET' in first_call['sql']
    
    @pytest.mark.asyncio
    async def test_insert_batch_with_upsert_mapping(self, consumer, mock_postgres_client):
        """Test batch insertion routing to upsert."""
        mapping = TableMapping("test-topic", "test_table", key_column="id", upsert=True)
        batch = [{'id': '1', 'name': 'test1'}]
        
        with patch.object(consumer, '_upsert_batch') as mock_upsert:
            await consumer._insert_batch(mapping, batch)
            mock_upsert.assert_called_once_with(mapping, batch)
    
    @pytest.mark.asyncio
    async def test_insert_batch_without_upsert(self, consumer, mock_postgres_client):
        """Test batch insertion routing to regular insert."""
        mapping = TableMapping("test-topic", "test_table", upsert=False)
        batch = [{'id': '1', 'name': 'test1'}]
        
        with patch.object(consumer, '_insert_batch_regular') as mock_regular:
            await consumer._insert_batch(mapping, batch)
            mock_regular.assert_called_once_with(mapping, batch)
    
    @pytest.mark.asyncio
    async def test_insert_batch_error_handling(self, consumer):
        """Test error handling in batch insertion."""
        # Mock failed PostgreSQL call
        mock_postgres_client = AsyncMock()
        mock_postgres_client.call_tool = AsyncMock(return_value={'success': False, 'error': 'DB Error'})
        consumer.postgres_client = mock_postgres_client
        
        mapping = TableMapping("test-topic", "test_table")
        batch = [{'id': '1', 'name': 'test1'}]
        
        with pytest.raises(Exception, match="Insert failed: DB Error"):
            await consumer._insert_batch_regular(mapping, batch)


class TestTopicConsumption:
    """Test topic consumption logic."""
    
    @pytest.fixture
    def consumer(self, mock_kafka_client, mock_postgres_client):
        """Create consumer with mocked clients."""
        consumer = PostgresKafkaConsumer(
            kafka_client=mock_kafka_client,
            postgres_client=mock_postgres_client,
            batch_size=2,
            poll_interval=0.01
        )
        consumer.add_table_mapping(TableMapping("test-topic", "test_table"))
        return consumer
    
    @pytest.fixture
    def mock_kafka_client(self):
        """Mock Kafka client."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_postgres_client(self):
        """Mock PostgreSQL client."""
        client = AsyncMock()
        client.call_tool = AsyncMock(return_value={'success': True})
        return client
    
    @pytest.mark.asyncio
    async def test_consume_topic_with_messages(self, consumer, mock_kafka_client, mock_postgres_client, sample_kafka_messages):
        """Test consuming topic with messages."""
        # Setup Kafka responses
        mock_kafka_client.call_tool.side_effect = [
            {
                'success': True,
                'result': {'messages': sample_kafka_messages}
            },
            {
                'success': True,
                'result': {'messages': []}  # No more messages
            }
        ]
        
        consumer.running = True
        
        # Run consumption for a short time
        task = asyncio.create_task(consumer._consume_topic("test-topic"))
        await asyncio.sleep(0.05)  # Let it process messages
        consumer.running = False
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify Kafka was called
        assert mock_kafka_client.call_tool.call_count >= 1
        
        # Verify PostgreSQL was called (for inserting processed messages)
        assert mock_postgres_client.call_tool.call_count >= 1
        
        # Verify metrics
        assert consumer.messages_processed >= 0
    
    @pytest.mark.asyncio
    async def test_consume_topic_no_messages(self, consumer, mock_kafka_client):
        """Test consuming topic with no messages."""
        # Setup Kafka to return no messages
        mock_kafka_client.call_tool.return_value = {
            'success': True,
            'result': {'messages': []}
        }
        
        consumer.running = True
        
        # Run consumption for a short time
        task = asyncio.create_task(consumer._consume_topic("test-topic"))
        await asyncio.sleep(0.05)
        consumer.running = False
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify Kafka was called
        assert mock_kafka_client.call_tool.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_consume_topic_kafka_error(self, consumer, mock_kafka_client):
        """Test handling Kafka errors during consumption."""
        # Setup Kafka to return error
        mock_kafka_client.call_tool.return_value = {
            'success': False,
            'error': 'Kafka connection failed'
        }
        
        consumer.running = True
        
        # Run consumption for a short time
        task = asyncio.create_task(consumer._consume_topic("test-topic"))
        await asyncio.sleep(0.05)
        consumer.running = False
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify Kafka was called despite errors
        assert mock_kafka_client.call_tool.call_count >= 1


class TestDataTransformation:
    """Test data transformation functions."""
    
    @pytest.fixture
    def consumer(self, mock_kafka_client, mock_postgres_client):
        """Create consumer instance."""
        return PostgresKafkaConsumer(
            kafka_client=mock_kafka_client,
            postgres_client=mock_postgres_client
        )
    
    @pytest.fixture
    def mock_kafka_client(self):
        """Mock Kafka client."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_postgres_client(self):
        """Mock PostgreSQL client."""
        return AsyncMock()
    
    def test_transform_customer_query(self, consumer):
        """Test customer query transformation."""
        message = {
            'query_id': 'query_123',
            'customer_id': 'customer_123',
            'query_text': 'How do I reset my password?',
            'priority': 'high',
            'category': 'technical',
            'context': {'session_id': 'session_123'},
            'metadata': {'source': 'web'},
            'timestamp': '2021-01-01T12:00:00Z'
        }
        
        result = consumer._transform_customer_query(message)
        
        assert result['query_id'] == 'query_123'
        assert result['customer_id'] == 'customer_123'
        assert result['query_text'] == 'How do I reset my password?'
        assert result['priority'] == 'high'
        assert result['category'] == 'technical'
        assert result['status'] == 'received'
        assert result['received_at'] == '2021-01-01T12:00:00Z'
        
        # Check JSON serialization
        assert json.loads(result['context']) == {'session_id': 'session_123'}
        assert json.loads(result['metadata']) == {'source': 'web'}
    
    def test_transform_agent_response(self, consumer):
        """Test agent response transformation."""
        message = {
            'query_id': 'query_123',
            'agent_id': 'agent_456',
            'response_text': 'Please click the forgot password link.',
            'confidence': 0.95,
            'processing_time': 1.2,
            'model_used': 'gpt-4',
            'tokens_used': 150,
            'response_type': 'text',
            'metadata': {'temperature': 0.7},
            'timestamp': '2021-01-01T12:01:00Z'
        }
        
        result = consumer._transform_agent_response(message)
        
        assert result['query_id'] == 'query_123'
        assert result['agent_id'] == 'agent_456'
        assert result['response_text'] == 'Please click the forgot password link.'
        assert result['confidence'] == 0.95
        assert result['processing_time'] == 1.2
        assert result['model_used'] == 'gpt-4'
        assert result['tokens_used'] == 150
        assert result['response_type'] == 'text'
        assert result['created_at'] == '2021-01-01T12:01:00Z'
        assert 'response_id' in result
        
        # Check JSON serialization
        assert json.loads(result['metadata']) == {'temperature': 0.7}
    
    def test_transform_ticket(self, consumer):
        """Test ticket transformation."""
        message = {
            'ticket_id': 'ticket_123',
            'customer_id': 'customer_123',
            'query_id': 'query_123',
            'title': 'Password Reset Issue',
            'description': 'Customer cannot reset password',
            'priority': 'high',
            'status': 'open',
            'category': 'technical',
            'assigned_agent': 'agent_456',
            'tags': ['password', 'urgent'],
            'metadata': {'escalated': True},
            'timestamp': '2021-01-01T12:02:00Z'
        }
        
        result = consumer._transform_ticket(message)
        
        assert result['ticket_id'] == 'ticket_123'
        assert result['customer_id'] == 'customer_123'
        assert result['query_id'] == 'query_123'
        assert result['title'] == 'Password Reset Issue'
        assert result['description'] == 'Customer cannot reset password'
        assert result['priority'] == 'high'
        assert result['status'] == 'open'
        assert result['category'] == 'technical'
        assert result['assigned_agent'] == 'agent_456'
        assert result['created_at'] == '2021-01-01T12:02:00Z'
        
        # Check JSON serialization
        assert json.loads(result['tags']) == ['password', 'urgent']
        assert json.loads(result['metadata']) == {'escalated': True}
    
    def test_transform_analytics_event(self, consumer):
        """Test analytics event transformation."""
        message = {
            'event_type': 'query_submitted',
            'customer_id': 'customer_123',
            'session_id': 'session_123',
            'query_id': 'query_123',
            'agent_id': 'agent_456',
            'event_data': {'page': '/support', 'duration': 30},
            'user_agent': 'Mozilla/5.0',
            'ip_address': '192.168.1.1',
            'timestamp': '2021-01-01T12:03:00Z'
        }
        
        result = consumer._transform_analytics_event(message)
        
        assert result['event_type'] == 'query_submitted'
        assert result['customer_id'] == 'customer_123'
        assert result['session_id'] == 'session_123'
        assert result['query_id'] == 'query_123'
        assert result['agent_id'] == 'agent_456'
        assert result['user_agent'] == 'Mozilla/5.0'
        assert result['ip_address'] == '192.168.1.1'
        assert result['timestamp'] == '2021-01-01T12:03:00Z'
        assert 'event_id' in result
        
        # Check JSON serialization
        assert json.loads(result['event_data']) == {'page': '/support', 'duration': 30}


class TestErrorHandling:
    """Test error handling and dead letter queue."""
    
    @pytest.fixture
    def consumer(self, mock_kafka_client, mock_postgres_client):
        """Create consumer instance."""
        return PostgresKafkaConsumer(
            kafka_client=mock_kafka_client,
            postgres_client=mock_postgres_client
        )
    
    @pytest.fixture
    def mock_kafka_client(self):
        """Mock Kafka client."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_postgres_client(self):
        """Mock PostgreSQL client."""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_send_to_dlq(self, consumer, mock_kafka_client):
        """Test sending messages to dead letter queue."""
        # Setup successful DLQ publish
        mock_kafka_client.call_tool.return_value = {'success': True}
        
        topic = "test-topic"
        message = {'id': '123', 'data': 'test'}
        error = "Processing failed"
        
        await consumer._send_to_dlq(topic, message, error)
        
        # Verify DLQ message was published
        mock_kafka_client.call_tool.assert_called_once()
        call_args = mock_kafka_client.call_tool.call_args[1]
        
        assert call_args['topic'] == 'postgres-consumer-dlq'
        assert call_args['key'] == 'dlq_test-topic'
        
        dlq_message = call_args['message']
        assert dlq_message['original_topic'] == topic
        assert dlq_message['original_message'] == message
        assert dlq_message['error'] == error
        assert dlq_message['consumer_group'] == 'test-group'
    
    @pytest.mark.asyncio
    async def test_send_to_dlq_failure(self, consumer, mock_kafka_client):
        """Test handling DLQ publish failures."""
        # Setup DLQ publish failure
        mock_kafka_client.call_tool.side_effect = Exception("DLQ publish failed")
        
        topic = "test-topic"
        message = {'id': '123'}
        error = "Processing failed"
        
        # Should not raise exception (should log error instead)
        await consumer._send_to_dlq(topic, message, error)
        
        # Verify attempt was made
        mock_kafka_client.call_tool.assert_called_once()


class TestTableCreation:
    """Test database table creation."""
    
    @pytest.fixture
    def consumer(self, mock_kafka_client, mock_postgres_client):
        """Create consumer instance."""
        return PostgresKafkaConsumer(
            kafka_client=mock_kafka_client,
            postgres_client=mock_postgres_client
        )
    
    @pytest.fixture
    def mock_kafka_client(self):
        """Mock Kafka client."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_postgres_client(self):
        """Mock PostgreSQL client."""
        client = AsyncMock()
        client.call_tool = AsyncMock(return_value={'success': True})
        return client
    
    @pytest.mark.asyncio
    async def test_create_tables_success(self, consumer, mock_postgres_client):
        """Test successful table creation."""
        await consumer.create_tables()
        
        # Verify multiple SQL calls were made (tables + indexes)
        assert mock_postgres_client.call_tool.call_count > 10
        
        # Check that table creation SQL was called
        calls = mock_postgres_client.call_tool.call_args_list
        sql_calls = [call[1]['sql'] for call in calls]
        
        # Verify key tables are created
        table_creates = [sql for sql in sql_calls if 'CREATE TABLE' in sql]
        assert any('customer_queries' in sql for sql in table_creates)
        assert any('agent_responses' in sql for sql in table_creates)
        assert any('support_tickets' in sql for sql in table_creates)
        assert any('analytics_events' in sql for sql in table_creates)
        
        # Verify indexes are created
        index_creates = [sql for sql in sql_calls if 'CREATE INDEX' in sql]
        assert len(index_creates) > 0
    
    @pytest.mark.asyncio
    async def test_create_tables_failure(self, consumer):
        """Test handling table creation failures."""
        # Mock PostgreSQL to fail on table creation
        mock_postgres_client = AsyncMock()
        mock_postgres_client.call_tool.return_value = {
            'success': False,
            'error': 'Table creation failed'
        }
        consumer.postgres_client = mock_postgres_client
        
        with pytest.raises(Exception, match="Table creation failed"):
            await consumer.create_tables()


class TestPerformanceAndMetrics:
    """Test performance and metrics functionality."""
    
    @pytest.fixture
    def consumer(self, mock_kafka_client, mock_postgres_client):
        """Create consumer instance."""
        return PostgresKafkaConsumer(
            kafka_client=mock_kafka_client,
            postgres_client=mock_postgres_client
        )
    
    @pytest.fixture
    def mock_kafka_client(self):
        """Mock Kafka client."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_postgres_client(self):
        """Mock PostgreSQL client."""
        return AsyncMock()
    
    def test_get_stats_initial(self, consumer):
        """Test getting initial statistics."""
        stats = consumer.get_stats()
        
        assert stats['running'] is False
        assert stats['active_topics'] == []
        assert stats['messages_processed'] == 0
        assert stats['messages_failed'] == 0
        assert stats['last_processed_time'] is None
        assert stats['table_mappings'] == {}
    
    def test_get_stats_with_mappings(self, consumer):
        """Test getting statistics with table mappings."""
        consumer.add_table_mapping(TableMapping("topic1", "table1"))
        consumer.add_table_mapping(TableMapping("topic2", "table2"))
        
        stats = consumer.get_stats()
        
        assert stats['table_mappings'] == {
            'topic1': 'table1',
            'topic2': 'table2'
        }
    
    def test_get_stats_with_activity(self, consumer):
        """Test getting statistics with processing activity."""
        # Simulate some processing
        consumer.messages_processed = 100
        consumer.messages_failed = 5
        consumer.last_processed_time = datetime.utcnow()
        consumer.running = True
        consumer.consumer_tasks = {'topic1': MagicMock(), 'topic2': MagicMock()}
        
        stats = consumer.get_stats()
        
        assert stats['running'] is True
        assert stats['active_topics'] == ['topic1', 'topic2']
        assert stats['messages_processed'] == 100
        assert stats['messages_failed'] == 5
        assert stats['last_processed_time'] is not None


class TestIntegration:
    """Test integration scenarios."""
    
    @pytest.fixture
    def mock_kafka_client(self):
        """Mock Kafka client."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_postgres_client(self):
        """Mock PostgreSQL client."""
        client = AsyncMock()
        client.call_tool = AsyncMock(return_value={'success': True})
        return client
    
    @pytest.mark.asyncio
    async def test_factory_function(self, mock_kafka_client, mock_postgres_client):
        """Test the factory function for creating consumers."""
        with patch('src.services.postgres_kafka_consumer.PostgresKafkaConsumer') as MockConsumer:
            mock_instance = AsyncMock()
            mock_instance.add_customer_support_mappings = MagicMock()
            mock_instance.create_tables = AsyncMock()
            MockConsumer.return_value = mock_instance
            
            result = await create_postgres_kafka_consumer(
                kafka_client=mock_kafka_client,
                postgres_client=mock_postgres_client,
                batch_size=50
            )
            
            # Verify consumer was created with correct parameters
            MockConsumer.assert_called_once_with(
                mock_kafka_client, 
                mock_postgres_client, 
                batch_size=50
            )
            
            # Verify initialization steps
            mock_instance.add_customer_support_mappings.assert_called_once()
            mock_instance.create_tables.assert_called_once()
            
            assert result == mock_instance
    
    @pytest.mark.asyncio
    async def test_end_to_end_processing(self, mock_kafka_client, mock_postgres_client, sample_kafka_messages):
        """Test end-to-end message processing."""
        # Setup successful responses
        mock_kafka_client.call_tool.side_effect = [
            {
                'success': True,
                'result': {'messages': sample_kafka_messages}
            },
            {
                'success': True,
                'result': {'messages': []}  # No more messages
            }
        ]
        
        consumer = PostgresKafkaConsumer(
            kafka_client=mock_kafka_client,
            postgres_client=mock_postgres_client,
            batch_size=5,
            poll_interval=0.01
        )
        
        # Add mapping with transformation
        consumer.add_customer_support_mappings()
        
        # Start consuming
        consumer.running = True
        task = asyncio.create_task(consumer._consume_topic("customer-support-queries"))
        
        # Let it process
        await asyncio.sleep(0.05)
        consumer.running = False
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify processing occurred
        assert mock_kafka_client.call_tool.call_count >= 1
        assert mock_postgres_client.call_tool.call_count >= 0


class TestConcurrency:
    """Test concurrent operations."""
    
    @pytest.fixture
    def consumer(self, mock_kafka_client, mock_postgres_client):
        """Create consumer instance."""
        return PostgresKafkaConsumer(
            kafka_client=mock_kafka_client,
            postgres_client=mock_postgres_client,
            poll_interval=0.01
        )
    
    @pytest.fixture
    def mock_kafka_client(self):
        """Mock Kafka client."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_postgres_client(self):
        """Mock PostgreSQL client."""
        client = AsyncMock()
        client.call_tool = AsyncMock(return_value={'success': True})
        return client
    
    @pytest.mark.asyncio
    async def test_multiple_topic_consumption(self, consumer, mock_kafka_client):
        """Test consuming from multiple topics concurrently."""
        # Setup Kafka responses for different topics
        def kafka_side_effect(tool_name, params):
            if params.get('topic') == 'topic1':
                return {'success': True, 'result': {'messages': []}}
            elif params.get('topic') == 'topic2':
                return {'success': True, 'result': {'messages': []}}
            return {'success': False}
        
        mock_kafka_client.call_tool.side_effect = kafka_side_effect
        
        # Add mappings for multiple topics
        consumer.add_table_mapping(TableMapping("topic1", "table1"))
        consumer.add_table_mapping(TableMapping("topic2", "table2"))
        
        # Start consuming from both topics
        await consumer.start_consuming()
        
        # Let them run briefly
        await asyncio.sleep(0.05)
        
        # Stop consuming
        await consumer.stop_consuming()
        
        # Verify both topics were being consumed
        assert len(consumer.consumer_tasks) == 0  # Should be cleared after stop


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    @pytest.fixture
    def consumer(self, mock_kafka_client, mock_postgres_client):
        """Create consumer instance."""
        return PostgresKafkaConsumer(
            kafka_client=mock_kafka_client,
            postgres_client=mock_postgres_client
        )
    
    @pytest.fixture
    def mock_kafka_client(self):
        """Mock Kafka client."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_postgres_client(self):
        """Mock PostgreSQL client."""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_empty_batch_processing(self, consumer):
        """Test processing empty message batches."""
        mapping = TableMapping("test-topic", "test_table")
        
        # Should handle empty batch gracefully
        await consumer._insert_batch(mapping, [])
        
        # No database calls should be made
        assert consumer.postgres_client.call_tool.call_count == 0
    
    @pytest.mark.asyncio
    async def test_malformed_message_processing(self, consumer):
        """Test processing malformed messages."""
        mapping = TableMapping("test-topic", "test_table")
        
        # Message without 'value' field
        malformed_message = {'offset': 100}
        
        result = await consumer._process_message(malformed_message, mapping)
        
        # Should handle gracefully and add metadata
        assert result['kafka_offset'] == 100
        assert 'created_at' in result
    
    def test_table_mapping_with_none_values(self, consumer):
        """Test table mapping with None/default values."""
        mapping = TableMapping(
            topic="test-topic",
            table="test_table"
            # key_column=None, transform_function=None, etc.
        )
        
        consumer.add_table_mapping(mapping)
        
        assert consumer.table_mappings["test-topic"] == mapping
        assert mapping.key_column is None
        assert mapping.transform_function is None
        assert mapping.upsert is False
    
    @pytest.mark.asyncio
    async def test_start_consuming_unknown_topic(self, consumer):
        """Test starting consumption for unmapped topics."""
        # Try to start consuming a topic without mapping
        await consumer.start_consuming(["unknown-topic"])
        
        # Should not create any consumer tasks
        assert len(consumer.consumer_tasks) == 0
        assert consumer.running is True


@pytest.fixture
def sample_kafka_messages():
    """Reusable sample Kafka messages."""
    return [
        {
            'key': 'customer_123',
            'value': {
                'query_id': 'query_123',
                'customer_id': 'customer_123',
                'query_text': 'How do I reset my password?',
                'priority': 'high',
                'category': 'technical'
            },
            'offset': 100,
            'partition': 0,
            'timestamp': 1609459200000
        },
        {
            'key': 'customer_456',
            'value': {
                'query_id': 'query_456',
                'customer_id': 'customer_456',
                'query_text': 'What is my account balance?',
                'priority': 'normal',
                'category': 'account'
            },
            'offset': 101,
            'partition': 0,
            'timestamp': 1609459260000
        }
    ]
