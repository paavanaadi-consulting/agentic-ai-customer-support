import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime
import uuid
import json

from src.api.kafka_routes import router
from src.api.schemas import (
    KafkaMessageRequest, KafkaMessageResponse,
    KafkaTopicRequest, KafkaTopicResponse,
    StreamingQueryRequest, StreamingQueryResponse,
    TopicMetadataResponse, ClusterInfoResponse,
    ConsumerRequest, ConsumerResponse,
    HealthCheckResponse, ActiveConsumersResponse
)


def create_test_app():
    """Create a test FastAPI application with Kafka routes"""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return app


@pytest.fixture
def client():
    app = create_test_app()
    return TestClient(app)


@pytest.fixture
def mock_kafka_client():
    """Mock Kafka MCP client for testing"""
    client = AsyncMock()
    
    # Mock call_tool responses
    client.call_tool.return_value = {
        "success": True,
        "message": "Operation completed successfully",
        "data": {"topic": "test_topic", "partition": 0, "offset": 123}
    }
    
    return client


@pytest.fixture
def mock_query_service():
    """Mock query service for streaming tests"""
    service = AsyncMock()
    service.process_streaming_query.return_value = {
        "query_id": str(uuid.uuid4()),
        "result": "Streaming response",
        "confidence": 0.92,
        "agent_used": "streaming_agent"
    }
    return service


@pytest.fixture(autouse=True)
def mock_dependencies(mock_kafka_client, mock_query_service):
    """Auto-use fixture to mock all dependencies"""
    with patch('src.api.kafka_routes.get_kafka_client_dep', return_value=mock_kafka_client), \
         patch('src.api.kafka_routes.get_query_service_dep', return_value=mock_query_service):
        yield


