"""
Enhanced comprehensive tests for A2A Coordinator.
Tests workflow orchestration, agent coordination, and complex scenarios.
"""
import pytest
import asyncio
import uuid
from unittest.mock import Mock, AsyncMock, patch
from src.a2a_protocol.a2a_coordinator import A2ACoordinator


class TestA2ACoordinatorEnhanced:
    """Enhanced tests for A2A Coordinator functionality."""
    
    @pytest.fixture
    def coordinator(self):
        """Create a coordinator for testing."""
        return A2ACoordinator("test_coordinator")
    
    def test_coordinator_initialization(self, coordinator):
        """Test coordinator initialization."""
        assert coordinator.agent_id == "test_coordinator"
        assert coordinator.agent_type == "coordinator"
        assert coordinator.port == 8004
        assert isinstance(coordinator.active_workflows, dict)
        assert isinstance(coordinator.workflow_results, dict)
    
    def test_coordinator_capabilities(self, coordinator):
        """Test coordinator capabilities."""
        capabilities = coordinator.get_capabilities()
        expected_capabilities = [
            'workflow_orchestration',
            'agent_discovery', 
            'load_balancing',
            'task_routing',
            'result_aggregation'
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities
    
    def test_coordinator_message_handlers(self, coordinator):
        """Test coordinator message handlers registration."""
        expected_handlers = [
            'start_workflow',
            'workflow_complete', 
            'agent_status_update'
        ]
        
        for handler in expected_handlers:
            assert handler in coordinator.message_handlers
    
    @pytest.mark.asyncio
    async def test_health_check_task(self, coordinator):
        """Test health check task processing."""
        task_data = {"task_type": "agent_health_check"}
        result = await coordinator.process_task(task_data)
        
        assert result["status"] == "healthy"
        assert result["a2a_enabled"] is True
    
    @pytest.mark.asyncio
    async def test_unsupported_task_type(self, coordinator):
        """Test handling of unsupported task types."""
        task_data = {"task_type": "unknown_task"}
        
        with pytest.raises(ValueError) as exc_info:
            await coordinator.process_task(task_data)
        
        assert "Unsupported task type" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_customer_support_workflow_minimal(self, coordinator):
        """Test minimal customer support workflow."""
        task_data = {
            "task_type": "customer_support_workflow",
            "query_data": {
                "query": "Test query",
                "api_key": "test-key"
            }
        }
        
        # Mock the agent classes to avoid external dependencies
        with patch('src.a2a_protocol.a2a_coordinator.A2AQueryAgent') as mock_query, \
             patch('src.a2a_protocol.a2a_coordinator.A2AKnowledgeAgent') as mock_knowledge, \
             patch('src.a2a_protocol.a2a_coordinator.A2AResponseAgent') as mock_response:
            
            # Mock agent instances and their process_task methods
            mock_query_instance = AsyncMock()
            mock_query_instance.process_task.return_value = {
                "success": True,
                "analysis": "Test analysis"
            }
            mock_query.return_value = mock_query_instance
            
            mock_knowledge_instance = AsyncMock()
            mock_knowledge_instance.process_task.return_value = {
                "success": True,
                "knowledge": "Test knowledge"
            }
            mock_knowledge.return_value = mock_knowledge_instance
            
            mock_response_instance = AsyncMock()
            mock_response_instance.process_task.return_value = {
                "success": True,
                "response": "Test response"
            }
            mock_response.return_value = mock_response_instance
            
            result = await coordinator._orchestrate_support_workflow(task_data)
            
            assert result["success"] is True
            assert "workflow_id" in result
            assert "query_analysis" in result
            assert "knowledge_result" in result
            assert "response_result" in result
            assert result["total_agents_used"] == 3
    
    @pytest.mark.asyncio
    async def test_workflow_with_llm_providers(self, coordinator):
        """Test workflow with different LLM providers."""
        providers = ["openai", "gemini", "claude"]
        
        for provider in providers:
            task_data = {
                "task_type": "customer_support_workflow",
                "query_data": {
                    "query": f"Test query for {provider}",
                    "llm_provider": provider,
                    "api_key": f"test-{provider}-key"
                }
            }
            
            with patch('src.a2a_protocol.a2a_coordinator.A2AQueryAgent') as mock_query, \
                 patch('src.a2a_protocol.a2a_coordinator.A2AKnowledgeAgent') as mock_knowledge, \
                 patch('src.a2a_protocol.a2a_coordinator.A2AResponseAgent') as mock_response:
                
                # Setup mocks
                for mock_class in [mock_query, mock_knowledge, mock_response]:
                    mock_instance = AsyncMock()
                    mock_instance.process_task.return_value = {"success": True}
                    mock_class.return_value = mock_instance
                
                result = await coordinator._orchestrate_support_workflow(task_data)
                
                assert result["success"] is True
                assert "workflow_id" in result
    
    @pytest.mark.asyncio
    async def test_workflow_with_mcp_clients(self, coordinator):
        """Test workflow with MCP client integration."""
        task_data = {
            "task_type": "customer_support_workflow",
            "query_data": {
                "query": "Test query with MCP",
                "api_key": "test-key",
                "mcp_clients": {
                    "postgres": "postgres_client",
                    "kafka": "kafka_client"
                },
                "context": {
                    "customer_id": "12345",
                    "session_id": "session_123"
                }
            }
        }
        
        with patch('src.a2a_protocol.a2a_coordinator.A2AQueryAgent') as mock_query, \
             patch('src.a2a_protocol.a2a_coordinator.A2AKnowledgeAgent') as mock_knowledge, \
             patch('src.a2a_protocol.a2a_coordinator.A2AResponseAgent') as mock_response:
            
            # Setup mocks
            for mock_class in [mock_query, mock_knowledge, mock_response]:
                mock_instance = AsyncMock()
                mock_instance.process_task.return_value = {"success": True}
                mock_class.return_value = mock_instance
            
            result = await coordinator._orchestrate_support_workflow(task_data)
            
            assert result["success"] is True
            
            # Verify MCP clients were passed to agents
            for mock_class in [mock_query, mock_knowledge, mock_response]:
                mock_class.assert_called_once()
                call_kwargs = mock_class.call_args[1]
                assert "mcp_clients" in call_kwargs
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, coordinator):
        """Test workflow error handling when agents fail."""
        task_data = {
            "task_type": "customer_support_workflow", 
            "query_data": {
                "query": "Test query",
                "api_key": "test-key"
            }
        }
        
        with patch('src.a2a_protocol.a2a_coordinator.A2AQueryAgent') as mock_query:
            # Mock query agent to raise an exception
            mock_query.side_effect = Exception("Query agent failed")
            
            result = await coordinator._orchestrate_support_workflow(task_data)
            
            assert result["success"] is False
            assert "error" in result
            assert "Query agent failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_workflow_agent_processing_error(self, coordinator):
        """Test workflow handling when agent processing fails."""
        task_data = {
            "task_type": "customer_support_workflow",
            "query_data": {
                "query": "Test query",
                "api_key": "test-key"
            }
        }
        
        with patch('src.a2a_protocol.a2a_coordinator.A2AQueryAgent') as mock_query, \
             patch('src.a2a_protocol.a2a_coordinator.A2AKnowledgeAgent') as mock_knowledge, \
             patch('src.a2a_protocol.a2a_coordinator.A2AResponseAgent') as mock_response:
            
            # Query agent succeeds
            mock_query_instance = AsyncMock()
            mock_query_instance.process_task.return_value = {"success": True}
            mock_query.return_value = mock_query_instance
            
            # Knowledge agent fails
            mock_knowledge_instance = AsyncMock()
            mock_knowledge_instance.process_task.side_effect = Exception("Knowledge retrieval failed")
            mock_knowledge.return_value = mock_knowledge_instance
            
            # Response agent setup (won't be reached)
            mock_response_instance = AsyncMock()
            mock_response.return_value = mock_response_instance
            
            result = await coordinator._orchestrate_support_workflow(task_data)
            
            assert result["success"] is False
            assert "error" in result
            assert "Agent processing error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_workflow_custom_models(self, coordinator):
        """Test workflow with custom LLM models."""
        task_data = {
            "task_type": "customer_support_workflow",
            "query_data": {
                "query": "Test query",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "api_key": "test-key"
            }
        }
        
        with patch('src.a2a_protocol.a2a_coordinator.A2AQueryAgent') as mock_query, \
             patch('src.a2a_protocol.a2a_coordinator.A2AKnowledgeAgent') as mock_knowledge, \
             patch('src.a2a_protocol.a2a_coordinator.A2AResponseAgent') as mock_response:
            
            # Setup mocks
            for mock_class in [mock_query, mock_knowledge, mock_response]:
                mock_instance = AsyncMock()
                mock_instance.process_task.return_value = {"success": True}
                mock_class.return_value = mock_instance
            
            result = await coordinator._orchestrate_support_workflow(task_data)
            
            assert result["success"] is True
            
            # Verify custom model was passed to agents
            for mock_class in [mock_query, mock_knowledge, mock_response]:
                mock_instance = mock_class.return_value
                process_task_call = mock_instance.process_task.call_args[0][0]
                assert process_task_call.get("llm_model") == "gpt-4"
    
    @pytest.mark.asyncio
    async def test_workflow_result_structure(self, coordinator):
        """Test workflow result structure and completeness."""
        task_data = {
            "task_type": "customer_support_workflow",
            "query_data": {
                "query": "Comprehensive test query",
                "customer_id": "test_customer_123",
                "api_key": "test-key"
            }
        }
        
        with patch('src.a2a_protocol.a2a_coordinator.A2AQueryAgent') as mock_query, \
             patch('src.a2a_protocol.a2a_coordinator.A2AKnowledgeAgent') as mock_knowledge, \
             patch('src.a2a_protocol.a2a_coordinator.A2AResponseAgent') as mock_response:
            
            # Setup detailed mock responses
            mock_query_instance = AsyncMock()
            mock_query_instance.process_task.return_value = {
                "success": True,
                "analysis": "Detailed query analysis",
                "intent": "help_request",
                "category": "technical"
            }
            mock_query.return_value = mock_query_instance
            
            mock_knowledge_instance = AsyncMock()
            mock_knowledge_instance.process_task.return_value = {
                "success": True,
                "knowledge_base": "Retrieved knowledge",
                "confidence": 0.85,
                "sources": ["kb_article_1", "kb_article_2"]
            }
            mock_knowledge.return_value = mock_knowledge_instance
            
            mock_response_instance = AsyncMock()
            mock_response_instance.process_task.return_value = {
                "success": True,
                "response": "Generated response text",
                "tone": "helpful",
                "confidence": 0.92
            }
            mock_response.return_value = mock_response_instance
            
            result = await coordinator._orchestrate_support_workflow(task_data)
            
            # Verify result structure
            assert result["success"] is True
            assert isinstance(result["workflow_id"], str)
            assert len(result["workflow_id"]) > 0
            
            assert "query_analysis" in result
            assert result["query_analysis"]["success"] is True
            assert "analysis" in result["query_analysis"]
            
            assert "knowledge_result" in result
            assert result["knowledge_result"]["success"] is True
            assert "knowledge_base" in result["knowledge_result"]
            
            assert "response_result" in result
            assert result["response_result"]["success"] is True
            assert "response" in result["response_result"]
            
            assert result["total_agents_used"] == 3
            assert result["coordination_overhead"] == "minimal"
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_workflows(self, coordinator):
        """Test handling multiple concurrent workflows."""
        tasks = []
        
        for i in range(5):
            task_data = {
                "task_type": "customer_support_workflow",
                "query_data": {
                    "query": f"Test query {i}",
                    "customer_id": f"customer_{i}",
                    "api_key": "test-key"
                }
            }
            tasks.append(task_data)
        
        with patch('src.a2a_protocol.a2a_coordinator.A2AQueryAgent') as mock_query, \
             patch('src.a2a_protocol.a2a_coordinator.A2AKnowledgeAgent') as mock_knowledge, \
             patch('src.a2a_protocol.a2a_coordinator.A2AResponseAgent') as mock_response:
            
            # Setup mocks
            for mock_class in [mock_query, mock_knowledge, mock_response]:
                mock_instance = AsyncMock()
                mock_instance.process_task.return_value = {"success": True}
                mock_class.return_value = mock_instance
            
            # Process workflows concurrently
            workflow_tasks = [
                coordinator._orchestrate_support_workflow(task) 
                for task in tasks
            ]
            
            results = await asyncio.gather(*workflow_tasks)
            
            assert len(results) == 5
            workflow_ids = set()
            
            for result in results:
                assert result["success"] is True
                assert "workflow_id" in result
                workflow_ids.add(result["workflow_id"])
            
            # All workflows should have unique IDs
            assert len(workflow_ids) == 5
    
    @pytest.mark.asyncio 
    async def test_workflow_logging(self, coordinator):
        """Test workflow logging and tracing."""
        task_data = {
            "task_type": "customer_support_workflow",
            "query_data": {
                "query": "Test query for logging",
                "api_key": "test-key"
            }
        }
        
        with patch('src.a2a_protocol.a2a_coordinator.A2AQueryAgent') as mock_query, \
             patch('src.a2a_protocol.a2a_coordinator.A2AKnowledgeAgent') as mock_knowledge, \
             patch('src.a2a_protocol.a2a_coordinator.A2AResponseAgent') as mock_response, \
             patch.object(coordinator.logger, 'info') as mock_log_info, \
             patch.object(coordinator.logger, 'error') as mock_log_error:
            
            # Setup successful mocks
            for mock_class in [mock_query, mock_knowledge, mock_response]:
                mock_instance = AsyncMock()
                mock_instance.process_task.return_value = {"success": True}
                mock_class.return_value = mock_instance
            
            result = await coordinator._orchestrate_support_workflow(task_data)
            
            assert result["success"] is True
            
            # Verify logging calls
            mock_log_info.assert_called()
            
            # Check for start and completion logs
            log_calls = [call.args[0] for call in mock_log_info.call_args_list]
            start_logged = any("Starting support workflow" in msg for msg in log_calls)
            complete_logged = any("Completed support workflow" in msg for msg in log_calls)
            
            assert start_logged
            assert complete_logged
    
    @pytest.mark.asyncio
    async def test_message_handlers(self, coordinator):
        """Test coordinator message handlers."""
        # Test workflow start handler
        start_message = Mock()
        start_message.payload = {"workflow_type": "test"}
        await coordinator._handle_workflow_start(start_message)
        
        # Test workflow complete handler
        complete_message = Mock()
        complete_message.payload = {"workflow_id": "test_id", "result": "success"}
        await coordinator._handle_workflow_complete(complete_message)
        
        # Test agent status update handler
        status_message = Mock()
        status_message.payload = {"agent_id": "test_agent", "status": "healthy"}
        await coordinator._handle_agent_status_update(status_message)
        
        # These methods are currently no-ops, so just verify they don't crash
        assert True


