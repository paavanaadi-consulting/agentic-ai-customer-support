"""
Comprehensive tests for Kafka/Streaming API routes.
Tests all Kafka endpoints including streaming, pub/sub, and error handling.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime
import json
import asyncio

from src.api.schemas import (
    KafkaMessageRequest, KafkaMessageResponse,
    KafkaTopicRequest, KafkaTopicResponse,
    KafkaConsumeRequest, KafkaConsumeResponse,
    StreamingQueryRequest, StreamingQueryResponse,
    TopicMetadataResponse, ClusterInfoResponse,
    HealthCheckResponse, CustomerSupportSetupResponse
)


class TestKafkaMessageEndpoints:
    """Test Kafka message publishing and consuming endpoints."""
    
    def test_publish_message_success(self, test_client, mock_service_dependencies, sample_kafka_message_request):
        """Test successful message publishing."""
        # Setup mock response
        mock_result = {
            'success': True,
            'result': {
                'topic': sample_kafka_message_request.topic,
                'partition': 0,
                'offset': 12345
            }
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        response = test_client.post("/streaming/publish", json=sample_kafka_message_request.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["topic"] == sample_kafka_message_request.topic
        assert data["partition"] == 0
        assert data["offset"] == 12345
        
        # Verify Kafka client was called correctly
        mock_service_dependencies['kafka_client'].call_tool.assert_called_once_with(
            "publish_message",
            {
                'topic': sample_kafka_message_request.topic,
                'message': sample_kafka_message_request.message,
                'key': sample_kafka_message_request.key
            }
        )
    
    def test_publish_message_failure(self, test_client, mock_service_dependencies, sample_kafka_message_request):
        """Test message publishing failure."""
        # Setup mock to return failure
        mock_result = {
            'success': False,
            'error': 'Failed to publish to topic'
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        response = test_client.post("/streaming/publish", json=sample_kafka_message_request.model_dump())
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to publish to topic" in data["detail"]
    
    def test_publish_message_exception(self, test_client, mock_service_dependencies, sample_kafka_message_request):
        """Test message publishing with exception."""
        # Setup mock to raise exception
        mock_service_dependencies['kafka_client'].call_tool.side_effect = Exception("Connection error")
        
        response = test_client.post("/streaming/publish", json=sample_kafka_message_request.model_dump())
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to publish message" in data["detail"]
        assert "Connection error" in data["detail"]
    
    def test_publish_message_invalid_input(self, test_client, mock_service_dependencies):
        """Test message publishing with invalid input."""
        invalid_request = {"topic": ""}  # Empty topic, missing message
        
        response = test_client.post("/streaming/publish", json=invalid_request)
        
        assert response.status_code == 422  # Validation error
    
    def test_consume_messages_success(self, test_client, mock_service_dependencies):
        """Test successful message consumption."""
        # Setup mock response
        mock_result = {
            'success': True,
            'result': {
                'messages': [
                    {'key': 'key1', 'value': {'data': 'message1'}},
                    {'key': 'key2', 'value': {'data': 'message2'}}
                ],
                'count': 2
            }
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        consume_request = KafkaConsumeRequest(
            topic="test_topic",
            max_messages=10,
            timeout_ms=5000
        )
        
        response = test_client.post("/streaming/consume", json=consume_request.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert len(data["messages"]) == 2
        
        # Verify Kafka client was called correctly
        mock_service_dependencies['kafka_client'].call_tool.assert_called_once_with(
            "consume_messages",
            {
                'topic': "test_topic",
                'max_messages': 10,
                'timeout_ms': 5000
            }
        )
    
    def test_consume_messages_no_messages(self, test_client, mock_service_dependencies):
        """Test consuming when no messages are available."""
        # Setup mock to return empty result
        mock_result = {
            'success': True,
            'result': {
                'messages': [],
                'count': 0
            }
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        consume_request = KafkaConsumeRequest(topic="empty_topic")
        
        response = test_client.post("/streaming/consume", json=consume_request.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 0
        assert data["messages"] == []
    
    def test_consume_messages_failure(self, test_client, mock_service_dependencies):
        """Test message consumption failure."""
        # Setup mock to return failure
        mock_result = {
            'success': False,
            'error': 'Topic does not exist'
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        consume_request = KafkaConsumeRequest(topic="nonexistent_topic")
        
        response = test_client.post("/streaming/consume", json=consume_request.model_dump())
        
        assert response.status_code == 500
        data = response.json()
        assert "Topic does not exist" in data["detail"]


class TestKafkaTopicEndpoints:
    """Test Kafka topic management endpoints."""
    
    def test_create_topic_success(self, test_client, mock_service_dependencies):
        """Test successful topic creation."""
        mock_result = {
            'success': True,
            'result': {
                'topic': 'new_topic',
                'partitions': 3,
                'replication_factor': 1
            }
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        topic_request = KafkaTopicRequest(
            topic="new_topic",
            num_partitions=3,
            replication_factor=1
        )
        
        response = test_client.post("/streaming/topics", json=topic_request.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["topic"] == "new_topic"
        assert data["partitions"] == 3
        assert data["replication_factor"] == 1
    
    def test_create_topic_already_exists(self, test_client, mock_service_dependencies):
        """Test creating a topic that already exists."""
        mock_result = {
            'success': False,
            'error': 'Topic already exists'
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        topic_request = KafkaTopicRequest(topic="existing_topic")
        
        response = test_client.post("/streaming/topics", json=topic_request.model_dump())
        
        assert response.status_code == 500
        data = response.json()
        assert "Topic already exists" in data["detail"]
    
    def test_list_topics_success(self, test_client, mock_service_dependencies):
        """Test successful topic listing."""
        mock_result = {
            'success': True,
            'topics': ['topic1', 'topic2', 'topic3'],
            'count': 3
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        response = test_client.get("/streaming/topics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 3
        assert len(data["topics"]) == 3
        assert "topic1" in data["topics"]
    
    def test_get_topic_metadata_success(self, test_client, mock_service_dependencies):
        """Test successful topic metadata retrieval."""
        mock_result = {
            'success': True,
            'topic': 'test_topic',
            'metadata': {
                'partitions': 3,
                'replication_factor': 1,
                'config': {'retention.ms': '604800000'}
            }
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        response = test_client.get("/streaming/topics/test_topic/metadata")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["topic"] == "test_topic"
        assert "partitions" in data["metadata"]
    
    def test_get_topic_metadata_not_found(self, test_client, mock_service_dependencies):
        """Test topic metadata for non-existent topic."""
        mock_result = {
            'success': False,
            'error': 'Topic not found'
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        response = test_client.get("/streaming/topics/nonexistent/metadata")
        
        assert response.status_code == 500
        data = response.json()
        assert "Topic not found" in data["detail"]


class TestStreamingEndpoints:
    """Test streaming-specific endpoints."""
    
    def test_streaming_query_success(self, test_client, mock_service_dependencies):
        """Test successful streaming query."""
        # Setup mocks
        mock_query_result = {
            'query_id': 'stream_query_123',
            'status': 'processing',
            'stream_id': 'stream_456'
        }
        mock_service_dependencies['query_service'].process_streaming_query.return_value = mock_query_result
        
        streaming_request = StreamingQueryRequest(
            query="What's my account balance?",
            customer_id="customer_123",
            stream_response=True
        )
        
        response = test_client.post("/streaming/query", json=streaming_request.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["query_id"] == "stream_query_123"
        assert data["status"] == "processing"
        assert data["stream_id"] == "stream_456"
    
    def test_streaming_query_with_callback(self, test_client, mock_service_dependencies):
        """Test streaming query with callback URL."""
        mock_service_dependencies['query_service'].process_streaming_query.return_value = {
            'query_id': 'callback_query_123',
            'status': 'queued',
            'callback_registered': True
        }
        
        streaming_request = StreamingQueryRequest(
            query="Process my refund",
            customer_id="customer_123",
            callback_url="https://api.example.com/webhook"
        )
        
        response = test_client.post("/streaming/query", json=streaming_request.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["query_id"] == "callback_query_123"
        assert data["status"] == "queued"
    
    @pytest.mark.asyncio
    async def test_streaming_response(self, mock_service_dependencies):
        """Test streaming response endpoint."""
        from httpx import AsyncClient
        from src.api.api_main import app
        
        # Mock streaming data
        async def mock_stream_generator():
            for i in range(3):
                yield f"data: chunk_{i}\n\n"
                await asyncio.sleep(0.1)
        
        mock_service_dependencies['query_service'].get_streaming_response.return_value = mock_stream_generator()
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            async with client.stream("GET", "/streaming/response/stream_123") as response:
                assert response.status_code == 200
                assert response.headers["content-type"] == "text/plain"
                
                chunks = []
                async for chunk in response.aiter_text():
                    chunks.append(chunk)
                
                assert len(chunks) > 0
                assert "chunk_0" in "".join(chunks)


class TestCustomerSupportEndpoints:
    """Test customer support specific Kafka endpoints."""
    
    def test_setup_customer_support_success(self, test_client, mock_service_dependencies):
        """Test successful customer support setup."""
        mock_result = {
            'success': True,
            'message': 'Customer support setup completed',
            'topics': ['customer_queries', 'agent_responses', 'feedback']
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        response = test_client.post("/streaming/setup/customer-support")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "setup completed" in data["message"]
        assert len(data["topics"]) == 3
        assert "customer_queries" in data["topics"]
    
    def test_publish_customer_query_success(self, test_client, mock_service_dependencies):
        """Test publishing customer query."""
        mock_result = {
            'success': True,
            'result': {
                'topic': 'customer_queries',
                'partition': 0,
                'offset': 100
            }
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        query_request = {
            "query_id": "query_123",
            "customer_id": "customer_123",
            "query_text": "I need help with my order",
            "priority": "normal"
        }
        
        response = test_client.post("/streaming/customer/query", json=query_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["topic"] == "customer_queries"
    
    def test_publish_agent_response_success(self, test_client, mock_service_dependencies):
        """Test publishing agent response."""
        mock_result = {
            'success': True,
            'result': {
                'topic': 'agent_responses',
                'partition': 1,
                'offset': 200
            }
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        response_request = {
            "query_id": "query_123",
            "agent_id": "agent_456",
            "response_text": "I can help you with that order",
            "confidence": 0.95
        }
        
        response = test_client.post("/streaming/agent/response", json=response_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["topic"] == "agent_responses"
    
    def test_get_recent_queries_success(self, test_client, mock_service_dependencies):
        """Test retrieving recent customer queries."""
        mock_result = {
            'success': True,
            'queries': [
                {
                    'query_id': 'query_1',
                    'customer_id': 'customer_123',
                    'query_text': 'Help with login',
                    'timestamp': '2024-01-01T10:00:00Z'
                },
                {
                    'query_id': 'query_2',
                    'customer_id': 'customer_456',
                    'query_text': 'Billing question',
                    'timestamp': '2024-01-01T10:05:00Z'
                }
            ],
            'count': 2
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        response = test_client.get("/streaming/queries/recent?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert len(data["queries"]) == 2
        assert data["queries"][0]["query_id"] == "query_1"
    
    def test_get_recent_responses_success(self, test_client, mock_service_dependencies):
        """Test retrieving recent agent responses."""
        mock_result = {
            'success': True,
            'responses': [
                {
                    'query_id': 'query_1',
                    'agent_id': 'agent_123',
                    'response_text': 'Login help provided',
                    'confidence': 0.9,
                    'timestamp': '2024-01-01T10:01:00Z'
                }
            ],
            'count': 1
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        response = test_client.get("/streaming/responses/recent?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 1
        assert len(data["responses"]) == 1


class TestKafkaHealthAndStatus:
    """Test Kafka health check and status endpoints."""
    
    def test_health_check_success(self, test_client, mock_service_dependencies):
        """Test successful Kafka health check."""
        mock_result = {
            'status': 'healthy',
            'connected': True,
            'client_type': 'optimized',
            'bootstrap_servers': 'localhost:9092',
            'topic_prefix': 'agentic_ai_',
            'test_result': {'ping': 'success'}
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        response = test_client.get("/streaming/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["connected"] is True
        assert data["client_type"] == "optimized"
        assert data["bootstrap_servers"] == "localhost:9092"
    
    def test_health_check_unhealthy(self, test_client, mock_service_dependencies):
        """Test Kafka health check when unhealthy."""
        mock_result = {
            'status': 'unhealthy',
            'connected': False,
            'client_type': 'optimized',
            'bootstrap_servers': 'localhost:9092',
            'topic_prefix': 'agentic_ai_',
            'test_result': {'error': 'Connection timeout'}
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        response = test_client.get("/streaming/health")
        
        assert response.status_code == 200  # Health endpoint should return 200 even if unhealthy
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["connected"] is False
        assert "error" in data["test_result"]
    
    def test_get_cluster_info_success(self, test_client, mock_service_dependencies):
        """Test successful cluster info retrieval."""
        mock_result = {
            'success': True,
            'cluster': {
                'cluster_id': 'test-cluster',
                'brokers': [
                    {'id': 0, 'host': 'localhost', 'port': 9092}
                ],
                'controller': {'id': 0}
            }
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        response = test_client.get("/streaming/cluster/info")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cluster_id" in data["cluster"]
        assert len(data["cluster"]["brokers"]) == 1
    
    def test_get_active_consumers_success(self, test_client, mock_service_dependencies):
        """Test retrieving active consumers."""
        mock_result = {
            'success': True,
            'active_consumers': ['consumer_1', 'consumer_2'],
            'count': 2
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        response = test_client.get("/streaming/consumers/active")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert "consumer_1" in data["active_consumers"]


class TestKafkaConsumerManagement:
    """Test Kafka consumer management endpoints."""
    
    def test_start_consumer_success(self, test_client, mock_service_dependencies):
        """Test starting a Kafka consumer."""
        mock_result = {
            'success': True,
            'consumer_id': 'consumer_123',
            'message': 'Consumer started successfully'
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        consumer_request = {
            "topic": "customer_queries",
            "consumer_id": "consumer_123",
            "auto_commit": True
        }
        
        response = test_client.post("/streaming/consumers/start", json=consumer_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["consumer_id"] == "consumer_123"
        assert "started successfully" in data["message"]
    
    def test_stop_consumer_success(self, test_client, mock_service_dependencies):
        """Test stopping a Kafka consumer."""
        mock_result = {
            'success': True,
            'consumer_id': 'consumer_123',
            'message': 'Consumer stopped successfully'
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        response = test_client.post("/streaming/consumers/consumer_123/stop")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["consumer_id"] == "consumer_123"
    
    def test_get_consumer_status_success(self, test_client, mock_service_dependencies):
        """Test getting consumer status."""
        mock_result = {
            'success': True,
            'running': True,
            'active_topics': ['customer_queries', 'agent_responses'],
            'messages_processed': 150,
            'messages_failed': 2,
            'last_processed_time': '2024-01-01T10:30:00Z'
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        response = test_client.get("/streaming/consumers/consumer_123/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["running"] is True
        assert len(data["active_topics"]) == 2
        assert data["messages_processed"] == 150


class TestErrorHandling:
    """Test error handling in Kafka endpoints."""
    
    def test_kafka_client_unavailable(self, test_client):
        """Test when Kafka client is not available."""
        with patch('src.api.dependencies.get_kafka_client_dep') as mock_dep:
            from fastapi import HTTPException
            mock_dep.side_effect = HTTPException(status_code=503, detail="Kafka MCP client not available")
            
            response = test_client.get("/streaming/health")
            
            assert response.status_code == 503
            data = response.json()
            assert "Kafka MCP client not available" in data["detail"]
    
    def test_kafka_connection_error(self, test_client, mock_service_dependencies):
        """Test handling of Kafka connection errors."""
        mock_service_dependencies['kafka_client'].call_tool.side_effect = Exception("Kafka connection failed")
        
        response = test_client.get("/streaming/topics")
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to list topics" in data["detail"]
    
    def test_invalid_topic_name(self, test_client, mock_service_dependencies):
        """Test handling of invalid topic names."""
        invalid_topic_request = KafkaTopicRequest(
            topic="",  # Empty topic name
            num_partitions=1
        )
        
        response = test_client.post("/streaming/topics", json=invalid_topic_request.model_dump())
        
        assert response.status_code == 422  # Validation error
    
    def test_consumer_already_exists(self, test_client, mock_service_dependencies):
        """Test starting a consumer that already exists."""
        mock_result = {
            'success': False,
            'error': 'Consumer already exists'
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        consumer_request = {
            "topic": "test_topic",
            "consumer_id": "existing_consumer"
        }
        
        response = test_client.post("/streaming/consumers/start", json=consumer_request)
        
        assert response.status_code == 500
        data = response.json()
        assert "Consumer already exists" in data["detail"]


class TestPerformance:
    """Test performance aspects of Kafka endpoints."""
    
    @pytest.mark.slow
    def test_high_volume_message_publishing(self, test_client, mock_service_dependencies):
        """Test publishing many messages quickly."""
        # Setup mock to simulate successful publishing
        mock_result = {
            'success': True,
            'result': {'topic': 'test_topic', 'partition': 0, 'offset': 0}
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        message_request = KafkaMessageRequest(
            topic="test_topic",
            message={"data": "test_message"}
        )
        
        # Publish 100 messages
        for i in range(100):
            response = test_client.post("/streaming/publish", json=message_request.model_dump())
            assert response.status_code == 200
        
        # Verify all calls were made
        assert mock_service_dependencies['kafka_client'].call_tool.call_count == 100
    
    @pytest.mark.slow
    def test_large_message_publishing(self, test_client, mock_service_dependencies):
        """Test publishing large messages."""
        mock_result = {
            'success': True,
            'result': {'topic': 'test_topic', 'partition': 0, 'offset': 0}
        }
        mock_service_dependencies['kafka_client'].call_tool.return_value = mock_result
        
        # Create a large message (1MB of data)
        large_data = "x" * (1024 * 1024)
        large_message_request = KafkaMessageRequest(
            topic="test_topic",
            message={"large_data": large_data}
        )
        
        response = test_client.post("/streaming/publish", json=large_message_request.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestSecurity:
    """Test security aspects of Kafka endpoints."""
    
    @pytest.mark.skip(reason="Security features not implemented yet")
    def test_topic_creation_authorization(self, test_client):
        """Test that topic creation requires proper authorization."""
        # This would test that only authorized users can create topics
        pass
    
    @pytest.mark.skip(reason="Security features not implemented yet")
    def test_message_encryption(self, test_client):
        """Test that sensitive messages are encrypted."""
        # This would test message encryption for sensitive data
        pass
    
    @pytest.mark.skip(reason="Security features not implemented yet")
    def test_consumer_isolation(self, test_client):
        """Test that consumers are properly isolated."""
        # This would test that consumers can only access authorized topics
        pass