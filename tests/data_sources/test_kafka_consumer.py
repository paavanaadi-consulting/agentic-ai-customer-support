"""
Comprehensive tests for KafkaConsumer data source component.
"""
import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from src.data_sources.kafka_consumer import KafkaConsumer


class TestKafkaConsumer:
    """Test KafkaConsumer functionality."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for Kafka consumer."""
        return {
            'bootstrap_servers': ['localhost:9092'],
            'topics': ['customer_queries', 'agent_responses'],
            'group_id': 'test_support_group',
            'auto_offset_reset': 'latest'
        }

    @pytest.fixture
    def kafka_consumer(self, mock_config):
        """Create KafkaConsumer instance with mock config."""
        return KafkaConsumer(mock_config)

    def test_kafka_consumer_initialization(self, kafka_consumer, mock_config):
        """Test KafkaConsumer initialization."""
        assert kafka_consumer.config == mock_config
        assert kafka_consumer.consumer is None  # Before start
        assert kafka_consumer.producer is None  # Before start
        assert kafka_consumer.running is False
        assert isinstance(kafka_consumer.message_handlers, dict)
        assert kafka_consumer.status == "disconnected"

    @pytest.mark.asyncio
    async def test_start_success(self, kafka_consumer):
        """Test successful Kafka consumer start."""
        with patch('src.data_sources.kafka_consumer.KafkaConsumer') as mock_kafka_consumer:
            with patch('src.data_sources.kafka_consumer.KafkaProducer') as mock_kafka_producer:
                
                await kafka_consumer.start()
                
                assert kafka_consumer.running is True
                assert kafka_consumer.status == "connected"
                mock_kafka_consumer.assert_called_once()
                mock_kafka_producer.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_failure(self, kafka_consumer):
        """Test Kafka consumer start failure."""
        with patch('src.data_sources.kafka_consumer.KafkaConsumer', side_effect=Exception("Connection failed")):
            
            await kafka_consumer.start()
            
            assert kafka_consumer.running is False
            assert kafka_consumer.status == "disconnected"

    @pytest.mark.asyncio
    async def test_stop(self, kafka_consumer):
        """Test stopping Kafka consumer."""
        # Mock running state
        kafka_consumer.running = True
        kafka_consumer.consumer = Mock()
        kafka_consumer.producer = Mock()
        
        await kafka_consumer.stop()
        
        assert kafka_consumer.running is False
        assert kafka_consumer.status == "disconnected"
        kafka_consumer.consumer.close.assert_called_once()
        kafka_consumer.producer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message(self, kafka_consumer):
        """Test sending message through Kafka producer."""
        # Mock producer
        kafka_consumer.producer = Mock()
        kafka_consumer.running = True
        
        message_data = {"query": "How do I reset my password?", "customer_id": "cust123"}
        
        result = await kafka_consumer.send_message("customer_queries", message_data)
        
        assert result is True
        kafka_consumer.producer.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_not_running(self, kafka_consumer):
        """Test sending message when consumer is not running."""
        result = await kafka_consumer.send_message("test_topic", {"data": "test"})
        
        assert result is False

    def test_register_message_handler(self, kafka_consumer):
        """Test registering message handler."""
        async def test_handler(message):
            return {"processed": True}
        
        kafka_consumer.register_handler("customer_query", test_handler)
        
        assert "customer_query" in kafka_consumer.message_handlers
        assert kafka_consumer.message_handlers["customer_query"] == test_handler

    @pytest.mark.asyncio
    async def test_process_message_with_handler(self, kafka_consumer):
        """Test processing message with registered handler."""
        # Register a mock handler
        mock_handler = AsyncMock(return_value={"processed": True})
        kafka_consumer.register_handler("test_type", mock_handler)
        
        # Mock message
        mock_message = Mock()
        mock_message.value = b'{"type": "test_type", "data": "test_data"}'
        
        await kafka_consumer._process_message(mock_message)
        
        mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_no_handler(self, kafka_consumer):
        """Test processing message without registered handler."""
        # Mock message with unknown type
        mock_message = Mock()
        mock_message.value = b'{"type": "unknown_type", "data": "test_data"}'
        
        # Should not raise exception
        await kafka_consumer._process_message(mock_message)

    @pytest.mark.asyncio
    async def test_get_topic_metadata(self, kafka_consumer):
        """Test getting topic metadata."""
        # Mock consumer with metadata
        kafka_consumer.consumer = Mock()
        mock_metadata = Mock()
        mock_metadata.topics = {"test_topic": Mock()}
        kafka_consumer.consumer.list_consumer_groups.return_value = mock_metadata
        
        metadata = await kafka_consumer.get_topic_metadata("test_topic")
        
        assert isinstance(metadata, dict)

    @pytest.mark.asyncio
    async def test_get_consumer_lag(self, kafka_consumer):
        """Test getting consumer lag information."""
        kafka_consumer.consumer = Mock()
        kafka_consumer.running = True
        
        # Mock lag calculation
        with patch.object(kafka_consumer, '_calculate_lag', return_value={"lag": 10}):
            lag_info = await kafka_consumer.get_consumer_lag()
            
            assert "lag" in lag_info

    def test_health_check(self, kafka_consumer):
        """Test health check functionality."""
        kafka_consumer.running = True
        kafka_consumer.status = "connected"
        
        health = kafka_consumer.health_check()
        
        assert health["status"] == "healthy"
        assert health["running"] is True
        assert health["connection_status"] == "connected"


@pytest.mark.integration
class TestKafkaConsumerIntegration:
    """Integration tests for KafkaConsumer."""

    @pytest.mark.asyncio
    async def test_message_flow_simulation(self):
        """Test simulated message flow with mocked Kafka."""
        config = {
            'bootstrap_servers': ['localhost:9092'],
            'topics': ['test_topic'],
            'group_id': 'test_group'
        }
        
        consumer = KafkaConsumer(config)
        
        # Track processed messages
        processed_messages = []
        
        async def test_handler(message_data):
            processed_messages.append(message_data)
            return {"status": "processed"}
        
        consumer.register_handler("test_message", test_handler)
        
        with patch('src.data_sources.kafka_consumer.KafkaConsumer'):
            with patch('src.data_sources.kafka_consumer.KafkaProducer'):
                
                await consumer.start()
                assert consumer.running is True
                
                # Simulate message processing
                mock_message = Mock()
                mock_message.value = b'{"type": "test_message", "content": "Hello World"}'
                
                await consumer._process_message(mock_message)
                
                # Check handler was called
                assert len(processed_messages) == 1
                
                await consumer.stop()


@pytest.mark.performance
class TestKafkaConsumerPerformance:
    """Performance tests for KafkaConsumer."""

    @pytest.mark.asyncio
    async def test_message_processing_performance(self):
        """Test message processing performance."""
        import time
        
        config = {'bootstrap_servers': ['localhost:9092'], 'topics': ['perf_test']}
        consumer = KafkaConsumer(config)
        
        # Simple handler for performance testing
        processed_count = 0
        
        async def perf_handler(message_data):
            nonlocal processed_count
            processed_count += 1
            return {"processed": True}
        
        consumer.register_handler("perf_test", perf_handler)
        
        # Simulate processing multiple messages
        start_time = time.time()
        
        for i in range(100):
            mock_message = Mock()
            mock_message.value = f'{{"type": "perf_test", "id": {i}}}'.encode()
            await consumer._process_message(mock_message)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert processed_count == 100
        assert processing_time < 5.0  # Should process 100 messages quickly
        
        messages_per_second = 100 / processing_time
        assert messages_per_second > 20  # Reasonable throughput