class TestKafkaMessageEndpoints:
    """Test Kafka message publishing and consuming endpoints"""

    def test_publish_message_success(self, client, mock_kafka_client):
        """Test successful message publishing"""
        request_data = {
            "topic": "customer_queries",
            "message": {"query": "How do I reset my password?", "customer_id": "123"},
            "key": "customer_123"
        }
        
        response = client.post("/api/v1/streaming/publish", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "topic" in data

    def test_publish_message_invalid_data(self, client):
        """Test message publishing with invalid data"""
        request_data = {
            "topic": "",  # Empty topic
            "message": {"query": "test"}
        }
        
        response = client.post("/api/v1/streaming/publish", json=request_data)
        assert response.status_code == 422

    def test_consume_messages_success(self, client, mock_kafka_client):
        """Test successful message consumption"""
        mock_kafka_client.call_tool.return_value = {
            "success": True,
            "messages": [
                {
                    "key": "customer_123",
                    "value": {"query": "test query", "customer_id": "123"},
                    "topic": "customer_queries",
                    "partition": 0,
                    "offset": 100,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }
        
        response = client.get("/api/v1/streaming/consume/customer_queries?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "messages" in data

    def test_consume_messages_topic_not_found(self, client, mock_kafka_client):
        """Test consuming from non-existent topic"""
        mock_kafka_client.call_tool.side_effect = Exception("Topic not found")
        
        response = client.get("/api/v1/streaming/consume/nonexistent_topic")
        assert response.status_code == 500


class TestKafkaTopicEndpoints:
    """Test Kafka topic management endpoints"""

    def test_create_topic_success(self, client, mock_kafka_client):
        """Test successful topic creation"""
        request_data = {
            "topic_name": "new_customer_events",
            "num_partitions": 3,
            "replication_factor": 1,
            "config": {"cleanup.policy": "delete", "retention.ms": "604800000"}
        }
        
        response = client.post("/api/v1/streaming/topics", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True

    def test_list_topics_success(self, client, mock_kafka_client):
        """Test listing Kafka topics"""
        mock_kafka_client.call_tool.return_value = {
            "success": True,
            "topics": [
                {"name": "customer_queries", "partitions": 3, "replication_factor": 1},
                {"name": "agent_responses", "partitions": 2, "replication_factor": 1}
            ]
        }
        
        response = client.get("/api/v1/streaming/topics")
        assert response.status_code == 200
        
        data = response.json()
        assert "topics" in data
        assert len(data["topics"]) == 2

    def test_get_topic_metadata_success(self, client, mock_kafka_client):
        """Test getting topic metadata"""
        topic_name = "customer_queries"
        mock_kafka_client.call_tool.return_value = {
            "success": True,
            "metadata": {
                "name": topic_name,
                "partitions": 3,
                "replication_factor": 1,
                "config": {"cleanup.policy": "delete"}
            }
        }
        
        response = client.get(f"/api/v1/streaming/topics/{topic_name}/metadata")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == topic_name
        assert data["partitions"] == 3

    def test_delete_topic_success(self, client, mock_kafka_client):
        """Test successful topic deletion"""
        topic_name = "old_topic"
        
        response = client.delete(f"/api/v1/streaming/topics/{topic_name}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True


class TestStreamingQueryEndpoints:
    """Test streaming query processing endpoints"""

    def test_process_streaming_query_success(self, client, mock_query_service):
        """Test successful streaming query processing"""
        request_data = {
            "query": "What's my account balance?",
            "customer_id": "customer_123",
            "stream_to_topic": "agent_responses",
            "query_type": "billing",
            "priority": "high"
        }
        
        response = client.post("/api/v1/streaming/queries/process", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "query_id" in data
        assert data["result"] == "Streaming response"

    def test_stream_query_responses(self, client):
        """Test streaming query responses endpoint"""
        # Note: This is a streaming endpoint, so we test that it returns the correct response type
        response = client.get("/api/v1/streaming/queries/stream?customer_id=123")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"


class TestKafkaMonitoringEndpoints:
    """Test Kafka monitoring and health endpoints"""

    def test_kafka_health_check_success(self, client, mock_kafka_client):
        """Test Kafka health check"""
        mock_kafka_client.call_tool.return_value = {
            "success": True,
            "cluster_info": {
                "cluster_id": "test_cluster",
                "brokers": [{"id": 0, "host": "localhost", "port": 9092}],
                "version": "2.8.0"
            }
        }
        
        response = client.get("/api/v1/streaming/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "cluster_info" in data

    def test_kafka_health_check_failure(self, client, mock_kafka_client):
        """Test Kafka health check when Kafka is unavailable"""
        mock_kafka_client.call_tool.side_effect = Exception("Connection failed")
        
        response = client.get("/api/v1/streaming/health")
        assert response.status_code == 503
        
        data = response.json()
        assert data["status"] == "unhealthy"

    def test_get_cluster_info_success(self, client, mock_kafka_client):
        """Test getting Kafka cluster information"""
        mock_kafka_client.call_tool.return_value = {
            "success": True,
            "cluster_info": {
                "cluster_id": "test_cluster_123",
                "brokers": [
                    {"id": 0, "host": "broker1", "port": 9092},
                    {"id": 1, "host": "broker2", "port": 9092}
                ],
                "controller": {"id": 0},
                "version": "2.8.0"
            }
        }
        
        response = client.get("/api/v1/streaming/cluster/info")
        assert response.status_code == 200
        
        data = response.json()
        assert data["cluster_id"] == "test_cluster_123"
        assert len(data["brokers"]) == 2

    def test_get_active_consumers_success(self, client, mock_kafka_client):
        """Test getting active consumers"""
        mock_kafka_client.call_tool.return_value = {
            "success": True,
            "consumers": [
                {
                    "group_id": "customer_support_group",
                    "client_id": "consumer_1",
                    "topic": "customer_queries",
                    "partition": 0,
                    "offset": 150
                }
            ]
        }
        
        response = client.get("/api/v1/streaming/consumers/active")
        assert response.status_code == 200
        
        data = response.json()
        assert "consumers" in data
        assert len(data["consumers"]) == 1


class TestKafkaConsumerManagement:
    """Test Kafka consumer management endpoints"""

    def test_start_consumer_success(self, client, mock_kafka_client):
        """Test starting a Kafka consumer"""
        request_data = {
            "topic": "customer_queries",
            "group_id": "support_agents",
            "auto_offset_reset": "earliest",
            "max_poll_records": 100
        }
        
        response = client.post("/api/v1/streaming/consumers/start", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "consumer_id" in data

    def test_stop_consumer_success(self, client, mock_kafka_client):
        """Test stopping a Kafka consumer"""
        consumer_id = "test_consumer_123"
        
        response = client.post(f"/api/v1/streaming/consumers/{consumer_id}/stop")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True

    def test_get_consumer_status_success(self, client, mock_kafka_client):
        """Test getting consumer status"""
        consumer_id = "test_consumer_123"
        mock_kafka_client.call_tool.return_value = {
            "success": True,
            "status": {
                "consumer_id": consumer_id,
                "state": "running",
                "topic": "customer_queries",
                "group_id": "support_agents",
                "last_poll": datetime.utcnow().isoformat(),
                "messages_processed": 250
            }
        }
        
        response = client.get(f"/api/v1/streaming/consumers/{consumer_id}/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["consumer_id"] == consumer_id
        assert data["state"] == "running"


class TestKafkaIntegrationEndpoints:
    """Test Kafka integration specific endpoints"""

    def test_setup_customer_support_topics_success(self, client, mock_kafka_client):
        """Test setting up customer support topics"""
        response = client.post("/api/v1/streaming/setup/customer-support")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "topics_created" in data

    def test_get_recent_queries_success(self, client, mock_kafka_client):
        """Test getting recent queries from Kafka"""
        mock_kafka_client.call_tool.return_value = {
            "success": True,
            "queries": [
                {
                    "query_id": str(uuid.uuid4()),
                    "query": "How do I reset my password?",
                    "customer_id": "123",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }
        
        response = client.get("/api/v1/streaming/queries/recent?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "queries" in data
        assert len(data["queries"]) == 1

    def test_get_recent_responses_success(self, client, mock_kafka_client):
        """Test getting recent agent responses from Kafka"""
        mock_kafka_client.call_tool.return_value = {
            "success": True,
            "responses": [
                {
                    "query_id": str(uuid.uuid4()),
                    "response": "To reset your password, go to settings...",
                    "agent_id": "agent_1",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }
        
        response = client.get("/api/v1/streaming/responses/recent?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "responses" in data
        assert len(data["responses"]) == 1


class TestErrorHandling:
    """Test error handling in Kafka routes"""

    def test_kafka_client_unavailable(self, client):
        """Test behavior when Kafka client is unavailable"""
        with patch('src.api.kafka_routes.get_kafka_client_dep', side_effect=Exception("Kafka unavailable")):
            response = client.post("/api/v1/streaming/publish", json={
                "topic": "test",
                "message": {"test": "data"}
            })
            assert response.status_code == 500

    def test_invalid_topic_name(self, client, mock_kafka_client):
        """Test handling of invalid topic names"""
        mock_kafka_client.call_tool.side_effect = Exception("Invalid topic name")
        
        request_data = {
            "topic_name": "invalid topic name with spaces",
            "num_partitions": 1,
            "replication_factor": 1
        }
        
        response = client.post("/api/v1/streaming/topics", json=request_data)
        assert response.status_code == 500

    def test_consumer_already_exists(self, client, mock_kafka_client):
        """Test starting a consumer that already exists"""
        mock_kafka_client.call_tool.side_effect = Exception("Consumer already exists")
        
        request_data = {
            "topic": "customer_queries",
            "group_id": "existing_group"
        }
        
        response = client.post("/api/v1/streaming/consumers/start", json=request_data)
        assert response.status_code == 500
