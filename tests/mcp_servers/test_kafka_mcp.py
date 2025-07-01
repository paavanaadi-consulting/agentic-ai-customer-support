"""
Comprehensive unit tests for Kafka MCP Client
"""
import pytest
import asyncio
import json
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.mcp.kafka_mcp_client import OptimizedKafkaMCPClient

class TestOptimizedKafkaMCPClient:
    """Test suite for Optimized Kafka MCP Client"""
    
    @pytest.fixture
    def kafka_client(self):
        return OptimizedKafkaMCPClient(
            bootstrap_servers="localhost:9092",
            topic_prefix="test",
            group_id="test-group"
        )
    
    @pytest.mark.asyncio
    async def test_initialization(self, kafka_client):
        """Test client initialization"""
        assert kafka_client.bootstrap_servers == "localhost:9092"
        assert kafka_client.topic_prefix == "test"
        assert kafka_client.group_id == "test-group"
        assert kafka_client.connected == False  # Initially false
        assert kafka_client.kafka_producer is None  # Initially None
    
    @pytest.mark.asyncio
    async def test_get_available_tools_external(self, kafka_mcp_wrapper):
        """Test getting available tools when external server is available"""
    @pytest.mark.asyncio
    async def test_connect_direct_kafka(self, kafka_client):
        """Test connecting via direct kafka-python"""
        with patch('src.mcp.kafka_mcp_client.KAFKA_PYTHON_AVAILABLE', True):
            with patch.object(kafka_client, '_connect_native_kafka') as mock_connect:
                mock_connect.return_value = None
                result = await kafka_client.connect()
                assert result == True
                assert kafka_client.connected == True
    
    @pytest.mark.asyncio
    async def test_connect_http_fallback(self, kafka_client):
        """Test connecting via HTTP fallback"""
        with patch('src.mcp.kafka_mcp_client.KAFKA_PYTHON_AVAILABLE', False):
            with patch.object(kafka_client, '_connect_http') as mock_connect:
                mock_connect.return_value = None
                result = await kafka_client.connect()
                assert result == True
                assert kafka_client.connected == True
    
    @pytest.mark.asyncio
    async def test_customer_support_methods(self, kafka_client):
        """Test customer support specific methods"""
        # Mock successful connection
        kafka_client.connected = True
        
        with patch.object(kafka_client, 'call_tool') as mock_call:
            mock_call.return_value = {'success': True}
            
            # Test publish customer query
            query_data = {
                'query_id': 'test-123',
                'customer_id': 'cust-456',
                'query_text': 'Test query'
            }
            result = await kafka_client.publish_customer_query(query_data)
            assert result['success'] == True
            
            # Test create customer support topics
            result = await kafka_client.create_customer_support_topics()
            assert 'success' in result
    
    @pytest.mark.asyncio
    async def test_get_config_info(self, kafka_client):
        """Test getting client configuration"""
        assert kafka_client.bootstrap_servers == "localhost:9092"
        assert kafka_client.topic_prefix == "test"
        assert kafka_client.group_id == "test-group"
        
    @pytest.mark.asyncio
    async def test_disconnect(self, kafka_client):
        """Test disconnecting client"""
        kafka_client.connected = True
        await kafka_client.disconnect()
        assert kafka_client.connected == False