@pytest.mark.integration
class TestA2ACoordinatorIntegration:
    """Integration tests for A2A Coordinator."""
    
    @pytest.fixture
    def integration_coordinator(self):
        return A2ACoordinator("integration_coordinator")
    
    @pytest.mark.asyncio
    async def test_coordinator_startup_shutdown(self, integration_coordinator):
        """Test coordinator startup and shutdown."""
        await integration_coordinator.start()
        assert integration_coordinator.running is True
        
        await integration_coordinator.stop()
        assert integration_coordinator.running is False
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow_mock(self, integration_coordinator):
        """Test end-to-end workflow with comprehensive mocking."""
        # Start coordinator
        await integration_coordinator.start()
        
        try:
            # Process a complete workflow
            task_data = {
                "task_type": "customer_support_workflow",
                "query_data": {
                    "query": "I need help with my account",
                    "customer_id": "integration_test_123",
                    "api_key": "test-integration-key",
                    "context": {
                        "previous_interactions": 2,
                        "customer_tier": "premium"
                    }
                }
            }
            
            with patch('src.a2a_protocol.a2a_coordinator.A2AQueryAgent') as mock_query, \
                 patch('src.a2a_protocol.a2a_coordinator.A2AKnowledgeAgent') as mock_knowledge, \
                 patch('src.a2a_protocol.a2a_coordinator.A2AResponseAgent') as mock_response:
                
                # Setup realistic mock responses
                mock_query_instance = AsyncMock()
                mock_query_instance.process_task.return_value = {
                    "success": True,
                    "analysis": "Account access inquiry", 
                    "intent": "account_help",
                    "urgency": "medium",
                    "category": "account_management"
                }
                mock_query.return_value = mock_query_instance
                
                mock_knowledge_instance = AsyncMock()
                mock_knowledge_instance.process_task.return_value = {
                    "success": True,
                    "knowledge": "Account help documentation",
                    "relevant_articles": ["account_recovery", "login_help"],
                    "confidence": 0.88
                }
                mock_knowledge.return_value = mock_knowledge_instance
                
                mock_response_instance = AsyncMock()
                mock_response_instance.process_task.return_value = {
                    "success": True,
                    "response": "I'd be happy to help you with your account. Let me guide you through the account recovery process.",
                    "tone": "helpful_professional",
                    "personalized": True
                }
                mock_response.return_value = mock_response_instance
                
                result = await integration_coordinator.process_task(task_data)
                
                # Verify complete workflow execution
                assert result["success"] is True
                assert result["total_agents_used"] == 3
                
                # Verify each agent was called correctly
                mock_query_instance.process_task.assert_called_once()
                mock_knowledge_instance.process_task.assert_called_once()
                mock_response_instance.process_task.assert_called_once()
                
                # Verify data flow between agents
                knowledge_call_args = mock_knowledge_instance.process_task.call_args[0][0]
                assert "customer_id" in knowledge_call_args
                assert knowledge_call_args["customer_id"] == "integration_test_123"
                
                response_call_args = mock_response_instance.process_task.call_args[0][0]
                assert "query_analysis" in response_call_args
                assert "knowledge_result" in response_call_args
        
        finally:
            await integration_coordinator.stop()


