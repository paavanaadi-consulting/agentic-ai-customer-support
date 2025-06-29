"""
Comprehensive unit tests for Kafka MCP Wrapper
"""
import pytest
import asyncio
import json
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from mcp.kafka_mcp_wrapper import KafkaMCPWrapper, ExternalKafkaMCPConfig

class TestKafkaMCPWrapper:
    """Test suite for Kafka MCP Wrapper"""
    
    @pytest.fixture
    def kafka_config(self):
        return ExternalKafkaMCPConfig(
            bootstrap_servers="localhost:9092",
            topic_name="test-topic",
            group_id="test-group",
            fallback_to_custom=True
        )
    
    @pytest.fixture
    def kafka_mcp_wrapper(self, kafka_config):
        return KafkaMCPWrapper(kafka_config)
    
    @pytest.mark.asyncio
    async def test_initialization(self, kafka_mcp_wrapper):
        """Test wrapper initialization"""
        assert kafka_mcp_wrapper.config.bootstrap_servers == "localhost:9092"
        assert kafka_mcp_wrapper.config.topic_name == "test-topic"
        assert kafka_mcp_wrapper.config.group_id == "test-group"
        assert kafka_mcp_wrapper.external_available == False  # Initially false
        assert kafka_mcp_wrapper.custom_server is None  # Initially None
    
    @pytest.mark.asyncio
    async def test_get_available_tools_external(self, kafka_mcp_wrapper):
        """Test getting available tools when external server is available"""
        kafka_mcp_wrapper.external_available = True
        
        tools = kafka_mcp_wrapper.get_available_tools()
        
        expected_tools = [
            'publish_message',
            'consume_messages', 
            'create_topic',
            'delete_topic',
            'list_topics',
            'get_topic_metadata',
            'get_topic_config',
            'cluster_health'
        ]
        assert tools == expected_tools
    
    @pytest.mark.asyncio
    async def test_get_available_tools_custom(self, kafka_mcp_wrapper):
        """Test getting available tools when using custom server"""
        kafka_mcp_wrapper.external_available = False
        kafka_mcp_wrapper.custom_server = Mock()
        
        tools = kafka_mcp_wrapper.get_available_tools()
        
        expected_tools = [
            'publish_message',
            'consume_messages',
            'get_topic_metadata',
            'list_topics'
        ]
        assert tools == expected_tools
    
    @pytest.mark.asyncio
    async def test_call_tool_no_server(self, kafka_mcp_wrapper):
        """Test calling tool when no server is available"""
        kafka_mcp_wrapper.external_available = False
        kafka_mcp_wrapper.custom_server = None
        
        with pytest.raises(RuntimeError, match="No Kafka MCP server available"):
            await kafka_mcp_wrapper.call_tool('publish_message', {'topic': 'test', 'message': 'hello'})
    
    def test_get_config_info(self, kafka_mcp_wrapper):
        """Test getting configuration information"""
        kafka_mcp_wrapper.external_available = True
        kafka_mcp_wrapper.custom_server = None
        
        config_info = kafka_mcp_wrapper.get_config_info()
        
        expected_info = {
            'external_available': True,
            'using_custom_fallback': False,
            'bootstrap_servers': 'localhost:9092',
            'topic_name': 'test-topic',
            'group_id': 'test-group'
        }
        assert config_info == expected_info
    
    def test_env_vars_setup(self, kafka_mcp_wrapper):
        """Test environment variables setup"""
        expected_env_vars = {
            "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
            "TOPIC_NAME": "test-topic",
            "DEFAULT_GROUP_ID_FOR_CONSUMER": "test-group",
            "IS_TOPIC_READ_FROM_BEGINNING": "False"
        }
        assert kafka_mcp_wrapper.env_vars == expected_env_vars
