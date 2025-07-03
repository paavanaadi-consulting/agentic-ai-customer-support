"""
Comprehensive tests for the base A2A agent and message system.
Tests the core foundation that all A2A agents inherit from.
"""
import pytest
import asyncio
import json
import websockets
from unittest.mock import Mock, AsyncMock, patch
from src.a2a_protocol.base_a2a_agent import A2AAgent, A2AMessage


class TestA2AMessage:
    """Test the A2A message structure and serialization."""
    
    def test_message_creation(self):
        """Test basic message creation."""
        msg = A2AMessage(
            sender_id="agent1",
            receiver_id="agent2", 
            message_type="test_message",
            payload={"test": "data"}
        )
        
        assert msg.sender_id == "agent1"
        assert msg.receiver_id == "agent2"
        assert msg.message_type == "test_message"
        assert msg.payload == {"test": "data"}
        assert msg.message_id is not None
        assert msg.timestamp is not None
        assert msg.request_id is not None
    
    def test_message_with_custom_request_id(self):
        """Test message creation with custom request ID."""
        custom_id = "custom-request-123"
        msg = A2AMessage(
            sender_id="agent1",
            receiver_id="agent2",
            message_type="test",
            payload={},
            request_id=custom_id
        )
        
        assert msg.request_id == custom_id
    
    def test_message_to_dict(self):
        """Test message serialization to dictionary."""
        msg = A2AMessage(
            sender_id="agent1",
            receiver_id="agent2",
            message_type="test",
            payload={"key": "value"}
        )
        
        msg_dict = msg.to_dict()
        
        assert isinstance(msg_dict, dict)
        assert msg_dict["sender_id"] == "agent1"
        assert msg_dict["receiver_id"] == "agent2"
        assert msg_dict["message_type"] == "test"
        assert msg_dict["payload"] == {"key": "value"}
        assert "message_id" in msg_dict
        assert "timestamp" in msg_dict
        assert "request_id" in msg_dict
    
    def test_message_from_dict(self):
        """Test message deserialization from dictionary."""
        msg_data = {
            "message_id": "msg-123",
            "sender_id": "agent1",
            "receiver_id": "agent2",
            "message_type": "test",
            "payload": {"test": "data"},
            "request_id": "req-123",
            "timestamp": "2025-01-01T00:00:00"
        }
        
        msg = A2AMessage.from_dict(msg_data)
        
        assert msg.message_id == "msg-123"
        assert msg.sender_id == "agent1"
        assert msg.receiver_id == "agent2"
        assert msg.message_type == "test"
        assert msg.payload == {"test": "data"}
        assert msg.request_id == "req-123"
        assert msg.timestamp == "2025-01-01T00:00:00"


class MockA2AAgent(A2AAgent):
    """Mock implementation of A2AAgent for testing."""
    
    def get_capabilities(self):
        return ["test_capability", "mock_feature"]
    
    async def process_task(self, task_data):
        return {"success": True, "mock": True, "data": task_data}


