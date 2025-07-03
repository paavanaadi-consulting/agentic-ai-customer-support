"""
Tests for SimplifiedGeneticAISystem and A2A protocol integration.
Tests the complete system initialization and workflow execution.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.a2a_protocol.simplified_main import SimplifiedGeneticAISystem


class TestSimplifiedGeneticAISystem:
    """Test the SimplifiedGeneticAISystem integration."""
    
    @pytest.fixture
    def ai_system(self):
        """Create AI system for testing."""
        return SimplifiedGeneticAISystem()
    
    def test_system_initialization(self, ai_system):
        """Test system basic initialization."""
        assert ai_system.coordinator is None
        assert isinstance(ai_system.agents, dict)
        assert ai_system.initialized is False
        assert ai_system.logger is not None
    
    @pytest.mark.asyncio
    async def test_system_initialization_success(self, ai_system):
        """Test successful system initialization."""
        with patch('src.a2a_protocol.simplified_main.A2ACoordinator') as mock_coordinator, \
             patch.object(ai_system, '_initialize_agents', new_callable=AsyncMock) as mock_init_agents:
            
            # Mock coordinator
            mock_coordinator_instance = AsyncMock()
            mock_coordinator.return_value = mock_coordinator_instance
            
            await ai_system.initialize()
            
            assert ai_system.coordinator is not None
            assert ai_system.initialized is True
            mock_coordinator_instance.start.assert_called_once()
            mock_init_agents.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_system_initialization_failure(self, ai_system):
        """Test system initialization failure handling."""
        with patch('src.a2a_protocol.simplified_main.A2ACoordinator') as mock_coordinator:
            # Mock coordinator to raise exception
            mock_coordinator.side_effect = Exception("Initialization failed")
            
            await ai_system.initialize()
            
            assert ai_system.coordinator is None
            assert ai_system.initialized is False
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, ai_system):
        """Test agent initialization process."""
        # Create a mock _initialize_agents method for testing
        ai_system.coordinator = Mock()
        
        # Mock the agents that would be created
        mock_query_agent = AsyncMock()
        mock_knowledge_agent = AsyncMock()
        mock_response_agent = AsyncMock()
        
        with patch('src.a2a_protocol.a2a_query_agent.A2AQueryAgent', return_value=mock_query_agent), \
             patch('src.a2a_protocol.a2a_knowledge_agent.A2AKnowledgeAgent', return_value=mock_knowledge_agent), \
             patch('src.a2a_protocol.a2a_response_agent.A2AResponseAgent', return_value=mock_response_agent):
            
            await ai_system._initialize_agents()
            
            # Verify agents were created and started
            assert 'query' in ai_system.agents
            assert 'knowledge' in ai_system.agents
            assert 'response' in ai_system.agents
    
    @pytest.mark.asyncio
    async def test_query_processing(self, ai_system):
        """Test query processing through the system."""
        # Setup initialized system
        ai_system.initialized = True
        ai_system.coordinator = AsyncMock()
        
        # Mock coordinator response
        mock_result = {
            "success": True,
            "workflow_id": "test_workflow_123",
            "response": "Test response"
        }
        ai_system.coordinator.process_task.return_value = mock_result
        
        query = "How do I reset my password?"
        customer_id = "test_customer_123"
        
        result = await ai_system.process_query(query, customer_id)
        
        assert result["success"] is True
        assert result["workflow_id"] == "test_workflow_123"
        ai_system.coordinator.process_task.assert_called_once()
        
        # Verify task data structure
        call_args = ai_system.coordinator.process_task.call_args[0][0]
        assert call_args["task_type"] == "customer_support_workflow"
        assert call_args["query_data"]["query"] == query
        assert call_args["query_data"]["customer_id"] == customer_id
    
    @pytest.mark.asyncio
    async def test_query_processing_not_initialized(self, ai_system):
        """Test query processing when system not initialized."""
        query = "Test query"
        customer_id = "test_customer"
        
        result = await ai_system.process_query(query, customer_id)
        
        assert result["success"] is False
        assert "not initialized" in result["error"]
    
    @pytest.mark.asyncio
    async def test_system_shutdown(self, ai_system):
        """Test system shutdown process."""
        # Setup initialized system with mocked components
        ai_system.initialized = True
        ai_system.coordinator = AsyncMock()
        ai_system.agents = {
            'query': AsyncMock(),
            'knowledge': AsyncMock(),
            'response': AsyncMock()
        }
        
        await ai_system.shutdown()
        
        # Verify all components were stopped
        ai_system.coordinator.stop.assert_called_once()
        for agent in ai_system.agents.values():
            agent.stop.assert_called_once()
        
        assert ai_system.initialized is False
    
    @pytest.mark.asyncio
    async def test_system_health_check(self, ai_system):
        """Test system health check functionality."""
        # Setup initialized system
        ai_system.initialized = True
        ai_system.coordinator = AsyncMock()
        ai_system.agents = {
            'query': AsyncMock(),
            'knowledge': AsyncMock(),
            'response': AsyncMock()
        }
        
        # Mock health responses
        ai_system.coordinator.process_task.return_value = {"status": "healthy"}
        for agent in ai_system.agents.values():
            agent.get_metrics.return_value = {"status": "healthy", "load": 0.1}
        
        health_status = await ai_system.get_health_status()
        
        assert health_status["system_initialized"] is True
        assert health_status["coordinator_status"]["status"] == "healthy"
        assert len(health_status["agent_status"]) == 3
    
    @pytest.mark.asyncio
    async def test_system_health_check_not_initialized(self, ai_system):
        """Test health check when system not initialized."""
        health_status = await ai_system.get_health_status()
        
        assert health_status["system_initialized"] is False
        assert health_status["coordinator_status"] is None
        assert health_status["agent_status"] == {}
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_queries(self, ai_system):
        """Test processing multiple concurrent queries."""
        # Setup initialized system
        ai_system.initialized = True
        ai_system.coordinator = AsyncMock()
        
        # Mock coordinator to return different results for each query
        def mock_process_task(task_data):
            query = task_data["query_data"]["query"]
            return {
                "success": True,
                "workflow_id": f"workflow_{hash(query)}",
                "response": f"Response for: {query}"
            }
        
        ai_system.coordinator.process_task.side_effect = mock_process_task
        
        # Process multiple queries concurrently
        queries = [
            ("How do I reset my password?", "customer_1"),
            ("What is your refund policy?", "customer_2"),
            ("I can't log into my account", "customer_3"),
            ("How do I change my billing address?", "customer_4"),
            ("When will my order arrive?", "customer_5")
        ]
        
        tasks = [
            ai_system.process_query(query, customer_id)
            for query, customer_id in queries
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        for result in results:
            assert result["success"] is True
            assert "workflow_id" in result
            assert "response" in result
        
        # Verify coordinator was called for each query
        assert ai_system.coordinator.process_task.call_count == 5
    
    @pytest.mark.asyncio
    async def test_system_error_recovery(self, ai_system):
        """Test system error recovery capabilities."""
        # Setup system that fails during initialization
        with patch('src.a2a_protocol.simplified_main.A2ACoordinator') as mock_coordinator:
            mock_coordinator.side_effect = Exception("Network error")
            
            # First initialization fails
            await ai_system.initialize()
            assert ai_system.initialized is False
            
            # Fix the issue and retry
            mock_coordinator_instance = AsyncMock()
            mock_coordinator.side_effect = None
            mock_coordinator.return_value = mock_coordinator_instance
            
            with patch.object(ai_system, '_initialize_agents', new_callable=AsyncMock):
                await ai_system.initialize()
                assert ai_system.initialized is True


@pytest.mark.integration
class TestSimplifiedGeneticAISystemIntegration:
    """Integration tests for the complete AI system."""
    
    @pytest.fixture
    def integration_system(self):
        return SimplifiedGeneticAISystem()
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, integration_system):
        """Test complete end-to-end workflow."""
        with patch('src.a2a_protocol.simplified_main.A2ACoordinator') as mock_coordinator, \
             patch('src.a2a_protocol.a2a_query_agent.A2AQueryAgent') as mock_query, \
             patch('src.a2a_protocol.a2a_knowledge_agent.A2AKnowledgeAgent') as mock_knowledge, \
             patch('src.a2a_protocol.a2a_response_agent.A2AResponseAgent') as mock_response:
            
            # Setup all mocks
            mock_coordinator_instance = AsyncMock()
            mock_coordinator.return_value = mock_coordinator_instance
            
            for mock_agent in [mock_query, mock_knowledge, mock_response]:
                mock_agent_instance = AsyncMock()
                mock_agent.return_value = mock_agent_instance
            
            # Mock coordinator workflow response
            mock_coordinator_instance.process_task.return_value = {
                "success": True,
                "workflow_id": "integration_test_workflow",
                "query_analysis": {"intent": "help", "urgency": "medium"},
                "knowledge_result": {"knowledge": "Helpful information"},
                "response_result": {"response": "Here's how I can help you..."},
                "total_agents_used": 3
            }
            
            # Initialize system
            await integration_system.initialize()
            assert integration_system.initialized is True
            
            # Process a query
            result = await integration_system.process_query(
                "I need help with my account",
                "integration_customer_123"
            )
            
            assert result["success"] is True
            assert result["workflow_id"] == "integration_test_workflow"
            assert result["total_agents_used"] == 3
            
            # Shutdown system
            await integration_system.shutdown()
            assert integration_system.initialized is False
    
    @pytest.mark.asyncio
    async def test_system_with_genetic_optimization(self, integration_system):
        """Test system with genetic algorithm optimization enabled."""
        # This would test the genetic algorithm integration
        # For now, we'll test the basic structure
        
        # Mock genetic optimization
        mock_chromosome = Mock()
        mock_chromosome.genes = {
            'response_timeout': 8.0,
            'confidence_threshold': 0.85,
            'empathy_level': 0.9
        }
        
        with patch('src.a2a_protocol.simplified_main.A2ACoordinator') as mock_coordinator:
            mock_coordinator_instance = AsyncMock()
            mock_coordinator.return_value = mock_coordinator_instance
            
            with patch.object(integration_system, '_initialize_agents', new_callable=AsyncMock):
                await integration_system.initialize()
                
                # Simulate setting chromosomes on agents
                for agent_id, agent in integration_system.agents.items():
                    if hasattr(agent, 'set_chromosome'):
                        agent.set_chromosome(mock_chromosome)
                
                assert integration_system.initialized is True
    
    @pytest.mark.asyncio
    async def test_system_performance_monitoring(self, integration_system):
        """Test system performance monitoring capabilities."""
        with patch('src.a2a_protocol.simplified_main.A2ACoordinator') as mock_coordinator:
            mock_coordinator_instance = AsyncMock()
            mock_coordinator.return_value = mock_coordinator_instance
            
            # Mock performance metrics
            mock_coordinator_instance.get_metrics.return_value = {
                "workflows_processed": 150,
                "average_response_time": 2.3,
                "success_rate": 0.98
            }
            
            with patch.object(integration_system, '_initialize_agents', new_callable=AsyncMock):
                await integration_system.initialize()
                
                # Get performance metrics
                metrics = await integration_system.get_performance_metrics()
                
                assert "coordinator_metrics" in metrics
                assert "system_uptime" in metrics
                assert "total_queries_processed" in metrics


@pytest.mark.performance
class TestSimplifiedGeneticAISystemPerformance:
    """Performance tests for the AI system."""
    
    @pytest.fixture
    def perf_system(self):
        return SimplifiedGeneticAISystem()
    
    @pytest.mark.asyncio
    async def test_system_startup_time(self, perf_system):
        """Test system startup performance."""
        import time
        
        with patch('src.a2a_protocol.simplified_main.A2ACoordinator') as mock_coordinator:
            mock_coordinator_instance = AsyncMock()
            mock_coordinator.return_value = mock_coordinator_instance
            
            with patch.object(perf_system, '_initialize_agents', new_callable=AsyncMock):
                start_time = time.time()
                await perf_system.initialize()
                end_time = time.time()
                
                startup_time = end_time - start_time
                
                assert perf_system.initialized is True
                assert startup_time < 5.0  # Should initialize in under 5 seconds
    
    @pytest.mark.asyncio
    async def test_query_processing_throughput(self, perf_system):
        """Test query processing throughput."""
        import time
        
        # Setup system
        perf_system.initialized = True
        perf_system.coordinator = AsyncMock()
        
        # Fast mock response
        perf_system.coordinator.process_task.return_value = {
            "success": True,
            "workflow_id": "perf_test",
            "response": "Fast response"
        }
        
        # Process many queries
        num_queries = 50
        queries = [
            (f"Performance test query {i}", f"customer_{i}")
            for i in range(num_queries)
        ]
        
        start_time = time.time()
        
        tasks = [
            perf_system.process_query(query, customer_id)
            for query, customer_id in queries
        ]
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert len(results) == num_queries
        assert all(result["success"] for result in results)
        
        queries_per_second = num_queries / processing_time
        assert queries_per_second > 10  # At least 10 queries per second
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, perf_system):
        """Test memory usage under load."""
        import gc
        
        # Setup system
        perf_system.initialized = True
        perf_system.coordinator = AsyncMock()
        perf_system.coordinator.process_task.return_value = {"success": True}
        
        # Get baseline memory
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Process many queries
        for i in range(200):
            result = await perf_system.process_query(f"Load test {i}", f"customer_{i}")
            assert result["success"] is True
        
        # Check memory growth
        gc.collect()
        final_objects = len(gc.get_objects())
        
        memory_growth_ratio = (final_objects - initial_objects) / initial_objects
        assert memory_growth_ratio < 1.0  # Memory shouldn't double
