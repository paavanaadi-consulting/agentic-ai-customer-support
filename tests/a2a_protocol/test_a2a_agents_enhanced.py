"""
Enhanced comprehensive tests for A2A agents (Query, Knowledge, Response).
Tests all capabilities, genetic algorithm features, and MCP integration.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.a2a_protocol.a2a_query_agent import A2AQueryAgent
from src.a2a_protocol.a2a_knowledge_agent import A2AKnowledgeAgent 
from src.a2a_protocol.a2a_response_agent import A2AResponseAgent


class TestA2AQueryAgentEnhanced:
    """Enhanced tests for A2A Query Agent."""
    
    @pytest.fixture
    def query_agent(self):
        return A2AQueryAgent("test_query_agent", "test-key", mcp_clients={"test": "client"})
    
    def test_query_agent_initialization(self, query_agent):
        """Test query agent initialization."""
        assert query_agent.agent_id == "test_query_agent"
        assert query_agent.agent_type == "query"
        assert query_agent.port == 8001
        assert query_agent.api_key == "test-key"
        assert query_agent.mcp_clients == {"test": "client"}
    
    def test_query_agent_capabilities(self, query_agent):
        """Test query agent capabilities."""
        capabilities = query_agent.get_capabilities()
        expected_capabilities = [
            'analyze_query',
            'extract_entities', 
            'classify_intent',
            'detect_urgency',
            'sentiment_analysis',
            'language_detection'
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities
    
    def test_query_agent_gene_template(self, query_agent):
        """Test query agent genetic algorithm gene template."""
        gene_template = query_agent._get_default_gene_template()
        
        expected_genes = [
            'confidence_threshold',
            'context_window_size',
            'classification_detail_level',
            'include_sentiment',
            'extract_entities',
            'urgency_detection'
        ]
        
        for gene in expected_genes:
            assert gene in gene_template
    
    def test_query_agent_gene_ranges(self, query_agent):
        """Test query agent gene ranges."""
        gene_ranges = query_agent._get_gene_ranges()
        
        assert isinstance(gene_ranges['confidence_threshold'], tuple)
        assert isinstance(gene_ranges['context_window_size'], tuple)
        assert isinstance(gene_ranges['classification_detail_level'], list)
        assert isinstance(gene_ranges['include_sentiment'], list)
        assert isinstance(gene_ranges['extract_entities'], list)
        assert isinstance(gene_ranges['urgency_detection'], list)
    
    def test_query_agent_prompt_building(self, query_agent):
        """Test query agent prompt building for different capabilities."""
        query = "I need help with my account"
        context = {"customer_id": "123", "previous_interactions": 2}
        mcp_clients = {"postgres": "db_client"}
        
        # Test analyze_query capability
        prompt = query_agent._build_prompt(query, "analyze_query", context, mcp_clients)
        assert "Analyze this customer support query" in prompt
        assert query in prompt
        assert "customer_id: 123" in prompt
        
        # Test extract_entities capability
        prompt = query_agent._build_prompt(query, "extract_entities", context, mcp_clients)
        assert "Extract entities from this customer query" in prompt
        
        # Test classify_intent capability
        prompt = query_agent._build_prompt(query, "classify_intent", context, mcp_clients)
        assert "Classify the intent of this customer query" in prompt
        
        # Test detect_urgency capability
        prompt = query_agent._build_prompt(query, "detect_urgency", context, mcp_clients)
        assert "Detect the urgency level of this customer query" in prompt
        
        # Test sentiment_analysis capability
        prompt = query_agent._build_prompt(query, "sentiment_analysis", context, mcp_clients)
        assert "Analyze the sentiment of this customer query" in prompt
        
        # Test language_detection capability
        prompt = query_agent._build_prompt(query, "language_detection", context, mcp_clients)
        assert "Detect the language of this customer query" in prompt
    
    @pytest.mark.asyncio
    async def test_query_agent_task_processing_capabilities(self, query_agent):
        """Test query agent processing different task capabilities."""
        base_task_data = {
            "task_type": "analyze_query",
            "input_data": {"query": "Test query"},
            "api_key": "test-key"
        }
        
        capabilities = query_agent.get_capabilities()
        
        for capability in capabilities:
            task_data = {**base_task_data, "capability": capability}
            
            with patch.object(query_agent, '_call_llm', new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = f"Mock response for {capability}"
                
                result = await query_agent.process_task(task_data)
                
                assert result["success"] is True
                assert result["a2a_processed"] is True
                assert result["agent_id"] == "test_query_agent"
                assert "processing_time" in result
                mock_llm.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_query_agent_llm_providers(self, query_agent):
        """Test query agent with different LLM providers."""
        providers = [
            ("openai", "gpt-3.5-turbo"),
            ("gemini", "gemini-pro"),
            ("claude", "claude-3-opus-20240229")
        ]
        
        for provider, model in providers:
            task_data = {
                "task_type": "analyze_query",
                "input_data": {"query": "Test query"},
                "capability": "analyze_query",
                "llm_provider": provider,
                "llm_model": model,
                "api_key": f"test-{provider}-key"
            }
            
            with patch.object(query_agent, '_call_llm', new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = f"Response from {provider}"
                
                result = await query_agent.process_task(task_data)
                
                assert result["success"] is True
                mock_llm.assert_called_once_with(
                    mock_llm.call_args[0][0],  # prompt
                    provider,
                    model
                )
    
    def test_query_agent_chromosome_application(self, query_agent):
        """Test query agent genetic algorithm chromosome application."""
        mock_chromosome = Mock()
        mock_chromosome.genes = {
            'confidence_threshold': 0.9,
            'context_window_size': 1500,
            'classification_detail_level': 'high',
            'include_sentiment': True,
            'extract_entities': True,
            'urgency_detection': False
        }
        
        query_agent.set_chromosome(mock_chromosome)
        
        assert query_agent.current_chromosome == mock_chromosome
        assert query_agent.confidence_threshold == 0.9
        assert query_agent.context_window_size == 1500
        assert query_agent.classification_detail_level == 'high'
        assert query_agent.include_sentiment is True
        assert query_agent.extract_entities is True
        assert query_agent.urgency_detection is False
    
    def test_query_agent_process_input_for_fitness(self, query_agent):
        """Test query agent process_input method for fitness evaluation."""
        input_data = {
            "query": "I can't log into my account",
            "context": {"customer_id": "123"},
            "expected_analysis": {
                "intent": "account_access",
                "urgency": "medium",
                "sentiment": "frustrated"
            }
        }
        
        result = query_agent.process_input(input_data)
        
        assert "processed" in result
        assert "analysis_quality" in result
        assert "processing_time" in result
        assert "confidence" in result


class TestA2AKnowledgeAgentEnhanced:
    """Enhanced tests for A2A Knowledge Agent."""
    
    @pytest.fixture
    def knowledge_agent(self):
        return A2AKnowledgeAgent("test_knowledge_agent", "test-key", mcp_clients={"test": "client"})
    
    def test_knowledge_agent_initialization(self, knowledge_agent):
        """Test knowledge agent initialization."""
        assert knowledge_agent.agent_id == "test_knowledge_agent"
        assert knowledge_agent.agent_type == "knowledge"
        assert knowledge_agent.port == 8002
        assert knowledge_agent.api_key == "test-key"
    
    def test_knowledge_agent_capabilities(self, knowledge_agent):
        """Test knowledge agent capabilities."""
        capabilities = knowledge_agent.get_capabilities()
        expected_capabilities = [
            'knowledge_search',
            'fact_verification',
            'content_synthesis', 
            'document_retrieval',
            'context_enrichment',
            'similarity_search'
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities
    
    def test_knowledge_agent_gene_template(self, knowledge_agent):
        """Test knowledge agent genetic algorithm gene template."""
        gene_template = knowledge_agent._get_default_gene_template()
        
        expected_genes = [
            'search_depth',
            'relevance_threshold', 
            'context_window',
            'fact_checking_enabled',
            'similarity_threshold',
            'max_documents'
        ]
        
        for gene in expected_genes:
            assert gene in gene_template
    
    def test_knowledge_agent_prompt_building(self, knowledge_agent):
        """Test knowledge agent prompt building for different capabilities."""
        query = "What is the refund policy?"
        context = {"customer_tier": "premium"}
        
        # Test knowledge_search capability
        prompt = knowledge_agent._build_prompt(query, "knowledge_search", context)
        assert "Search for relevant knowledge" in prompt
        assert query in prompt
        
        # Test fact_verification capability  
        prompt = knowledge_agent._build_prompt(query, "fact_verification", context)
        assert "Verify the factual accuracy" in prompt
        
        # Test content_synthesis capability
        prompt = knowledge_agent._build_prompt(query, "content_synthesis", context)
        assert "Synthesize relevant information" in prompt
    
    @pytest.mark.asyncio
    async def test_knowledge_agent_task_processing(self, knowledge_agent):
        """Test knowledge agent task processing."""
        task_data = {
            "task_type": "knowledge_search",
            "input_data": {"query": "How do I reset my password?"},
            "capability": "knowledge_search",
            "api_key": "test-key"
        }
        
        with patch.object(knowledge_agent, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Password reset instructions..."
            
            result = await knowledge_agent.process_task(task_data)
            
            assert result["success"] is True
            assert result["a2a_processed"] is True
            assert result["agent_id"] == "test_knowledge_agent"
            assert "processing_time" in result
    
    def test_knowledge_agent_chromosome_application(self, knowledge_agent):
        """Test knowledge agent chromosome application."""
        mock_chromosome = Mock()
        mock_chromosome.genes = {
            'search_depth': 8,
            'relevance_threshold': 0.85,
            'context_window': 2000,
            'fact_checking_enabled': True,
            'similarity_threshold': 0.75,
            'max_documents': 20
        }
        
        knowledge_agent.set_chromosome(mock_chromosome)
        
        assert knowledge_agent.current_chromosome == mock_chromosome
        assert knowledge_agent.search_depth == 8
        assert knowledge_agent.relevance_threshold == 0.85
        assert knowledge_agent.context_window == 2000
        assert knowledge_agent.fact_checking_enabled is True
        assert knowledge_agent.similarity_threshold == 0.75
        assert knowledge_agent.max_documents == 20


class TestA2AResponseAgentEnhanced:
    """Enhanced tests for A2A Response Agent."""
    
    @pytest.fixture
    def response_agent(self):
        return A2AResponseAgent("test_response_agent", "test-key", mcp_clients={"test": "client"})
    
    def test_response_agent_initialization(self, response_agent):
        """Test response agent initialization."""
        assert response_agent.agent_id == "test_response_agent"
        assert response_agent.agent_type == "response"
        assert response_agent.port == 8003
        assert response_agent.api_key == "test-key"
    
    def test_response_agent_capabilities(self, response_agent):
        """Test response agent capabilities."""
        capabilities = response_agent.get_capabilities()
        expected_capabilities = [
            'generate_response',
            'craft_email',
            'create_ticket_response',
            'personalize_content',
            'tone_adjustment',
            'multi_language_response'
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities
    
    def test_response_agent_gene_template(self, response_agent):
        """Test response agent genetic algorithm gene template."""
        gene_template = response_agent._get_default_gene_template()
        
        expected_genes = [
            'empathy_level',
            'formality_level',
            'personalization_level',
            'response_length',
            'fact_checking_enabled',
            'escalation_threshold'
        ]
        
        for gene in expected_genes:
            assert gene in gene_template
    
    def test_response_agent_prompt_building(self, response_agent):
        """Test response agent prompt building for different capabilities."""
        query = "Generate a helpful response"
        context = {"customer_mood": "frustrated"}
        
        # Test generate_response capability
        prompt = response_agent._build_prompt(query, "generate_response", context)
        assert query in prompt
        assert "customer_mood: frustrated" in prompt
        
        # Test craft_email capability
        prompt = response_agent._build_prompt(query, "craft_email", context)
        assert "Craft a professional email response" in prompt
        
        # Test personalize_content capability
        prompt = response_agent._build_prompt(query, "personalize_content", context)
        assert "Personalize the following content" in prompt
        
        # Test tone_adjustment capability
        prompt = response_agent._build_prompt(query, "tone_adjustment", context)
        assert "Adjust the tone of this response" in prompt
        
        # Test multi_language_response capability
        prompt = response_agent._build_prompt(query, "multi_language_response", context)
        assert "Translate the following response" in prompt
    
    @pytest.mark.asyncio
    async def test_response_agent_task_processing(self, response_agent):
        """Test response agent task processing."""
        task_data = {
            "task_type": "generate_response",
            "query_analysis": {"analysis": "Customer needs password reset help"},
            "knowledge_result": {"knowledge": "Password reset procedure"},
            "capability": "generate_response",
            "api_key": "test-key"
        }
        
        with patch.object(response_agent, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "I'd be happy to help you reset your password..."
            
            result = await response_agent.process_task(task_data)
            
            assert result["success"] is True
            assert result["a2a_processed"] is True
            assert result["agent_id"] == "test_response_agent"
            assert "processing_time" in result
            assert "response" in result
    
    def test_response_agent_content_generation_methods(self, response_agent):
        """Test response agent content generation helper methods."""
        # Test solution-focused content generation
        content = response_agent._generate_solution_focused_content("technical", "high")
        assert "technical issue" in content
        assert "urgency" in content or "prioritize" in content
        
        content = response_agent._generate_solution_focused_content("billing", "low")
        assert "billing" in content
        
        # Test general content generation
        content = response_agent._generate_general_content("feature_request")
        assert "feature_request" in content
        
        # Test suggestions generation
        suggestions = response_agent._generate_suggestions("technical", "medium")
        assert "troubleshooting" in suggestions
        
        suggestions = response_agent._generate_suggestions("billing", "low")
        assert "auto-pay" in suggestions
    
    def test_response_agent_chromosome_application(self, response_agent):
        """Test response agent chromosome application."""
        mock_chromosome = Mock()
        mock_chromosome.genes = {
            'empathy_level': 0.9,
            'formality_level': 0.6,
            'personalization_level': 0.8,
            'response_length': 'medium',
            'fact_checking_enabled': True,
            'escalation_threshold': 0.85
        }
        
        response_agent.set_chromosome(mock_chromosome)
        
        assert response_agent.current_chromosome == mock_chromosome
        assert response_agent.empathy_level == 0.9
        assert response_agent.formality_level == 0.6
        assert response_agent.personalization_level == 0.8
        assert response_agent.response_length == 'medium'
        assert response_agent.fact_checking_enabled is True
        assert response_agent.escalation_threshold == 0.85
    
    def test_response_agent_process_input_for_fitness(self, response_agent):
        """Test response agent process_input method for fitness evaluation."""
        input_data = {
            "query_analysis": {"intent": "help_request", "sentiment": "neutral"},
            "knowledge_result": {"relevant_info": "Product documentation"},
            "context": {"customer_tier": "premium"},
            "expected_response": {
                "tone": "professional_helpful",
                "personalized": True,
                "empathy_level": "high"
            }
        }
        
        result = response_agent.process_input(input_data)
        
        assert "response_generated" in result
        assert "response_quality" in result
        assert "processing_time" in result
        assert "confidence" in result


@pytest.mark.integration
class TestA2AAgentsIntegration:
    """Integration tests for A2A agents working together."""
    
    @pytest.fixture
    def all_agents(self):
        """Create all A2A agents for integration testing."""
        return {
            "query": A2AQueryAgent("integration_query", "test-key"),
            "knowledge": A2AKnowledgeAgent("integration_knowledge", "test-key"),
            "response": A2AResponseAgent("integration_response", "test-key")
        }
    
    @pytest.mark.asyncio
    async def test_agent_capability_discovery(self, all_agents):
        """Test agents can discover each other's capabilities."""
        query_agent = all_agents["query"]
        knowledge_agent = all_agents["knowledge"]
        
        # Start agents
        await query_agent.start()
        await knowledge_agent.start()
        
        try:
            # Allow discovery time
            await asyncio.sleep(1)
            
            # Test capability querying
            query_capabilities = query_agent.get_capabilities()
            knowledge_capabilities = knowledge_agent.get_capabilities()
            
            assert len(query_capabilities) > 0
            assert len(knowledge_capabilities) > 0
            assert query_capabilities != knowledge_capabilities
        
        finally:
            await query_agent.stop()
            await knowledge_agent.stop()
    
    @pytest.mark.asyncio
    async def test_agent_task_delegation(self, all_agents):
        """Test agent task delegation between agents."""
        query_agent = all_agents["query"]
        knowledge_agent = all_agents["knowledge"]
        
        # Mock task delegation
        task_data = {
            "task_type": "knowledge_search",
            "input_data": {"query": "Integration test query"},
            "capability": "knowledge_search"
        }
        
        with patch.object(knowledge_agent, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Integration test knowledge"
            
            # Simulate task delegation from query to knowledge agent
            result = await knowledge_agent.process_task(task_data)
            
            assert result["success"] is True
            assert result["agent_id"] == "integration_knowledge"
    
    @pytest.mark.asyncio
    async def test_multi_agent_workflow_simulation(self, all_agents):
        """Test simulated multi-agent workflow."""
        query_agent = all_agents["query"]
        knowledge_agent = all_agents["knowledge"]  
        response_agent = all_agents["response"]
        
        # Simulate full workflow
        customer_query = "I forgot my password and can't log in"
        
        # Step 1: Query analysis
        with patch.object(query_agent, '_call_llm', new_callable=AsyncMock) as mock_query_llm:
            mock_query_llm.return_value = "Intent: password_reset, Urgency: medium, Sentiment: frustrated"
            
            query_result = await query_agent.process_task({
                "task_type": "analyze_query",
                "input_data": {"query": customer_query},
                "capability": "analyze_query"
            })
        
        # Step 2: Knowledge retrieval
        with patch.object(knowledge_agent, '_call_llm', new_callable=AsyncMock) as mock_knowledge_llm:
            mock_knowledge_llm.return_value = "Password reset steps: 1) Go to login page 2) Click forgot password..."
            
            knowledge_result = await knowledge_agent.process_task({
                "task_type": "knowledge_search",
                "input_data": {"query": customer_query},
                "capability": "knowledge_search"
            })
        
        # Step 3: Response generation
        with patch.object(response_agent, '_call_llm', new_callable=AsyncMock) as mock_response_llm:
            mock_response_llm.return_value = "I understand you're having trouble logging in. Let me help you reset your password..."
            
            response_result = await response_agent.process_task({
                "task_type": "generate_response",
                "query_analysis": query_result,
                "knowledge_result": knowledge_result,
                "capability": "generate_response"
            })
        
        # Verify workflow completion
        assert query_result["success"] is True
        assert knowledge_result["success"] is True
        assert response_result["success"] is True
        
        # Verify data flow
        assert "analysis" in query_result or "response" in query_result
        assert "knowledge" in knowledge_result or "response" in knowledge_result
        assert "response" in response_result


@pytest.mark.performance  
class TestA2AAgentsPerformance:
    """Performance tests for A2A agents."""
    
    @pytest.fixture
    def perf_agents(self):
        return {
            "query": A2AQueryAgent("perf_query", "test-key"),
            "knowledge": A2AKnowledgeAgent("perf_knowledge", "test-key"),
            "response": A2AResponseAgent("perf_response", "test-key")
        }
    
    @pytest.mark.asyncio
    async def test_agent_concurrent_processing(self, perf_agents):
        """Test agent concurrent task processing performance."""
        import time
        
        agent = perf_agents["query"]
        
        # Create multiple tasks
        tasks = []
        for i in range(20):
            task_data = {
                "task_type": "analyze_query",
                "input_data": {"query": f"Performance test query {i}"},
                "capability": "analyze_query"
            }
            tasks.append(task_data)
        
        with patch.object(agent, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Fast mock response"
            
            start_time = time.time()
            
            # Process all tasks concurrently
            async_tasks = [agent.process_task(task) for task in tasks]
            results = await asyncio.gather(*async_tasks)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            assert len(results) == 20
            assert all(result["success"] for result in results)
            assert processing_time < 10.0  # Should complete in under 10 seconds
            
            tasks_per_second = 20 / processing_time
            assert tasks_per_second > 2  # At least 2 tasks per second
    
    @pytest.mark.asyncio
    async def test_agent_memory_efficiency(self, perf_agents):
        """Test agent memory efficiency during processing."""
        import gc
        import sys
        
        agent = perf_agents["response"]
        
        # Get initial memory usage
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Process many tasks
        with patch.object(agent, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Memory test response"
            
            for i in range(100):
                task_data = {
                    "task_type": "generate_response", 
                    "query_analysis": {"analysis": f"Test {i}"},
                    "capability": "generate_response"
                }
                
                result = await agent.process_task(task_data)
                assert result["success"] is True
        
        # Check memory usage after processing
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Memory increase should be reasonable (less than 50% increase)
        memory_increase_ratio = (final_objects - initial_objects) / initial_objects
        assert memory_increase_ratio < 0.5