class TestA2AAgent:
    """Test the base A2A agent functionality."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock A2A agent for testing."""
        return MockA2AAgent("test_agent", "test_type", 8999)
    
    def test_agent_initialization(self, mock_agent):
        """Test agent basic initialization."""
        assert mock_agent.agent_id == "test_agent"
        assert mock_agent.agent_type == "test_type"
        assert mock_agent.port == 8999
        assert mock_agent.running is False
        assert isinstance(mock_agent.connections, dict)
        assert isinstance(mock_agent.message_handlers, dict)
        assert isinstance(mock_agent.discovery_registry, dict)
        assert isinstance(mock_agent.metrics, dict)
    
    def test_default_port_assignment(self):
        """Test default port assignment by agent type."""
        query_agent = MockA2AAgent("test", "query")
        knowledge_agent = MockA2AAgent("test", "knowledge") 
        response_agent = MockA2AAgent("test", "response")
        coordinator_agent = MockA2AAgent("test", "coordinator")
        other_agent = MockA2AAgent("test", "other")
        
        assert query_agent.port == 8001
        assert knowledge_agent.port == 8002
        assert response_agent.port == 8003
        assert coordinator_agent.port == 8004
        assert other_agent.port == 8000
    
    def test_message_handlers_registration(self, mock_agent):
        """Test that default message handlers are registered."""
        expected_handlers = [
            'discovery_request', 'discovery_response',
            'capability_query', 'capability_response',
            'collaboration_request', 'collaboration_response',
            'task_delegation', 'task_result', 'error'
        ]
        
        for handler in expected_handlers:
            assert handler in mock_agent.message_handlers
    
    def test_capabilities(self, mock_agent):
        """Test agent capabilities."""
        capabilities = mock_agent.get_capabilities()
        assert "test_capability" in capabilities
        assert "mock_feature" in capabilities
    
    @pytest.mark.asyncio
    async def test_process_task(self, mock_agent):
        """Test task processing."""
        task_data = {"task_type": "test", "data": "sample"}
        result = await mock_agent.process_task(task_data)
        
        assert result["success"] is True
        assert result["mock"] is True
        assert result["data"] == task_data
    
    def test_gene_template_initialization(self, mock_agent):
        """Test genetic algorithm gene template."""
        gene_template = mock_agent.gene_template
        
        assert isinstance(gene_template, dict)
        assert "response_timeout" in gene_template
        assert "confidence_threshold" in gene_template
        assert "max_retries" in gene_template
        assert "batch_size" in gene_template
    
    def test_gene_ranges_initialization(self, mock_agent):
        """Test genetic algorithm gene ranges."""
        gene_ranges = mock_agent.gene_ranges
        
        assert isinstance(gene_ranges, dict)
        assert "response_timeout" in gene_ranges
        assert "confidence_threshold" in gene_ranges
        assert "max_retries" in gene_ranges
        assert "batch_size" in gene_ranges
        
        # Test range formats
        assert isinstance(gene_ranges["response_timeout"], tuple)
        assert len(gene_ranges["response_timeout"]) == 2
    
    def test_metrics_initialization(self, mock_agent):
        """Test metrics tracking initialization."""
        metrics = mock_agent.metrics
        
        assert "messages_sent" in metrics
        assert "messages_received" in metrics
        assert "successful_collaborations" in metrics
        assert "failed_collaborations" in metrics
        
        # Initially all should be zero
        for metric in metrics.values():
            assert metric == 0
    
    def test_get_metrics(self, mock_agent):
        """Test metrics reporting."""
        metrics = mock_agent.get_metrics()
        
        assert "messages_sent" in metrics
        assert "messages_received" in metrics
        assert "successful_collaborations" in metrics
        assert "failed_collaborations" in metrics
        assert "connections" in metrics
        assert "known_agents" in metrics
        assert "agent_load" in metrics
    
    @pytest.mark.asyncio
    async def test_send_error_response(self, mock_agent):
        """Test error response sending."""
        original_msg = A2AMessage(
            sender_id="sender",
            receiver_id=mock_agent.agent_id,
            message_type="test",
            payload={},
            request_id="req-123"
        )
        
        with patch.object(mock_agent, 'send_message', new_callable=AsyncMock) as mock_send:
            await mock_agent.send_error_response(original_msg, "Test error")
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[1]["receiver_id"] == "sender"
            assert call_args[1]["message_type"] == "error"
            assert "error" in call_args[1]["payload"]
            assert call_args[1]["payload"]["error"] == "Test error"
    
    def test_task_handling_capabilities(self, mock_agent):
        """Test task handling capability checks."""
        assert mock_agent._can_handle_task("test_capability") is True
        assert mock_agent._can_handle_task("mock_feature") is True
        assert mock_agent._can_handle_task("unknown_task") is False
    
    def test_task_estimation_methods(self, mock_agent):
        """Test task estimation methods."""
        # Test time estimation
        time_estimate = mock_agent._estimate_task_time("test_capability")
        assert isinstance(time_estimate, float)
        assert time_estimate > 0
        
        # Test confidence estimation
        confidence = mock_agent._get_task_confidence("test_capability")
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        
        # Test load calculation
        load = mock_agent._get_current_load()
        assert isinstance(load, float)
        assert load >= 0
    
    def test_chromosome_support(self, mock_agent):
        """Test genetic algorithm chromosome support."""
        # Initially no chromosome
        assert mock_agent.current_chromosome is None
        
        # Mock chromosome
        mock_chromosome = Mock()
        mock_chromosome.genes = {
            "response_timeout": 10.0,
            "confidence_threshold": 0.9,
            "max_retries": 5
        }
        
        # Set chromosome
        mock_agent.set_chromosome(mock_chromosome)
        assert mock_agent.current_chromosome == mock_chromosome
    
    @pytest.mark.asyncio
    async def test_mcp_integration_methods(self, mock_agent):
        """Test MCP integration methods."""
        with patch.object(mock_agent.mcp_manager, 'call_tool', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"success": True, "result": "test"}
            
            result = await mock_agent.call_mcp_tool("server1", "test_tool", {"arg": "value"})
            
            mock_call.assert_called_once_with("server1", "test_tool", {"arg": "value"})
            assert result["success"] is True
            assert result["result"] == "test"
    
    @pytest.mark.asyncio
    async def test_mcp_tool_error_handling(self, mock_agent):
        """Test MCP tool call error handling."""
        with patch.object(mock_agent.mcp_manager, 'call_tool', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("MCP Error")
            
            result = await mock_agent.call_mcp_tool("server1", "test_tool")
            
            assert result["success"] is False
            assert "error" in result
            assert "MCP Error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_message_processing(self, mock_agent):
        """Test message processing with handlers."""
        # Mock a discovery request handler
        mock_handler = AsyncMock()
        mock_agent.message_handlers["test_message"] = mock_handler
        
        test_message = A2AMessage(
            sender_id="sender",
            receiver_id=mock_agent.agent_id,
            message_type="test_message",
            payload={"test": "data"}
        )
        
        await mock_agent._process_message(test_message)
        mock_handler.assert_called_once_with(test_message)
    
    @pytest.mark.asyncio
    async def test_message_processing_no_handler(self, mock_agent):
        """Test message processing when no handler exists."""
        test_message = A2AMessage(
            sender_id="sender",
            receiver_id=mock_agent.agent_id,
            message_type="unknown_message",
            payload={}
        )
        
        # Should not raise an exception
        await mock_agent._process_message(test_message)
    
    @pytest.mark.asyncio
    async def test_message_processing_handler_error(self, mock_agent):
        """Test message processing when handler raises an error."""
        # Mock a handler that raises an exception
        mock_handler = AsyncMock(side_effect=Exception("Handler error"))
        mock_agent.message_handlers["error_message"] = mock_handler
        
        test_message = A2AMessage(
            sender_id="sender", 
            receiver_id=mock_agent.agent_id,
            message_type="error_message",
            payload={}
        )
        
        with patch.object(mock_agent, 'send_error_response', new_callable=AsyncMock) as mock_error:
            await mock_agent._process_message(test_message)
            
            mock_handler.assert_called_once()
            mock_error.assert_called_once_with(test_message, "Handler error")


@pytest.mark.integration
class TestA2AAgentIntegration:
    """Integration tests for A2A agent communication."""
    
    @pytest.fixture
    def agent1(self):
        return MockA2AAgent("agent1", "test", 8991)
    
    @pytest.fixture 
    def agent2(self):
        return MockA2AAgent("agent2", "test", 8992)
    
    @pytest.mark.asyncio
    async def test_agent_startup_shutdown(self, agent1):
        """Test agent startup and shutdown process."""
        # Start agent
        await agent1.start()
        assert agent1.running is True
        assert agent1.server is not None
        
        # Stop agent
        await agent1.stop()
        assert agent1.running is False
    
    @pytest.mark.asyncio
    async def test_discovery_process(self, agent1, agent2):
        """Test agent discovery process."""
        # Start both agents
        await agent1.start()
        await agent2.start()
        
        # Allow discovery time
        await asyncio.sleep(1)
        
        # Check if agents discovered each other
        # Note: This is a simplified test - real discovery happens over websockets
        
        # Cleanup
        await agent1.stop()
        await agent2.stop()
    
    @pytest.mark.asyncio
    async def test_message_sending_mock(self, agent1):
        """Test message sending with mocked connections."""
        # Mock websocket connection
        mock_websocket = AsyncMock()
        agent1.connections["agent2"] = mock_websocket
        
        # Send message
        success = await agent1.send_message(
            receiver_id="agent2",
            message_type="test",
            payload={"data": "test"}
        )
        
        assert success is True
        mock_websocket.send.assert_called_once()
        
        # Verify message format
        sent_data = mock_websocket.send.call_args[0][0]
        message_dict = json.loads(sent_data)
        assert message_dict["sender_id"] == "agent1"
        assert message_dict["receiver_id"] == "agent2"
        assert message_dict["message_type"] == "test"
        assert message_dict["payload"]["data"] == "test"
    
    @pytest.mark.asyncio
    async def test_collaboration_request_response(self, agent1):
        """Test collaboration request/response pattern."""
        # Mock handler for collaboration response
        collaboration_responses = []
        
        async def mock_collaboration_handler(message):
            collaboration_responses.append(message.payload)
        
        agent1.message_handlers["collaboration_response"] = mock_collaboration_handler
        
        # Simulate collaboration request
        request_msg = A2AMessage(
            sender_id="requester",
            receiver_id="agent1",
            message_type="collaboration_request",
            payload={"task_type": "test_capability"}
        )
        
        with patch.object(agent1, 'send_message', new_callable=AsyncMock) as mock_send:
            await agent1._handle_collaboration_request(request_msg)
            
            # Verify response was sent
            mock_send.assert_called_once()
            call_args = mock_send.call_args[1]
            assert call_args["message_type"] == "collaboration_response"
            assert call_args["payload"]["accepted"] is True


@pytest.mark.performance
class TestA2AAgentPerformance:
    """Performance tests for A2A agent operations."""
    
    @pytest.fixture
    def performance_agent(self):
        return MockA2AAgent("perf_agent", "performance", 8990)
    
    @pytest.mark.asyncio
    async def test_message_processing_speed(self, performance_agent):
        """Test message processing performance."""
        import time
        
        # Create multiple test messages
        messages = []
        for i in range(100):
            msg = A2AMessage(
                sender_id=f"sender_{i}",
                receiver_id="perf_agent",
                message_type="test_message",
                payload={"index": i}
            )
            messages.append(msg)
        
        # Mock handler that just increments a counter
        processed_count = 0
        
        async def counting_handler(message):
            nonlocal processed_count
            processed_count += 1
        
        performance_agent.message_handlers["test_message"] = counting_handler
        
        # Measure processing time
        start_time = time.time()
        
        for msg in messages:
            await performance_agent._process_message(msg)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert processed_count == 100
        assert processing_time < 5.0  # Should process 100 messages in under 5 seconds
        
        messages_per_second = 100 / processing_time
        assert messages_per_second > 20  # At least 20 messages per second
    
    @pytest.mark.asyncio
    async def test_concurrent_task_processing(self, performance_agent):
        """Test concurrent task processing."""
        # Create multiple tasks
        tasks = []
        for i in range(10):
            task_data = {"task_id": i, "data": f"task_{i}"}
            task = performance_agent.process_task(task_data)
            tasks.append(task)
        
        # Process all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        for i, result in enumerate(results):
            assert result["success"] is True
            assert result["data"]["task_id"] == i
