"""
Comprehensive test suite for Kafka MCP Client.
Tests optimized Kafka operations via MCP with multiple fallback strategies.
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from src.mcp.kafka_mcp_client import OptimizedKafkaMCPClient, KafkaClientError
from src.mcp.mcp_client_interface import MCPClientInterface


class TestOptimizedKafkaMCPClient:
    """Test cases for OptimizedKafkaMCPClient class."""

    @pytest.fixture
    def kafka_client(self):
        """Create a Kafka MCP client instance for testing."""
        return OptimizedKafkaMCPClient(
            bootstrap_servers="localhost:9092",
            mcp_server_url="http://localhost:8002",
            use_direct_connection=True,
            topic_prefix="customer-support",
            group_id="test-group"
        )

    @pytest.fixture
    def kafka_client_http_only(self):
        """Create a Kafka MCP client instance configured for HTTP only."""
        return OptimizedKafkaMCPClient(
            bootstrap_servers="localhost:9092",
            mcp_server_url="http://localhost:8002",
            use_direct_connection=False
        )

    @pytest.fixture
    def mock_http_session(self):
        """Create a mock HTTP session for testing."""
        session = AsyncMock()
        session.post.return_value.__aenter__.return_value.json.return_value = {"result": "success"}
        session.post.return_value.__aenter__.return_value.status = 200
        return session

    @pytest.fixture
    def mock_kafka_producer(self):
        """Create a mock Kafka producer for testing."""
        producer = Mock()
        producer.send.return_value.get.return_value = Mock(topic="test-topic", partition=0, offset=123)
        return producer

    def test_kafka_client_initialization(self, kafka_client):
        """Test Kafka MCP client initialization."""
        assert kafka_client.bootstrap_servers == "localhost:9092"
        assert kafka_client.mcp_server_url == "http://localhost:8002"
        assert kafka_client.use_direct_connection is True
        assert kafka_client.topic_prefix == "customer-support"
        assert kafka_client.group_id == "test-group"
        assert kafka_client.connected is False
        assert kafka_client.kafka_producer is None
        assert kafka_client.http_session is None
        assert kafka_client.cache_duration == 60
        assert isinstance(kafka_client.active_consumers, dict)
        assert isinstance(kafka_client.message_handlers, dict)

    def test_kafka_client_implements_interface(self, kafka_client):
        """Test that Kafka client implements MCPClientInterface."""
        assert isinstance(kafka_client, MCPClientInterface)

    @pytest.mark.asyncio
    async def test_connect_confluent_mcp_success(self, kafka_client):
        """Test successful connection via Confluent MCP server."""
        with patch('src.mcp.kafka_mcp_client.CONFLUENT_MCP_AVAILABLE', True):
            with patch('confluent_mcp.KafkaMCPServer') as MockServer:
                mock_server = AsyncMock()
                MockServer.return_value = mock_server
                
                result = await kafka_client.connect()
                
                assert result is True
                assert kafka_client.connected is True
                assert kafka_client.confluent_server == mock_server

    @pytest.mark.asyncio
    async def test_connect_kafka_python_fallback(self, kafka_client):
        """Test fallback to kafka-python when Confluent MCP is not available."""
        with patch('src.mcp.kafka_mcp_client.CONFLUENT_MCP_AVAILABLE', False):
            with patch('src.mcp.kafka_mcp_client.KAFKA_PYTHON_AVAILABLE', True):
                with patch('src.mcp.kafka_mcp_client.KafkaProducer') as MockProducer:
                    with patch('src.mcp.kafka_mcp_client.KafkaAdminClient') as MockAdmin:
                        mock_producer = Mock()
                        mock_admin = Mock()
                        MockProducer.return_value = mock_producer
                        MockAdmin.return_value = mock_admin
                        
                        result = await kafka_client.connect()
                        
                        assert result is True
                        assert kafka_client.connected is True
                        assert kafka_client.kafka_producer == mock_producer
                        assert kafka_client.kafka_admin == mock_admin

    @pytest.mark.asyncio
    async def test_connect_http_fallback(self, kafka_client):
        """Test HTTP fallback when direct connections fail."""
        with patch('src.mcp.kafka_mcp_client.CONFLUENT_MCP_AVAILABLE', False):
            with patch('src.mcp.kafka_mcp_client.KAFKA_PYTHON_AVAILABLE', False):
                with patch('aiohttp.ClientSession') as MockSession:
                    mock_session = AsyncMock()
                    MockSession.return_value = mock_session
                    
                    result = await kafka_client.connect()
                    
                    assert result is True
                    assert kafka_client.connected is True
                    assert kafka_client.http_session == mock_session

    @pytest.mark.asyncio
    async def test_connect_already_connected(self, kafka_client):
        """Test connection when already connected."""
        kafka_client.connected = True
        
        result = await kafka_client.connect()
        
        assert result is True

    @pytest.mark.asyncio
    async def test_connect_all_methods_fail(self, kafka_client):
        """Test connection when all methods fail."""
        with patch('src.mcp.kafka_mcp_client.CONFLUENT_MCP_AVAILABLE', False):
            with patch('src.mcp.kafka_mcp_client.KAFKA_PYTHON_AVAILABLE', False):
                with patch('aiohttp.ClientSession', side_effect=Exception("HTTP connection failed")):
                    result = await kafka_client.connect()
                    
                    assert result is False
                    assert kafka_client.connected is False

    @pytest.mark.asyncio
    async def test_disconnect_confluent_connection(self, kafka_client):
        """Test disconnection from Confluent MCP connection."""
        mock_server = AsyncMock()
        kafka_client.confluent_server = mock_server
        kafka_client.connected = True
        
        await kafka_client.disconnect()
        
        assert kafka_client.connected is False
        assert kafka_client.confluent_server is None

    @pytest.mark.asyncio
    async def test_disconnect_kafka_python_connection(self, kafka_client, mock_kafka_producer):
        """Test disconnection from kafka-python connection."""
        kafka_client.kafka_producer = mock_kafka_producer
        kafka_client.connected = True
        
        await kafka_client.disconnect()
        
        assert kafka_client.connected is False
        assert kafka_client.kafka_producer is None
        mock_kafka_producer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_http_connection(self, kafka_client):
        """Test disconnection from HTTP connection."""
        mock_session = AsyncMock()
        kafka_client.http_session = mock_session
        kafka_client.connected = True
        
        await kafka_client.disconnect()
        
        assert kafka_client.connected is False
        assert kafka_client.http_session is None
        mock_session.close.assert_called_once()


class TestKafkaClientMessageOperations:
    """Test message publishing and consuming operations."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected Kafka MCP client for testing."""
        client = OptimizedKafkaMCPClient()
        client.connected = True
        client.http_session = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_publish_message_http(self, connected_client, mock_http_session):
        """Test publishing message via HTTP."""
        mock_response = {
            "result": {
                "topic": "customer-support-tickets",
                "partition": 0,
                "offset": 123,
                "timestamp": 1234567890
            }
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        message_data = {
            "ticket_id": "456",
            "customer_id": "123",
            "event_type": "ticket_created",
            "data": {"title": "New support ticket"}
        }
        
        result = await connected_client.publish_message("tickets", message_data)
        
        assert result["topic"] == "customer-support-tickets"
        assert result["offset"] == 123
        mock_http_session.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_message_direct_kafka(self, connected_client, mock_kafka_producer):
        """Test publishing message via direct Kafka connection."""
        connected_client.kafka_producer = mock_kafka_producer
        connected_client.http_session = None
        
        message_data = {
            "ticket_id": "456",
            "event_type": "ticket_updated",
            "data": {"status": "resolved"}
        }
        
        # Mock the send result
        future_mock = Mock()
        record_metadata = Mock()
        record_metadata.topic = "customer-support-tickets"
        record_metadata.partition = 0
        record_metadata.offset = 124
        future_mock.get.return_value = record_metadata
        mock_kafka_producer.send.return_value = future_mock
        
        result = await connected_client.publish_message("tickets", message_data)
        
        assert result["topic"] == "customer-support-tickets"
        assert result["offset"] == 124
        mock_kafka_producer.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_consume_messages_http(self, connected_client, mock_http_session):
        """Test consuming messages via HTTP."""
        mock_response = {
            "result": {
                "messages": [
                    {
                        "topic": "customer-support-tickets",
                        "partition": 0,
                        "offset": 123,
                        "key": "ticket_456",
                        "value": {"ticket_id": "456", "event_type": "ticket_created"},
                        "timestamp": 1234567890
                    },
                    {
                        "topic": "customer-support-tickets",
                        "partition": 0,
                        "offset": 124,
                        "key": "ticket_457",
                        "value": {"ticket_id": "457", "event_type": "ticket_updated"},
                        "timestamp": 1234567891
                    }
                ]
            }
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.consume_messages("tickets", limit=10)
        
        assert len(result["messages"]) == 2
        assert result["messages"][0]["key"] == "ticket_456"
        assert result["messages"][1]["offset"] == 124

    @pytest.mark.asyncio
    async def test_setup_consumer_with_handler(self, connected_client):
        """Test setting up message consumer with handler function."""
        async def message_handler(message):
            return {"processed": True, "ticket_id": message.get("ticket_id")}
        
        # Mock kafka consumer setup
        with patch('src.mcp.kafka_mcp_client.KafkaConsumer') as MockConsumer:
            mock_consumer = Mock()
            MockConsumer.return_value = mock_consumer
            
            result = await connected_client.setup_consumer("tickets", message_handler)
            
            assert result is True
            assert "tickets" in connected_client.active_consumers
            assert "tickets" in connected_client.message_handlers

    @pytest.mark.asyncio
    async def test_stop_consumer(self, connected_client):
        """Test stopping a message consumer."""
        # Setup a mock consumer
        mock_consumer = Mock()
        connected_client.active_consumers["tickets"] = mock_consumer
        connected_client.message_handlers["tickets"] = lambda x: x
        
        result = await connected_client.stop_consumer("tickets")
        
        assert result is True
        assert "tickets" not in connected_client.active_consumers
        assert "tickets" not in connected_client.message_handlers
        mock_consumer.close.assert_called_once()


class TestKafkaClientTopicManagement:
    """Test topic management operations."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected Kafka MCP client for testing."""
        client = OptimizedKafkaMCPClient()
        client.connected = True
        client.http_session = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_create_topic_http(self, connected_client, mock_http_session):
        """Test creating topic via HTTP."""
        mock_response = {
            "result": {
                "topic": "customer-support-new-topic",
                "partitions": 3,
                "replication_factor": 1,
                "created": True
            }
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.create_topic("new-topic", partitions=3, replication_factor=1)
        
        assert result["created"] is True
        assert result["topic"] == "customer-support-new-topic"
        assert result["partitions"] == 3

    @pytest.mark.asyncio
    async def test_list_topics_http(self, connected_client, mock_http_session):
        """Test listing topics via HTTP."""
        mock_response = {
            "result": {
                "topics": [
                    {
                        "name": "customer-support-tickets",
                        "partitions": 3,
                        "replication_factor": 1
                    },
                    {
                        "name": "customer-support-events",
                        "partitions": 5,
                        "replication_factor": 2
                    }
                ]
            }
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.list_topics()
        
        assert len(result["topics"]) == 2
        assert any(topic["name"] == "customer-support-tickets" for topic in result["topics"])

    @pytest.mark.asyncio
    async def test_delete_topic_http(self, connected_client, mock_http_session):
        """Test deleting topic via HTTP."""
        mock_response = {
            "result": {
                "topic": "customer-support-old-topic",
                "deleted": True
            }
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.delete_topic("old-topic")
        
        assert result["deleted"] is True
        assert result["topic"] == "customer-support-old-topic"

    @pytest.mark.asyncio
    async def test_get_topic_info_http(self, connected_client, mock_http_session):
        """Test getting topic information via HTTP."""
        mock_response = {
            "result": {
                "topic": "customer-support-tickets",
                "partitions": 3,
                "replication_factor": 1,
                "configs": {
                    "retention.ms": "604800000",
                    "cleanup.policy": "delete"
                },
                "partition_info": [
                    {"partition": 0, "leader": 1, "replicas": [1], "isr": [1]},
                    {"partition": 1, "leader": 2, "replicas": [2], "isr": [2]},
                    {"partition": 2, "leader": 3, "replicas": [3], "isr": [3]}
                ]
            }
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.get_topic_info("tickets")
        
        assert result["topic"] == "customer-support-tickets"
        assert result["partitions"] == 3
        assert len(result["partition_info"]) == 3


class TestKafkaClientCustomerSupportIntegration:
    """Test integration with customer support specific functionality."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected Kafka MCP client for testing."""
        client = OptimizedKafkaMCPClient()
        client.connected = True
        client.http_session = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_get_customers_via_kafka_events(self, connected_client, mock_http_session):
        """Test getting customers via Kafka event stream."""
        # This would be implemented as a custom method that queries customer events
        mock_response = {
            "result": [
                {"id": "1", "name": "Customer 1", "email": "customer1@example.com"},
                {"id": "2", "name": "Customer 2", "email": "customer2@example.com"}
            ]
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.get_customers(limit=100)
        
        assert len(result) == 2
        assert result[0]["name"] == "Customer 1"

    @pytest.mark.asyncio
    async def test_publish_ticket_event(self, connected_client, mock_http_session):
        """Test publishing ticket-related events."""
        ticket_event = {
            "event_type": "ticket_created",
            "ticket_id": "456",
            "customer_id": "123",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "title": "Login issue",
                "priority": "high",
                "category": "technical"
            }
        }
        
        mock_response = {
            "result": {
                "topic": "customer-support-tickets",
                "partition": 0,
                "offset": 125
            }
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.publish_ticket_event(ticket_event)
        
        assert result["topic"] == "customer-support-tickets"
        assert result["offset"] == 125

    @pytest.mark.asyncio
    async def test_get_customer_interaction_history(self, connected_client, mock_http_session):
        """Test getting customer interaction history from Kafka events."""
        mock_response = {
            "result": {
                "customer_id": "123",
                "interactions": [
                    {
                        "timestamp": "2024-01-01T10:00:00Z",
                        "event_type": "ticket_created",
                        "ticket_id": "456",
                        "data": {"title": "Login issue"}
                    },
                    {
                        "timestamp": "2024-01-01T11:00:00Z",
                        "event_type": "ticket_updated",
                        "ticket_id": "456",
                        "data": {"status": "in_progress"}
                    },
                    {
                        "timestamp": "2024-01-01T12:00:00Z",
                        "event_type": "ticket_resolved",
                        "ticket_id": "456",
                        "data": {"resolution": "Password reset"}
                    }
                ]
            }
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.get_customer_interaction_history("123")
        
        assert result["customer_id"] == "123"
        assert len(result["interactions"]) == 3
        assert result["interactions"][0]["event_type"] == "ticket_created"


class TestKafkaClientErrorHandling:
    """Test error handling in Kafka MCP client."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected Kafka MCP client for testing."""
        client = OptimizedKafkaMCPClient()
        client.connected = True
        client.http_session = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_kafka_broker_unavailable(self, connected_client):
        """Test handling when Kafka broker is unavailable."""
        mock_producer = Mock()
        mock_producer.send.side_effect = Exception("Kafka broker unavailable")
        connected_client.kafka_producer = mock_producer
        connected_client.http_session = None
        
        with pytest.raises(KafkaClientError, match="Kafka broker unavailable"):
            await connected_client.publish_message("tickets", {"test": "data"})

    @pytest.mark.asyncio
    async def test_topic_not_found(self, connected_client, mock_http_session):
        """Test handling when topic is not found."""
        mock_response = {
            "error": {
                "code": "UNKNOWN_TOPIC_OR_PARTITION",
                "message": "Topic 'nonexistent-topic' does not exist"
            }
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 404
        connected_client.http_session = mock_http_session
        
        with pytest.raises(KafkaClientError, match="does not exist"):
            await connected_client.publish_message("nonexistent-topic", {"test": "data"})

    @pytest.mark.asyncio
    async def test_serialization_error(self, connected_client):
        """Test handling of message serialization errors."""
        mock_producer = Mock()
        mock_producer.send.side_effect = TypeError("Object is not JSON serializable")
        connected_client.kafka_producer = mock_producer
        connected_client.http_session = None
        
        # Test with non-serializable data
        non_serializable_data = {"datetime": datetime.now()}
        
        with pytest.raises(KafkaClientError):
            await connected_client.publish_message("tickets", non_serializable_data)

    @pytest.mark.asyncio
    async def test_consumer_offset_error(self, connected_client):
        """Test handling of consumer offset errors."""
        # Test error handling when consumer can't commit offsets
        mock_consumer = Mock()
        mock_consumer.commit.side_effect = Exception("Offset commit failed")
        connected_client.active_consumers["tickets"] = mock_consumer
        
        # This would be called during message processing
        try:
            await connected_client.commit_consumer_offset("tickets")
        except KafkaClientError as e:
            assert "Offset commit failed" in str(e)


class TestKafkaClientPerformance:
    """Test performance characteristics of Kafka MCP client."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected Kafka MCP client for testing."""
        client = OptimizedKafkaMCPClient()
        client.connected = True
        client.http_session = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_batch_message_publishing(self, connected_client, mock_http_session):
        """Test batch publishing of messages."""
        messages = [
            {"ticket_id": f"ticket_{i}", "event_type": "ticket_created"}
            for i in range(10)
        ]
        
        mock_response = {
            "result": {
                "published": 10,
                "failed": 0,
                "offsets": [{"partition": 0, "offset": i} for i in range(10)]
            }
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.publish_messages_batch("tickets", messages)
        
        assert result["published"] == 10
        assert result["failed"] == 0
        assert len(result["offsets"]) == 10

    @pytest.mark.asyncio
    async def test_concurrent_message_publishing(self, connected_client, mock_http_session):
        """Test concurrent message publishing."""
        mock_response = {
            "result": {
                "topic": "customer-support-tickets",
                "partition": 0,
                "offset": 100
            }
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = mock_response
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        # Publish messages concurrently
        tasks = [
            connected_client.publish_message("tickets", {"message_id": i})
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(result["topic"] == "customer-support-tickets" for result in results)
        assert mock_http_session.post.call_count == 5

    @pytest.mark.asyncio
    async def test_high_throughput_consuming(self, connected_client, mock_http_session):
        """Test high-throughput message consuming."""
        # Simulate large batch of messages
        large_message_batch = {
            "result": {
                "messages": [
                    {
                        "offset": i,
                        "key": f"key_{i}",
                        "value": {"message_id": i, "data": f"Message {i}"},
                        "timestamp": 1234567890 + i
                    }
                    for i in range(100)
                ]
            }
        }
        
        mock_http_session.post.return_value.__aenter__.return_value.json.return_value = large_message_batch
        mock_http_session.post.return_value.__aenter__.return_value.status = 200
        connected_client.http_session = mock_http_session
        
        result = await connected_client.consume_messages("tickets", limit=100)
        
        assert len(result["messages"]) == 100
        assert result["messages"][0]["offset"] == 0
        assert result["messages"][99]["offset"] == 99


class TestKafkaClientConfiguration:
    """Test various configuration scenarios for Kafka MCP client."""

    def test_default_configuration(self):
        """Test default configuration values."""
        client = OptimizedKafkaMCPClient()
        
        assert client.bootstrap_servers == "localhost:9092"
        assert client.mcp_server_url == "http://localhost:8002"
        assert client.use_direct_connection is False  # False when libraries not available
        assert client.topic_prefix == "customer-support"
        assert client.group_id == "ai-support-group"
        assert client.cache_duration == 60

    def test_custom_configuration(self):
        """Test custom configuration values."""
        client = OptimizedKafkaMCPClient(
            bootstrap_servers="kafka.example.com:9092,kafka2.example.com:9092",
            mcp_server_url="http://kafka-mcp.example.com:9000",
            use_direct_connection=True,
            topic_prefix="custom-support",
            group_id="custom-group"
        )
        
        assert "kafka.example.com" in client.bootstrap_servers
        assert client.mcp_server_url == "http://kafka-mcp.example.com:9000"
        assert client.topic_prefix == "custom-support"
        assert client.group_id == "custom-group"

    def test_topic_name_formatting(self):
        """Test topic name formatting with prefix."""
        client = OptimizedKafkaMCPClient(topic_prefix="test-prefix")
        
        # This would be implemented as a helper method
        formatted_topic = client._format_topic_name("tickets")
        assert formatted_topic == "test-prefix-tickets"
        
        formatted_topic = client._format_topic_name("events")
        assert formatted_topic == "test-prefix-events"

    def test_configuration_validation(self):
        """Test configuration validation."""
        # Test that client handles various configuration combinations gracefully
        
        # Empty bootstrap servers
        client1 = OptimizedKafkaMCPClient(bootstrap_servers="")
        assert client1.bootstrap_servers == ""  # Should accept but might fail to connect
        
        # Invalid URL
        client2 = OptimizedKafkaMCPClient(mcp_server_url="invalid-url")
        assert client2.mcp_server_url == "invalid-url"  # Should accept but might fail to connect
