"""
Comprehensive test suite for EvolutionEngine.
Tests evolution management, agent coordination, and optimization processes.
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

from src.geneticML.engines.evolution_engine import EvolutionEngine
from src.geneticML.core.genetic_algorithm import GeneticAlgorithm, Chromosome
from src.geneticML.evaluators.fitness_evaluator import FitnessEvaluator


class TestEvolutionEngine:
    """Test cases for EvolutionEngine class."""

    @pytest.fixture
    def mock_agents(self):
        """Create mock agents for testing."""
        agents = {}
        
        for agent_id in ['query', 'knowledge', 'response']:
            agent = Mock()
            agent.gene_template = {
                'confidence_threshold': 0.8,
                'timeout': 5.0,
                'max_retries': 3
            }
            agent.gene_ranges = {
                'confidence_threshold': (0.5, 1.0),
                'timeout': (1.0, 10.0),
                'max_retries': (1, 5)
            }
            agent.set_chromosome = Mock()
            agent.process_input = Mock(return_value={'success': True, 'content': 'test'})
            agents[agent_id] = agent
        
        return agents

    @pytest.fixture
    def evolution_config(self):
        """Create evolution configuration for testing."""
        config = Mock()
        config.population_size = 10
        config.mutation_rate = 0.1
        config.crossover_rate = 0.8
        config.elite_size = 2
        config.max_generations = 5
        config.fitness_threshold = 0.9
        return config

    @pytest.fixture
    def evolution_engine(self, mock_agents, evolution_config):
        """Create an EvolutionEngine instance for testing."""
        return EvolutionEngine(mock_agents, evolution_config)

    def test_evolution_engine_initialization(self, evolution_engine, mock_agents, evolution_config):
        """Test EvolutionEngine initialization."""
        assert evolution_engine.agents == mock_agents
        assert evolution_engine.config == evolution_config
        assert evolution_engine.genetic_algorithms == {}
        assert evolution_engine.training_data == []
        assert evolution_engine.test_cases == []
        assert evolution_engine.evolution_history == []
        assert evolution_engine.current_generation == 0
        assert evolution_engine.best_chromosomes == {}
        assert evolution_engine.interaction_history == []
        assert isinstance(evolution_engine.fitness_evaluator, FitnessEvaluator)

    @pytest.mark.asyncio
    async def test_initialize_engine(self, evolution_engine, mock_agents):
        """Test engine initialization process."""
        with patch.object(evolution_engine, '_load_test_cases', new_callable=AsyncMock):
            await evolution_engine.initialize()
        
        # Verify genetic algorithms were created for each agent
        assert len(evolution_engine.genetic_algorithms) == len(mock_agents)
        
        for agent_id in mock_agents.keys():
            assert agent_id in evolution_engine.genetic_algorithms
            ga = evolution_engine.genetic_algorithms[agent_id]
            assert isinstance(ga, GeneticAlgorithm)
            assert len(ga.population) == evolution_engine.config.population_size

    @pytest.mark.asyncio
    async def test_load_test_cases(self, evolution_engine):
        """Test loading of test cases."""
        await evolution_engine._load_test_cases()
        
        # Verify test cases were loaded
        assert len(evolution_engine.test_cases) > 0
        
        # Verify test case structure
        for test_case in evolution_engine.test_cases:
            assert 'input' in test_case
            assert 'expected' in test_case
            assert 'query' in test_case['input']

    def test_get_gene_template_query_agent(self, evolution_engine):
        """Test gene template for query agent."""
        template = evolution_engine._get_gene_template('query')
        
        expected_keys = [
            'confidence_threshold', 'context_window_size', 
            'classification_detail_level', 'include_sentiment',
            'extract_entities', 'urgency_detection', 'response_timeout'
        ]
        
        for key in expected_keys:
            assert key in template

    def test_get_gene_template_knowledge_agent(self, evolution_engine):
        """Test gene template for knowledge agent."""
        template = evolution_engine._get_gene_template('knowledge')
        
        expected_keys = [
            'search_depth', 'relevance_threshold', 'max_sources',
            'include_citations', 'fact_checking_enabled',
            'synthesis_level', 'search_timeout'
        ]
        
        for key in expected_keys:
            assert key in template

    def test_get_gene_template_response_agent(self, evolution_engine):
        """Test gene template for response agent."""
        template = evolution_engine._get_gene_template('response')
        
        expected_keys = [
            'tone', 'length_preference', 'personalization_level',
            'empathy_level', 'formality_level', 'include_suggestions',
            'response_timeout'
        ]
        
        for key in expected_keys:
            assert key in template

    def test_get_gene_template_unknown_agent(self, evolution_engine):
        """Test gene template for unknown agent type."""
        template = evolution_engine._get_gene_template('unknown_agent')
        
        assert template == {}

    @pytest.mark.asyncio
    async def test_evolve_single_generation(self, evolution_engine):
        """Test evolution for a single generation."""
        # Initialize engine
        with patch.object(evolution_engine, '_load_test_cases', new_callable=AsyncMock):
            await evolution_engine.initialize()
        
        # Mock fitness evaluation to return consistent results
        def mock_fitness_function(chromosome):
            return 0.8  # Consistent fitness
        
        # Patch the evolve_agent method to use mock fitness
        with patch.object(evolution_engine, '_evolve_agent', new_callable=AsyncMock) as mock_evolve:
            mock_evolve.return_value = {
                'best_fitness': 0.8,
                'average_fitness': 0.6,
                'std_fitness': 0.1,
                'diversity': 0.5
            }
            
            await evolution_engine.evolve(max_generations=1)
        
        # Verify evolution completed
        assert evolution_engine.current_generation == 0  # 0-indexed
        assert len(evolution_engine.evolution_history) == 1
        
        # Verify evolution history structure
        history_entry = evolution_engine.evolution_history[0]
        assert 'generation' in history_entry
        assert 'timestamp' in history_entry
        assert 'stats' in history_entry

    @pytest.mark.asyncio
    async def test_evolve_agent_single(self, evolution_engine, mock_agents):
        """Test evolution of a single agent."""
        # Initialize engine
        with patch.object(evolution_engine, '_load_test_cases', new_callable=AsyncMock):
            await evolution_engine.initialize()
        
        agent_id = 'query'
        ga = evolution_engine.genetic_algorithms[agent_id]
        
        # Mock fitness evaluator
        with patch.object(evolution_engine.fitness_evaluator, 'evaluate_chromosome') as mock_eval:
            mock_eval.return_value = 0.75
            
            stats = await evolution_engine._evolve_agent(agent_id, ga)
        
        # Verify stats structure
        assert 'best_fitness' in stats
        assert 'average_fitness' in stats
        assert 'std_fitness' in stats
        assert 'diversity' in stats
        
        # Verify best chromosome was tracked
        assert agent_id in evolution_engine.best_chromosomes

    def test_check_convergence_not_converged(self, evolution_engine):
        """Test convergence check when fitness threshold not met."""
        evolution_engine.config.fitness_threshold = 0.9
        
        generation_stats = {
            'query': {'best_fitness': 0.8},
            'knowledge': {'best_fitness': 0.85},
            'response': {'best_fitness': 0.7}
        }
        
        converged = evolution_engine._check_convergence(generation_stats)
        
        assert converged is False

    def test_check_convergence_converged(self, evolution_engine):
        """Test convergence check when fitness threshold is met."""
        evolution_engine.config.fitness_threshold = 0.9
        
        generation_stats = {
            'query': {'best_fitness': 0.95},
            'knowledge': {'best_fitness': 0.92},
            'response': {'best_fitness': 0.91}
        }
        
        converged = evolution_engine._check_convergence(generation_stats)
        
        assert converged is True

    def test_log_generation_progress(self, evolution_engine):
        """Test logging of generation progress."""
        generation = 5
        stats = {
            'query': {
                'best_fitness': 0.85,
                'average_fitness': 0.65,
                'std_fitness': 0.12
            },
            'knowledge': {
                'best_fitness': 0.78,
                'average_fitness': 0.58,
                'std_fitness': 0.15
            }
        }
        
        # Should not raise any exceptions
        evolution_engine._log_generation_progress(generation, stats)

    @pytest.mark.asyncio
    async def test_apply_best_chromosomes(self, evolution_engine, mock_agents):
        """Test application of best chromosomes to agents."""
        # Set up best chromosomes
        for agent_id in mock_agents.keys():
            chromosome = Chromosome(
                genes={'test_gene': 0.8},
                fitness=0.9
            )
            evolution_engine.best_chromosomes[agent_id] = chromosome
        
        await evolution_engine._apply_best_chromosomes()
        
        # Verify each agent received its best chromosome
        for agent_id, agent in mock_agents.items():
            agent.set_chromosome.assert_called_once_with(
                evolution_engine.best_chromosomes[agent_id]
            )

    @pytest.mark.asyncio
    async def test_record_interaction(self, evolution_engine):
        """Test recording of interaction for continuous learning."""
        interaction_result = {
            'query_analysis': {
                'analysis': {
                    'category': 'technical',
                    'urgency': 'medium'
                }
            },
            'original_query': 'How do I reset my password?',
            'customer_id': 'test_001'
        }
        
        # Mock adaptive evolution
        with patch.object(evolution_engine, '_adaptive_evolution', new_callable=AsyncMock) as mock_adaptive:
            # Record 100 interactions to trigger adaptive evolution
            for i in range(100):
                await evolution_engine.record_interaction(interaction_result)
            
            # Verify adaptive evolution was triggered
            mock_adaptive.assert_called_once()
        
        # Verify interactions were recorded
        assert len(evolution_engine.interaction_history) == 100

    @pytest.mark.asyncio
    async def test_adaptive_evolution(self, evolution_engine):
        """Test adaptive evolution based on recent interactions."""
        # Set up interaction history
        interactions = []
        for i in range(50):
            interaction = {
                'result': {
                    'query_analysis': {
                        'analysis': {
                            'category': 'technical',
                            'urgency': 'medium'
                        }
                    },
                    'original_query': f'Test query {i}',
                    'customer_id': f'test_{i:03d}'
                }
            }
            interactions.append(interaction)
        
        evolution_engine.interaction_history = interactions
        
        # Mock the evolve method
        with patch.object(evolution_engine, 'evolve', new_callable=AsyncMock) as mock_evolve:
            await evolution_engine._adaptive_evolution()
            
            # Verify evolve was called with short generation count
            mock_evolve.assert_called_once_with(max_generations=5)

    def test_get_status(self, evolution_engine):
        """Test getting evolution status."""
        # Set up some state
        evolution_engine.current_generation = 10
        evolution_engine.interaction_history = ['interaction'] * 50
        evolution_engine.best_chromosomes = {
            'query': Chromosome(genes={}, fitness=0.8),
            'knowledge': Chromosome(genes={}, fitness=0.7)
        }
        evolution_engine.evolution_history = ['history'] * 5
        
        status = evolution_engine.get_status()
        
        assert status['current_generation'] == 10
        assert status['total_interactions'] == 50
        assert status['best_fitness_scores']['query'] == 0.8
        assert status['best_fitness_scores']['knowledge'] == 0.7
        assert status['evolution_history_length'] == 5
        assert 'agents_count' in status
        assert 'test_cases_count' in status

    def test_export_results(self, evolution_engine):
        """Test exporting evolution results."""
        # Set up some state
        evolution_engine.current_generation = 5
        evolution_engine.interaction_history = ['interaction'] * 25
        evolution_engine.evolution_history = [
            {
                'generation': 0,
                'stats': {'query': {'best_fitness': 0.5}}
            }
        ]
        evolution_engine.best_chromosomes = {
            'query': Chromosome(
                genes={'confidence': 0.8},
                fitness=0.9,
                generation=3
            )
        }
        
        results = evolution_engine.export_results()
        
        assert 'config' in results
        assert 'evolution_history' in results
        assert 'best_chromosomes' in results
        assert 'final_generation' in results
        assert 'total_interactions' in results
        
        # Verify chromosome export structure
        query_chromosome = results['best_chromosomes']['query']
        assert 'genes' in query_chromosome
        assert 'fitness' in query_chromosome
        assert 'generation' in query_chromosome


class TestEvolutionEngineIntegration:
    """Integration tests for EvolutionEngine with realistic scenarios."""

    @pytest.fixture
    def realistic_agents(self):
        """Create more realistic agent mocks."""
        agents = {}
        
        # Query agent - analyzes customer queries
        query_agent = Mock()
        query_agent.gene_template = {
            'confidence_threshold': 0.8,
            'context_window_size': 1000,
            'classification_detail': 'medium',
            'sentiment_analysis': True,
            'entity_extraction': True
        }
        query_agent.gene_ranges = {
            'confidence_threshold': (0.5, 1.0),
            'context_window_size': (500, 2000),
            'classification_detail': ['low', 'medium', 'high'],
            'sentiment_analysis': [True, False],
            'entity_extraction': [True, False]
        }
        
        def query_process(input_data):
            confidence = query_agent.chromosome.genes.get('confidence_threshold', 0.8)
            return {
                'success': True,
                'category': 'technical' if 'password' in input_data['query'] else 'general',
                'confidence': confidence,
                'processing_time': 1.0
            }
        
        query_agent.process_input = Mock(side_effect=query_process)
        query_agent.set_chromosome = Mock()
        query_agent.chromosome = Chromosome(genes=query_agent.gene_template)
        agents['query'] = query_agent
        
        # Knowledge agent - searches for relevant information
        knowledge_agent = Mock()
        knowledge_agent.gene_template = {
            'search_depth': 5,
            'relevance_threshold': 0.7,
            'max_sources': 10,
            'fact_checking': True
        }
        knowledge_agent.gene_ranges = {
            'search_depth': (3, 10),
            'relevance_threshold': (0.5, 0.9),
            'max_sources': (5, 20),
            'fact_checking': [True, False]
        }
        
        def knowledge_process(input_data):
            depth = knowledge_agent.chromosome.genes.get('search_depth', 5)
            return {
                'success': True,
                'sources_found': min(depth * 2, 15),
                'relevance_score': 0.8,
                'processing_time': depth * 0.5
            }
        
        knowledge_agent.process_input = Mock(side_effect=knowledge_process)
        knowledge_agent.set_chromosome = Mock()
        knowledge_agent.chromosome = Chromosome(genes=knowledge_agent.gene_template)
        agents['knowledge'] = knowledge_agent
        
        # Response agent - generates customer responses
        response_agent = Mock()
        response_agent.gene_template = {
            'tone': 'friendly',
            'personalization': 0.7,
            'empathy_level': 0.8,
            'response_length': 'medium'
        }
        response_agent.gene_ranges = {
            'tone': ['friendly', 'professional', 'casual'],
            'personalization': (0.0, 1.0),
            'empathy_level': (0.0, 1.0),
            'response_length': ['short', 'medium', 'long']
        }
        
        def response_process(input_data):
            empathy = response_agent.chromosome.genes.get('empathy_level', 0.8)
            return {
                'success': True,
                'response': 'Thank you for contacting us. We are here to help.',
                'empathy_score': empathy,
                'processing_time': 2.0,
                'word_count': 50
            }
        
        response_agent.process_input = Mock(side_effect=response_process)
        response_agent.set_chromosome = Mock()
        response_agent.chromosome = Chromosome(genes=response_agent.gene_template)
        agents['response'] = response_agent
        
        return agents

    @pytest.fixture
    def realistic_config(self):
        """Create realistic evolution configuration."""
        config = Mock()
        config.population_size = 20
        config.mutation_rate = 0.15
        config.crossover_rate = 0.8
        config.elite_size = 3
        config.max_generations = 10
        config.fitness_threshold = 0.85
        return config

    @pytest.mark.asyncio
    async def test_full_evolution_cycle(self, realistic_agents, realistic_config):
        """Test a complete evolution cycle with realistic agents."""
        evolution_engine = EvolutionEngine(realistic_agents, realistic_config)
        
        # Initialize and run evolution
        await evolution_engine.initialize()
        
        # Mock fitness evaluation for faster testing
        def mock_fitness_eval(chromosome, agent, test_cases):
            # Simulate fitness based on gene values
            base_fitness = 0.6
            
            if hasattr(agent, 'chromosome') and agent.chromosome:
                genes = agent.chromosome.genes
                
                # Reward certain gene combinations
                if 'confidence_threshold' in genes:
                    if 0.7 <= genes['confidence_threshold'] <= 0.9:
                        base_fitness += 0.2
                
                if 'empathy_level' in genes:
                    if genes['empathy_level'] > 0.7:
                        base_fitness += 0.1
            
            return min(base_fitness, 1.0)
        
        with patch.object(evolution_engine.fitness_evaluator, 'evaluate_chromosome', side_effect=mock_fitness_eval):
            await evolution_engine.evolve(max_generations=3)
        
        # Verify evolution completed
        assert evolution_engine.current_generation >= 0
        assert len(evolution_engine.evolution_history) > 0
        assert len(evolution_engine.best_chromosomes) == len(realistic_agents)
        
        # Verify best chromosomes were applied to agents
        for agent_id, agent in realistic_agents.items():
            agent.set_chromosome.assert_called()

    @pytest.mark.asyncio
    async def test_convergence_behavior(self, realistic_agents, realistic_config):
        """Test evolution convergence behavior."""
        # Set high fitness threshold to test early convergence
        realistic_config.fitness_threshold = 0.95
        
        evolution_engine = EvolutionEngine(realistic_agents, realistic_config)
        await evolution_engine.initialize()
        
        # Mock high fitness to trigger convergence
        def high_fitness_eval(chromosome, agent, test_cases):
            return 0.96  # Above threshold
        
        with patch.object(evolution_engine.fitness_evaluator, 'evaluate_chromosome', side_effect=high_fitness_eval):
            await evolution_engine.evolve(max_generations=10)
        
        # Should converge early (before 10 generations)
        assert evolution_engine.current_generation < 9

    @pytest.mark.asyncio
    async def test_adaptive_evolution_trigger(self, realistic_agents, realistic_config):
        """Test adaptive evolution triggering mechanism."""
        evolution_engine = EvolutionEngine(realistic_agents, realistic_config)
        await evolution_engine.initialize()
        
        # Create realistic interaction data
        interaction_template = {
            'result': {
                'query_analysis': {
                    'analysis': {
                        'category': 'technical',
                        'urgency': 'medium',
                        'sentiment': 'neutral'
                    }
                },
                'original_query': 'How do I reset my password?',
                'customer_id': 'cust_001'
            }
        }
        
        # Mock adaptive evolution
        with patch.object(evolution_engine, '_adaptive_evolution', new_callable=AsyncMock) as mock_adaptive:
            # Record 100 interactions to trigger adaptive evolution
            for i in range(100):
                interaction = interaction_template.copy()
                interaction['result']['customer_id'] = f'cust_{i:03d}'
                await evolution_engine.record_interaction(interaction)
            
            # Verify adaptive evolution was triggered
            mock_adaptive.assert_called_once()

    @pytest.mark.asyncio
    async def test_performance_tracking(self, realistic_agents, realistic_config):
        """Test performance tracking throughout evolution."""
        evolution_engine = EvolutionEngine(realistic_agents, realistic_config)
        await evolution_engine.initialize()
        
        # Mock fitness evaluation with improving scores
        generation_counter = [0]
        
        def improving_fitness_eval(chromosome, agent, test_cases):
            base_fitness = 0.5 + (generation_counter[0] * 0.1)
            return min(base_fitness, 1.0)
        
        def increment_generation(*args):
            generation_counter[0] += 1
            return improving_fitness_eval(*args)
        
        with patch.object(evolution_engine.fitness_evaluator, 'evaluate_chromosome', side_effect=increment_generation):
            await evolution_engine.evolve(max_generations=5)
        
        # Verify performance improved over generations
        assert len(evolution_engine.evolution_history) > 0
        
        # Check that fitness generally improved (allowing for some variance)
        first_gen_fitness = evolution_engine.evolution_history[0]['stats']
        last_gen_fitness = evolution_engine.evolution_history[-1]['stats']
        
        # At least one agent should have improved
        improved = False
        for agent_id in realistic_agents.keys():
            if (last_gen_fitness[agent_id]['best_fitness'] > 
                first_gen_fitness[agent_id]['best_fitness']):
                improved = True
                break
        
        assert improved, "No improvement detected across generations"


class TestEvolutionEngineErrorHandling:
    """Test error handling and edge cases for EvolutionEngine."""

    @pytest.fixture
    def minimal_config(self):
        """Create minimal configuration for testing."""
        config = Mock()
        config.population_size = 5
        config.mutation_rate = 0.1
        config.crossover_rate = 0.8
        config.elite_size = 1
        config.max_generations = 3
        config.fitness_threshold = 0.9
        return config

    @pytest.mark.asyncio
    async def test_empty_agents_dict(self, minimal_config):
        """Test behavior with empty agents dictionary."""
        evolution_engine = EvolutionEngine({}, minimal_config)
        
        await evolution_engine.initialize()
        
        # Should handle empty agents gracefully
        assert len(evolution_engine.genetic_algorithms) == 0
        
        # Evolution should complete without errors
        await evolution_engine.evolve(max_generations=1)

    @pytest.mark.asyncio
    async def test_agent_missing_gene_template(self, minimal_config):
        """Test handling of agents missing gene templates."""
        faulty_agent = Mock()
        faulty_agent.gene_template = None
        faulty_agent.gene_ranges = {}
        
        agents = {'faulty': faulty_agent}
        evolution_engine = EvolutionEngine(agents, minimal_config)
        
        # Should handle missing gene template gracefully
        try:
            await evolution_engine.initialize()
        except Exception as e:
            pytest.fail(f"Should handle missing gene template gracefully: {e}")

    @pytest.mark.asyncio
    async def test_fitness_evaluation_failure(self, minimal_config):
        """Test handling of fitness evaluation failures."""
        agent = Mock()
        agent.gene_template = {'param': 1.0}
        agent.gene_ranges = {'param': (0.0, 2.0)}
        agent.process_input = Mock(side_effect=Exception("Agent failure"))
        
        agents = {'test_agent': agent}
        evolution_engine = EvolutionEngine(agents, minimal_config)
        
        await evolution_engine.initialize()
        
        # Evolution should continue despite fitness evaluation failures
        await evolution_engine.evolve(max_generations=1)
        
        # Should have recorded the generation
        assert len(evolution_engine.evolution_history) == 1

    def test_malformed_interaction_data(self, minimal_config):
        """Test handling of malformed interaction data."""
        agents = {'test': Mock()}
        evolution_engine = EvolutionEngine(agents, minimal_config)
        
        # Test with various malformed interaction data
        malformed_interactions = [
            {},  # Empty dict
            {'result': {}},  # Missing required fields
            {'result': {'query_analysis': {}}},  # Missing analysis
            None,  # None value
        ]
        
        # Should handle all malformed data gracefully
        for interaction in malformed_interactions:
            try:
                asyncio.run(evolution_engine.record_interaction(interaction))
            except Exception as e:
                pytest.fail(f"Should handle malformed interaction gracefully: {e}")

    def test_status_with_empty_state(self, minimal_config):
        """Test getting status with empty/minimal state."""
        agents = {}
        evolution_engine = EvolutionEngine(agents, minimal_config)
        
        status = evolution_engine.get_status()
        
        # Should return valid status even with empty state
        assert isinstance(status, dict)
        assert 'current_generation' in status
        assert 'total_interactions' in status
        assert 'best_fitness_scores' in status
        assert status['agents_count'] == 0

    def test_export_results_empty_state(self, minimal_config):
        """Test exporting results with empty state."""
        agents = {}
        evolution_engine = EvolutionEngine(agents, minimal_config)
        
        results = evolution_engine.export_results()
        
        # Should return valid results structure even with empty state
        assert isinstance(results, dict)
        assert 'config' in results
        assert 'evolution_history' in results
        assert 'best_chromosomes' in results
        assert results['final_generation'] == 0
        assert results['total_interactions'] == 0