@pytest.mark.performance
class TestA2ACoordinatorPerformance:
    """Performance tests for A2A Coordinator."""
    
    @pytest.fixture
    def perf_coordinator(self):
        return A2ACoordinator("perf_coordinator")
    
    @pytest.mark.asyncio
    async def test_workflow_processing_speed(self, perf_coordinator):
        """Test workflow processing performance."""
        import time
        
        task_data = {
            "task_type": "customer_support_workflow",
            "query_data": {
                "query": "Performance test query",
                "api_key": "perf-test-key"
            }
        }
        
        with patch('src.a2a_protocol.a2a_coordinator.A2AQueryAgent') as mock_query, \
             patch('src.a2a_protocol.a2a_coordinator.A2AKnowledgeAgent') as mock_knowledge, \
             patch('src.a2a_protocol.a2a_coordinator.A2AResponseAgent') as mock_response:
            
            # Setup fast-responding mocks
            for mock_class in [mock_query, mock_knowledge, mock_response]:
                mock_instance = AsyncMock()
                mock_instance.process_task.return_value = {"success": True}
                mock_class.return_value = mock_instance
            
            # Measure single workflow time
            start_time = time.time()
            result = await perf_coordinator._orchestrate_support_workflow(task_data)
            end_time = time.time()
            
            workflow_time = end_time - start_time
            
            assert result["success"] is True
            assert workflow_time < 1.0  # Should complete in under 1 second
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_performance(self, perf_coordinator):
        """Test concurrent workflow processing performance."""
        import time
        
        # Create multiple workflow tasks
        tasks = []
        for i in range(10):
            task_data = {
                "task_type": "customer_support_workflow",
                "query_data": {
                    "query": f"Concurrent test query {i}",
                    "api_key": "perf-test-key"
                }
            }
            tasks.append(task_data)
        
        with patch('src.a2a_protocol.a2a_coordinator.A2AQueryAgent') as mock_query, \
             patch('src.a2a_protocol.a2a_coordinator.A2AKnowledgeAgent') as mock_knowledge, \
             patch('src.a2a_protocol.a2a_coordinator.A2AResponseAgent') as mock_response:
            
            # Setup mocks
            for mock_class in [mock_query, mock_knowledge, mock_response]:
                mock_instance = AsyncMock()
                mock_instance.process_task.return_value = {"success": True}
                mock_class.return_value = mock_instance
            
            # Process workflows concurrently
            start_time = time.time()
            
            workflow_tasks = [
                perf_coordinator._orchestrate_support_workflow(task)
                for task in tasks
            ]
            
            results = await asyncio.gather(*workflow_tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            assert len(results) == 10
            assert all(result["success"] for result in results)
            assert total_time < 5.0  # Should complete 10 workflows in under 5 seconds
            
            workflows_per_second = 10 / total_time
            assert workflows_per_second > 2  # At least 2 workflows per second
