"""
Integration tests for A2A module
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import AsyncMock, Mock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from a2a_protocol.base_a2a_agent import A2AAgent, A2AMessage
from scripts.test_a2a_local import TestQueryAgent, TestKnowledgeAgent, TestResponseAgent

class TestA2AIntegration:
    """Integration tests for A2A protocol"""
    
    @pytest.fixture
    def mcp_config(self):
        return {
            "servers": {
                "mcp_database": {"uri": "ws://localhost:8001"},
                "mcp_kafka": {"uri": "ws://localhost:8002"}
            }
        }
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_agent_initialization(self, mcp_config):
        """Test that agents can be initialized properly"""
        agent = TestQueryAgent("test-query-agent", mcp_config)
        
        assert agent.agent_id == "test-query-agent"
        assert agent.agent_type == "query"
        assert agent.mcp_config == mcp_config
        
        # Test start/stop
        await agent.start()
        assert agent.running is True
        
        await agent.stop()
        assert agent.running is False
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_message_creation(self):
        """Test A2A message creation and serialization"""
        message = A2AMessage(
            sender_id="test-sender",
            receiver_id="test-receiver",
            message_type="test_message",
            payload={"test": "data"}
        )
        
        assert message.sender_id == "test-sender"
        assert message.receiver_id == "test-receiver"
        assert message.message_type == "test_message"
        assert message.payload == {"test": "data"}
        
        # Test serialization
        message_dict = message.to_dict()
        assert "message_id" in message_dict
        assert "timestamp" in message_dict
        
        # Test deserialization
        restored_message = A2AMessage.from_dict(message_dict)
        assert restored_message.sender_id == message.sender_id
        assert restored_message.payload == message.payload
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_query_processing(self, mcp_config):
        """Test query processing without MCP dependencies"""
        agent = TestQueryAgent("test-query-agent", mcp_config)
        
        # Mock MCP manager to avoid actual connections
        agent.mcp_manager = Mock()
        agent.mcp_manager.clients = {}
        
        await agent.start()
        
        try:
            result = await agent.process_customer_query(
                "Test query", 
                "test_customer_123"
            )
            
            assert result["success"] is True
            assert "query_id" in result
            assert len(agent.processed_queries) == 1
            
        finally:
            await agent.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_agent_communication_mock(self, mcp_config):
        """Test agent communication with mocked websockets"""
        query_agent = TestQueryAgent("query-agent-1", mcp_config)
        knowledge_agent = TestKnowledgeAgent("knowledge-agent-1", mcp_config)
        
        # Mock MCP managers
        query_agent.mcp_manager = Mock()
        query_agent.mcp_manager.clients = {}
        knowledge_agent.mcp_manager = Mock()
        knowledge_agent.mcp_manager.clients = {}
        
        # Mock websocket connections
        query_agent.send_message = AsyncMock()
        knowledge_agent.send_message = AsyncMock()
        
        await query_agent.start()
        await knowledge_agent.start()
        
        try:
            # Process a query
            await query_agent.process_customer_query(
                "How do I reset my password?", 
                "test_customer_456"
            )
            
            # Verify query was processed
            assert len(query_agent.processed_queries) == 1
            
            # Verify message was sent
            query_agent.send_message.assert_called_once()
            call_args = query_agent.send_message.call_args[0][0]
            assert call_args.message_type == "query_analysis"
            assert call_args.receiver_id == "knowledge-agent-1"
            
        finally:
            await query_agent.stop()
            await knowledge_agent.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_message_handling(self, mcp_config):
        """Test message handling in agents"""
        knowledge_agent = TestKnowledgeAgent("knowledge-agent-1", mcp_config)
        
        # Mock MCP manager
        knowledge_agent.mcp_manager = Mock()
        knowledge_agent.mcp_manager.clients = {}
        knowledge_agent.send_message = AsyncMock()
        
        await knowledge_agent.start()
        
        try:
            # Create test message
            test_message = A2AMessage(
                sender_id="query-agent-1",
                receiver_id="knowledge-agent-1",
                message_type="query_analysis",
                payload={
                    "query": "How do I reset my password?",
                    "customer_id": "test_customer_789"
                }
            )
            
            # Process message
            await knowledge_agent._process_message(test_message)
            
            # Verify analysis was performed
            assert len(knowledge_agent.analyzed_queries) == 1
            
            # Verify response was sent
            knowledge_agent.send_message.assert_called_once()
            
        finally:
            await knowledge_agent.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_response_generation(self, mcp_config):
        """Test response generation in response agent"""
        response_agent = TestResponseAgent("response-agent-1", mcp_config)
        
        # Mock MCP manager
        response_agent.mcp_manager = Mock()
        response_agent.mcp_manager.clients = {}
        response_agent.send_message = AsyncMock()
        
        await response_agent.start()
        
        try:
            # Create test message
            test_message = A2AMessage(
                sender_id="knowledge-agent-1",
                receiver_id="response-agent-1",
                message_type="generate_response",
                payload={
                    "original_query": "How do I reset my password?",
                    "customer_id": "test_customer_999",
                    "intent": "password_reset",
                    "confidence": 0.95
                }
            )
            
            # Process message
            await response_agent._process_message(test_message)
            
            # Verify response was generated
            assert len(response_agent.generated_responses) == 1
            
            generated_response = response_agent.generated_responses[0]
            assert "password" in generated_response["response"].lower()
            assert generated_response["customer_id"] == "test_customer_999"
            
            # Verify response was sent back
            response_agent.send_message.assert_called_once()
            
        finally:
            await response_agent.stop()


class TestA2AMockIntegration:
    """Test A2A integration with completely mocked dependencies"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_mock(self):
        """Test the complete A2A pipeline with mocked components"""
        # Create agents with mocked dependencies
        query_agent = TestQueryAgent("query-1")
        knowledge_agent = TestKnowledgeAgent("knowledge-1") 
        response_agent = TestResponseAgent("response-1")
        
        # Mock all external dependencies
        for agent in [query_agent, knowledge_agent, response_agent]:
            agent.mcp_manager = Mock()
            agent.mcp_manager.clients = {}
            agent.send_message = AsyncMock()
            agent.start = AsyncMock()
            agent.stop = AsyncMock()
        
        await query_agent.start()
        await knowledge_agent.start()
        await response_agent.start()
        
        try:
            # Simulate the full pipeline
            
            # 1. Query processing
            query_result = await query_agent.process_customer_query(
                "I forgot my password", 
                "customer_123"
            )
            assert query_result["success"] is True
            
            # 2. Knowledge analysis (simulate)
            query_message = A2AMessage(
                sender_id="query-1",
                receiver_id="knowledge-1", 
                message_type="query_analysis",
                payload={
                    "query": "I forgot my password",
                    "customer_id": "customer_123"
                }
            )
            await knowledge_agent._process_message(query_message)
            
            # 3. Response generation (simulate)
            analysis_message = A2AMessage(
                sender_id="knowledge-1",
                receiver_id="response-1",
                message_type="generate_response", 
                payload={
                    "original_query": "I forgot my password",
                    "customer_id": "customer_123",
                    "intent": "password_reset"
                }
            )
            await response_agent._process_message(analysis_message)
            
            # Verify end-to-end processing
            assert len(query_agent.processed_queries) == 1
            assert len(knowledge_agent.analyzed_queries) == 1
            assert len(response_agent.generated_responses) == 1
            
            # Verify response content
            final_response = response_agent.generated_responses[0]
            assert "password" in final_response["response"].lower()
            assert final_response["customer_id"] == "customer_123"
            
        finally:
            await query_agent.stop()
            await knowledge_agent.stop()
            await response_agent.stop()
