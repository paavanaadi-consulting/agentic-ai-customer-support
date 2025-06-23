"""
Comprehensive unit tests for Kafka MCP Server
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from mcp.kafka_mcp_server import KafkaMCPServer

class TestKafkaMCPServer:
    """Test suite for Kafka MCP Server"""
    
    @pytest.fixture
    def kafka_mcp_server(self):
        return KafkaMCPServer("localhost:9092")
    
    @pytest.mark.asyncio
    async def test_initialization(self, kafka_mcp_server):
        """Test server initialization"""
        assert kafka_mcp_server.server_id == "mcp_kafka"
        assert kafka_mcp_server.name == "Kafka MCP Server"
        assert 'publish_message' in kafka_mcp_server.tools
        assert 'consume_messages' in kafka_mcp_server.tools
        assert 'kafka://topics' in kafka_mcp_server.resources
        assert kafka_mcp_server.bootstrap_servers == "localhost:9092"
    
    @pytest.mark.asyncio
    @patch('mcp.kafka_mcp_server.KafkaProducer')
    async def test_start_server(self, mock_producer_class, kafka_mcp_server):
        """Test server startup"""
        mock_producer = Mock()
        mock_producer_class.return_value = mock_producer
        
        await kafka_mcp_server.start()
        
        assert kafka_mcp_server.running is True
        assert kafka_mcp_server.producer is not None
        mock_producer_class.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('mcp.kafka_mcp_server.KafkaProducer')
    async def test_publish_message_tool(self, mock_producer_class, kafka_mcp_server):
        """Test publish_message tool"""
        mock_producer = Mock()
        mock_producer_class.return_value = mock_producer
        
        await kafka_mcp_server.start()
        
        result = await kafka_mcp_server.call_tool('publish_message', {
            'topic': 'test-topic',
            'message': {'text': 'Hello World'},
            'key': 'test-key'
        })
        
        assert result['success'] is True
        assert result['topic'] == 'test-topic'
        assert result['key'] == 'test-key'
        mock_producer.send.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('mcp.kafka_mcp_server.KafkaConsumer')
    async def test_consume_messages_tool(self, mock_consumer_class, kafka_mcp_server):
        """Test consume_messages tool"""
        # Setup mock consumer
        mock_consumer = Mock()
        mock_message = Mock()
        mock_message.topic = 'test-topic'
        mock_message.partition = 0
        mock_message.offset = 1
        mock_message.key = b'test-key'
        mock_message.value = b'{"text": "Hello World"}'
        mock_message.timestamp = 1624464000000
        
        mock_consumer.__iter__ = Mock(return_value=iter([mock_message]))
        mock_consumer_class.return_value = mock_consumer
        
        result = await kafka_mcp_server.call_tool('consume_messages', {
            'topic': 'test-topic',
            'group_id': 'test-group',
            'max_messages': 1
        })
        
        assert result['success'] is True
        assert len(result['messages']) == 1
        assert result['messages'][0]['topic'] == 'test-topic'
    
    @pytest.mark.asyncio
    @patch('mcp.kafka_mcp_server.KafkaConsumer')
    async def test_get_topic_metadata_tool(self, mock_consumer_class, kafka_mcp_server):
        """Test get_topic_metadata tool"""
        mock_consumer = Mock()
        mock_metadata = {
            'test-topic': Mock(partitions={0: Mock(leader=1), 1: Mock(leader=2)})
        }
        mock_consumer.list_consumer_group_offsets.return_value = {}
        mock_consumer_class.return_value = mock_consumer
        
        with patch.object(kafka_mcp_server, '_get_cluster_metadata', return_value=mock_metadata):
            result = await kafka_mcp_server.call_tool('get_topic_metadata', {
                'topic': 'test-topic'
            })
            
            assert result['success'] is True
            assert result['topic'] == 'test-topic'
            assert 'partitions' in result
    
    @pytest.mark.asyncio
    async def test_unknown_tool(self, kafka_mcp_server):
        """Test handling of unknown tools"""
        result = await kafka_mcp_server.call_tool('unknown_tool', {})
        
        assert result['success'] is False
        assert 'Unknown tool' in result['error']
    
    @pytest.mark.asyncio
    @patch('mcp.kafka_mcp_server.KafkaProducer')
    async def test_kafka_error_handling(self, mock_producer_class, kafka_mcp_server):
        """Test Kafka error handling"""
        mock_producer = Mock()
        mock_producer.send.side_effect = Exception("Kafka connection failed")
        mock_producer_class.return_value = mock_producer
        
        await kafka_mcp_server.start()
        
        result = await kafka_mcp_server.call_tool('publish_message', {
            'topic': 'test-topic',
            'message': {'text': 'Hello World'}
        })
        
        assert result['success'] is False
        assert 'Kafka connection failed' in result['error']
    
    @pytest.mark.asyncio
    @patch('mcp.kafka_mcp_server.KafkaConsumer')
    async def test_get_resource_topics(self, mock_consumer_class, kafka_mcp_server):
        """Test getting topics resource"""
        mock_consumer = Mock()
        mock_consumer.topics.return_value = {'topic1', 'topic2', 'topic3'}
        mock_consumer_class.return_value = mock_consumer
        
        result = await kafka_mcp_server.get_resource('kafka://topics')
        
        assert result['success'] is True
        assert len(result['contents']) == 1
        assert result['contents'][0]['mimeType'] == 'application/json'
    
    @pytest.mark.asyncio
    async def test_get_unknown_resource(self, kafka_mcp_server):
        """Test getting unknown resource"""
        result = await kafka_mcp_server.get_resource('kafka://unknown')
        
        assert result['success'] is False
        assert 'Unknown resource' in result['error']
    
    @pytest.mark.asyncio
    async def test_tool_definitions(self, kafka_mcp_server):
        """Test tool definitions"""
        publish_def = await kafka_mcp_server._get_tool_definition('publish_message')
        
        assert publish_def is not None
        assert publish_def['name'] == 'publish_message'
        assert 'inputSchema' in publish_def
        assert 'topic' in publish_def['inputSchema']['properties']
        assert 'message' in publish_def['inputSchema']['properties']
