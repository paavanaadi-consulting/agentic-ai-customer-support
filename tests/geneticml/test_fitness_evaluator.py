"""
Comprehensive test suite for FitnessEvaluator.
Tests fitness evaluation, metrics calculation, and performance assessment.
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from src.geneticML.evaluators.fitness_evaluator import FitnessEvaluator, FitnessMetrics
from src.geneticML.core.genetic_algorithm import Chromosome


class TestFitnessMetrics:
    """Test cases for FitnessMetrics class."""

    def test_fitness_metrics_initialization(self):
        """Test FitnessMetrics initialization with default values."""
        metrics = FitnessMetrics()
        
        assert metrics.accuracy == 0.0
        assert metrics.response_time == 0.0
        assert metrics.customer_satisfaction == 0.0
        assert metrics.resolution_rate == 0.0
        assert metrics.consistency == 0.0

    def test_fitness_metrics_custom_values(self):
        """Test FitnessMetrics initialization with custom values."""
        metrics = FitnessMetrics(
            accuracy=0.85,
            response_time=2.5,
            customer_satisfaction=0.9,
            resolution_rate=0.8,
            consistency=0.75
        )
        
        assert metrics.accuracy == 0.85
        assert metrics.response_time == 2.5
        assert metrics.customer_satisfaction == 0.9
        assert metrics.resolution_rate == 0.8
        assert metrics.consistency == 0.75

    def test_weighted_score_default_weights(self):
        """Test weighted score calculation with default weights."""
        metrics = FitnessMetrics(
            accuracy=0.8,
            response_time=2.0,
            customer_satisfaction=0.9,
            resolution_rate=0.85,
            consistency=0.75
        )
        
        score = metrics.weighted_score()
        
        # Verify score is between 0 and 1
        assert 0.0 <= score <= 1.0
        
        # Calculate expected score manually
        expected = (
            0.25 * 0.8 +  # accuracy
            0.20 * (1.0 / (1.0 + 2.0)) +  # response_time (inverted)
            0.25 * 0.9 +  # customer_satisfaction
            0.20 * 0.85 +  # resolution_rate
            0.10 * 0.75   # consistency
        )
        
        assert abs(score - expected) < 1e-6

    def test_weighted_score_custom_weights(self):
        """Test weighted score calculation with custom weights."""
        metrics = FitnessMetrics(
            accuracy=0.8,
            response_time=1.0,
            customer_satisfaction=0.9,
            resolution_rate=0.85,
            consistency=0.75
        )
        
        custom_weights = {
            'accuracy': 0.4,
            'response_time': 0.1,
            'customer_satisfaction': 0.3,
            'resolution_rate': 0.15,
            'consistency': 0.05
        }
        
        score = metrics.weighted_score(custom_weights)
        
        # Calculate expected score
        expected = (
            0.4 * 0.8 +
            0.1 * (1.0 / (1.0 + 1.0)) +
            0.3 * 0.9 +
            0.15 * 0.85 +
            0.05 * 0.75
        )
        
        assert abs(score - expected) < 1e-6

    def test_weighted_score_boundary_values(self):
        """Test weighted score with boundary values."""
        # All zeros
        metrics_zeros = FitnessMetrics()
        score_zeros = metrics_zeros.weighted_score()
        assert score_zeros >= 0.0
        
        # All ones (except response_time which should be 0 for best score)
        metrics_ones = FitnessMetrics(
            accuracy=1.0,
            response_time=0.0,
            customer_satisfaction=1.0,
            resolution_rate=1.0,
            consistency=1.0
        )
        score_ones = metrics_ones.weighted_score()
        assert score_ones <= 1.0


class TestFitnessEvaluator:
    """Test cases for FitnessEvaluator class."""

    @pytest.fixture
    def fitness_evaluator(self):
        """Create a FitnessEvaluator instance for testing."""
        return FitnessEvaluator()

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        agent = Mock()
        agent.set_chromosome = Mock()
        agent.process_input = Mock()
        return agent

    @pytest.fixture
    def sample_chromosome(self):
        """Create a sample chromosome for testing."""
        return Chromosome(
            genes={
                'confidence_threshold': 0.8,
                'response_timeout': 5.0,
                'max_retries': 3
            }
        )

    @pytest.fixture
    def sample_test_cases(self):
        """Create sample test cases for fitness evaluation."""
        return [
            {
                'input': {
                    'query': 'How do I reset my password?',
                    'customer_id': 'test_001'
                },
                'expected': {
                    'category': 'technical',
                    'urgency': 'medium',
                    'sentiment': 'neutral'
                }
            },
            {
                'input': {
                    'query': 'I want a refund immediately!',
                    'customer_id': 'test_002'
                },
                'expected': {
                    'category': 'billing',
                    'urgency': 'high',
                    'sentiment': 'negative'
                }
            },
            {
                'input': {
                    'query': 'Thank you for the great service',
                    'customer_id': 'test_003'
                },
                'expected': {
                    'category': 'feedback',
                    'urgency': 'low',
                    'sentiment': 'positive'
                }
            }
        ]

    def test_fitness_evaluator_initialization(self, fitness_evaluator):
        """Test FitnessEvaluator initialization."""
        assert fitness_evaluator.historical_data == []
        assert fitness_evaluator.baseline_metrics is None
        assert fitness_evaluator.logger is not None

    def test_evaluate_chromosome_empty_test_cases(self, fitness_evaluator, mock_agent, sample_chromosome):
        """Test chromosome evaluation with empty test cases."""
        fitness = fitness_evaluator.evaluate_chromosome(sample_chromosome, mock_agent, [])
        
        assert fitness == 0.0
        mock_agent.set_chromosome.assert_not_called()

    def test_evaluate_chromosome_successful_cases(self, fitness_evaluator, mock_agent, sample_chromosome, sample_test_cases):
        """Test chromosome evaluation with successful test cases."""
        # Mock successful agent responses
        mock_responses = [
            {
                'success': True,
                'content': 'Here is how to reset your password...',
                'processing_time': 1.5,
                'category': 'technical',
                'urgency': 'medium',
                'sentiment': 'neutral'
            },
            {
                'success': True,
                'content': 'I understand your frustration. Let me help with the refund...',
                'processing_time': 2.0,
                'category': 'billing',
                'urgency': 'high',
                'sentiment': 'negative'
            },
            {
                'success': True,
                'content': 'Thank you for your feedback!',
                'processing_time': 0.8,
                'category': 'feedback',
                'urgency': 'low',
                'sentiment': 'positive'
            }
        ]
        
        mock_agent.process_input.side_effect = mock_responses
        
        fitness = fitness_evaluator.evaluate_chromosome(sample_chromosome, mock_agent, sample_test_cases)
        
        # Verify agent was configured with chromosome
        mock_agent.set_chromosome.assert_called_once_with(sample_chromosome)
        
        # Verify agent was called for each test case
        assert mock_agent.process_input.call_count == len(sample_test_cases)
        
        # Verify fitness is reasonable (should be > 0 for successful cases)
        assert fitness > 0.0
        assert fitness <= 1.0
        
        # Verify chromosome fitness was updated
        assert sample_chromosome.fitness == fitness

    def test_evaluate_chromosome_failed_cases(self, fitness_evaluator, mock_agent, sample_chromosome, sample_test_cases):
        """Test chromosome evaluation with failed test cases."""
        # Mock failed agent responses
        mock_agent.process_input.side_effect = [
            {'success': False, 'error': 'Processing failed'},
            Exception("Agent crashed"),
            {'success': False, 'content': ''}
        ]
        
        fitness = fitness_evaluator.evaluate_chromosome(sample_chromosome, mock_agent, sample_test_cases)
        
        # Fitness should be low for failed cases
        assert fitness >= 0.0
        assert fitness < 0.5  # Should be less than 50% due to failures

    def test_evaluate_chromosome_mixed_results(self, fitness_evaluator, mock_agent, sample_chromosome, sample_test_cases):
        """Test chromosome evaluation with mixed success/failure results."""
        mock_responses = [
            {
                'success': True,
                'content': 'Password reset instructions...',
                'processing_time': 1.0,
                'category': 'technical'
            },
            {'success': False, 'error': 'Service unavailable'},
            {
                'success': True,
                'content': 'Thank you!',
                'processing_time': 0.5,
                'category': 'feedback'
            }
        ]
        
        mock_agent.process_input.side_effect = mock_responses
        
        fitness = fitness_evaluator.evaluate_chromosome(sample_chromosome, mock_agent, sample_test_cases)
        
        # Should have moderate fitness (some success, some failure)
        assert 0.0 < fitness < 1.0

    def test_calculate_metrics_empty_results(self, fitness_evaluator):
        """Test metrics calculation with empty results."""
        metrics = fitness_evaluator._calculate_metrics([])
        
        assert metrics.accuracy == 0.0
        assert metrics.response_time == 0.0
        assert metrics.customer_satisfaction == 0.0
        assert metrics.resolution_rate == 0.0
        assert metrics.consistency == 0.0

    def test_calculate_metrics_all_successful(self, fitness_evaluator):
        """Test metrics calculation with all successful results."""
        results = [
            {
                'success': True,
                'result': {
                    'content': 'Good response',
                    'processing_time': 1.0,
                    'category': 'technical'
                },
                'test_case': {
                    'expected': {'category': 'technical', 'sentiment': 'neutral'}
                }
            },
            {
                'success': True,
                'result': {
                    'content': 'Another good response',
                    'processing_time': 1.5,
                    'category': 'billing'
                },
                'test_case': {
                    'expected': {'category': 'billing', 'sentiment': 'negative'}
                }
            }
        ]
        
        metrics = fitness_evaluator._calculate_metrics(results)
        
        assert metrics.accuracy == 1.0  # All successful
        assert metrics.resolution_rate == 1.0  # All have meaningful content
        assert metrics.response_time > 0.0  # Average processing time
        assert metrics.customer_satisfaction >= 0.0
        assert metrics.consistency >= 0.0

    def test_calculate_metrics_mixed_results(self, fitness_evaluator):
        """Test metrics calculation with mixed results."""
        results = [
            {
                'success': True,
                'result': {
                    'content': 'Good response',
                    'processing_time': 1.0
                },
                'test_case': {'expected': {}}
            },
            {
                'success': False,
                'result': {'error': 'Failed'},
                'test_case': {'expected': {}}
            },
            {
                'success': True,
                'result': {
                    'content': 'Short',  # Less than 10 characters
                    'processing_time': 0.5
                },
                'test_case': {'expected': {}}
            }
        ]
        
        metrics = fitness_evaluator._calculate_metrics(results)
        
        assert metrics.accuracy == 2/3  # 2 out of 3 successful
        assert metrics.resolution_rate == 1/3  # Only 1 has meaningful content (>10 chars)

    def test_calculate_similarity_exact_match(self, fitness_evaluator):
        """Test similarity calculation with exact matches."""
        expected = {'category': 'technical', 'urgency': 'high'}
        actual = {'category': 'technical', 'urgency': 'high'}
        
        similarity = fitness_evaluator._calculate_similarity(expected, actual)
        
        assert similarity == 1.0

    def test_calculate_similarity_partial_match(self, fitness_evaluator):
        """Test similarity calculation with partial matches."""
        expected = {'category': 'technical support', 'urgency': 'high'}
        actual = {'category': 'technical', 'urgency': 'high'}
        
        similarity = fitness_evaluator._calculate_similarity(expected, actual)
        
        assert 0.0 < similarity < 1.0

    def test_calculate_similarity_no_match(self, fitness_evaluator):
        """Test similarity calculation with no matches."""
        expected = {'category': 'technical', 'urgency': 'high'}
        actual = {'category': 'billing', 'urgency': 'low'}
        
        similarity = fitness_evaluator._calculate_similarity(expected, actual)
        
        assert similarity >= 0.0

    def test_calculate_similarity_no_common_keys(self, fitness_evaluator):
        """Test similarity calculation with no common keys."""
        expected = {'category': 'technical'}
        actual = {'urgency': 'high'}
        
        similarity = fitness_evaluator._calculate_similarity(expected, actual)
        
        assert similarity == 0.0

    def test_calculate_similarity_empty_dicts(self, fitness_evaluator):
        """Test similarity calculation with empty dictionaries."""
        similarity = fitness_evaluator._calculate_similarity({}, {})
        assert similarity == 0.0

    def test_calculate_similarity_jaccard_text(self, fitness_evaluator):
        """Test Jaccard similarity for text content."""
        expected = {'content': 'password reset help'}
        actual = {'content': 'help with password reset process'}
        
        similarity = fitness_evaluator._calculate_similarity(expected, actual)
        
        # Should have some similarity due to overlapping words
        assert similarity > 0.0


class TestFitnessEvaluatorIntegration:
    """Integration tests for FitnessEvaluator with real-world scenarios."""

    @pytest.fixture
    def fitness_evaluator(self):
        """Create a FitnessEvaluator instance for testing."""
        return FitnessEvaluator()

    @pytest.fixture
    def comprehensive_test_cases(self):
        """Create comprehensive test cases for integration testing."""
        return [
            {
                'input': {
                    'query': 'I forgot my password and cannot access my account',
                    'customer_id': 'cust_001',
                    'context': {'previous_attempts': 2}
                },
                'expected': {
                    'category': 'authentication',
                    'urgency': 'medium',
                    'sentiment': 'neutral',
                    'entities': ['password', 'account'],
                    'intent': 'password_reset'
                }
            },
            {
                'input': {
                    'query': 'This is completely unacceptable! I demand a full refund now!',
                    'customer_id': 'cust_002',
                    'context': {'tier': 'premium', 'order_value': 500}
                },
                'expected': {
                    'category': 'billing',
                    'urgency': 'high',
                    'sentiment': 'very_negative',
                    'entities': ['refund'],
                    'intent': 'refund_request',
                    'escalation_needed': True
                }
            },
            {
                'input': {
                    'query': 'How can I upgrade my plan to get more features?',
                    'customer_id': 'cust_003',
                    'context': {'current_plan': 'basic'}
                },
                'expected': {
                    'category': 'sales',
                    'urgency': 'low',
                    'sentiment': 'positive',
                    'entities': ['upgrade', 'plan', 'features'],
                    'intent': 'upgrade_request'
                }
            }
        ]

    def test_performance_evaluation_realistic_scenario(self, fitness_evaluator, comprehensive_test_cases):
        """Test fitness evaluation in a realistic customer support scenario."""
        # Create a mock agent that performs reasonably well
        mock_agent = Mock()
        
        def realistic_agent_response(input_data):
            query = input_data['query'].lower()
            
            if 'password' in query:
                return {
                    'success': True,
                    'content': 'I can help you reset your password. Please check your email for reset instructions.',
                    'processing_time': 1.2,
                    'category': 'authentication',
                    'urgency': 'medium',
                    'sentiment': 'neutral',
                    'confidence': 0.85
                }
            elif 'refund' in query:
                return {
                    'success': True,
                    'content': 'I understand your concern. Let me escalate this to our billing team for immediate attention.',
                    'processing_time': 2.1,
                    'category': 'billing',
                    'urgency': 'high',
                    'sentiment': 'negative',
                    'confidence': 0.92
                }
            elif 'upgrade' in query:
                return {
                    'success': True,
                    'content': 'I would be happy to help you upgrade your plan. Here are the available options...',
                    'processing_time': 1.8,
                    'category': 'sales',
                    'urgency': 'low',
                    'sentiment': 'positive',
                    'confidence': 0.88
                }
            else:
                return {
                    'success': False,
                    'error': 'Unable to process query',
                    'processing_time': 5.0
                }
        
        mock_agent.process_input.side_effect = realistic_agent_response
        
        sample_chromosome = Chromosome(genes={'confidence_threshold': 0.8})
        
        fitness = fitness_evaluator.evaluate_chromosome(
            sample_chromosome, mock_agent, comprehensive_test_cases
        )
        
        # Should achieve good fitness with realistic responses
        assert fitness > 0.7  # Should be quite good
        assert fitness <= 1.0

    def test_poor_performance_scenario(self, fitness_evaluator, comprehensive_test_cases):
        """Test fitness evaluation with poor agent performance."""
        mock_agent = Mock()
        
        def poor_agent_response(input_data):
            return {
                'success': True,
                'content': 'I do not understand',  # Generic, unhelpful response
                'processing_time': 10.0,  # Very slow
                'category': 'unknown',
                'confidence': 0.1
            }
        
        mock_agent.process_input.side_effect = poor_agent_response
        
        sample_chromosome = Chromosome(genes={'confidence_threshold': 0.8})
        
        fitness = fitness_evaluator.evaluate_chromosome(
            sample_chromosome, mock_agent, comprehensive_test_cases
        )
        
        # Should achieve low fitness with poor responses
        assert fitness < 0.5

    def test_inconsistent_performance_scenario(self, fitness_evaluator, comprehensive_test_cases):
        """Test fitness evaluation with inconsistent agent performance."""
        mock_agent = Mock()
        
        responses = [
            # Good response
            {
                'success': True,
                'content': 'Excellent response with detailed help',
                'processing_time': 1.0,
                'category': 'authentication',
                'sentiment': 'neutral'
            },
            # Poor response
            {
                'success': False,
                'error': 'System error',
                'processing_time': 8.0
            },
            # Average response
            {
                'success': True,
                'content': 'Okay response',
                'processing_time': 3.0,
                'category': 'sales'
            }
        ]
        
        mock_agent.process_input.side_effect = responses
        
        sample_chromosome = Chromosome(genes={'confidence_threshold': 0.8})
        
        fitness = fitness_evaluator.evaluate_chromosome(
            sample_chromosome, mock_agent, comprehensive_test_cases
        )
        
        # Should have moderate fitness due to inconsistency
        assert 0.2 < fitness < 0.8

    @pytest.mark.asyncio
    async def test_concurrent_evaluations(self, fitness_evaluator):
        """Test concurrent fitness evaluations for performance."""
        import asyncio
        
        # Create multiple agents and chromosomes
        agents = []
        chromosomes = []
        test_cases = [
            {
                'input': {'query': 'test query'},
                'expected': {'category': 'test'}
            }
        ]
        
        for i in range(5):
            agent = Mock()
            agent.process_input.return_value = {
                'success': True,
                'content': f'Response {i}',
                'processing_time': 1.0
            }
            agents.append(agent)
            
            chromosome = Chromosome(genes={'param': i * 0.2})
            chromosomes.append(chromosome)
        
        # Evaluate all chromosomes (simulating concurrent evaluation)
        fitness_scores = []
        for agent, chromosome in zip(agents, chromosomes):
            fitness = fitness_evaluator.evaluate_chromosome(chromosome, agent, test_cases)
            fitness_scores.append(fitness)
        
        # All should have reasonable fitness scores
        assert all(score > 0.0 for score in fitness_scores)
        assert len(fitness_scores) == 5


class TestFitnessEvaluatorEdgeCases:
    """Test edge cases and error conditions for FitnessEvaluator."""

    @pytest.fixture
    def fitness_evaluator(self):
        """Create a FitnessEvaluator instance for testing."""
        return FitnessEvaluator()

    def test_agent_exception_handling(self, fitness_evaluator):
        """Test handling of agent exceptions during evaluation."""
        mock_agent = Mock()
        mock_agent.process_input.side_effect = Exception("Agent crashed")
        
        chromosome = Chromosome(genes={'test': 1.0})
        test_cases = [{'input': {'query': 'test'}, 'expected': {}}]
        
        # Should not raise exception, should return low fitness
        fitness = fitness_evaluator.evaluate_chromosome(chromosome, mock_agent, test_cases)
        
        assert fitness >= 0.0
        assert fitness <= 1.0

    def test_malformed_test_cases(self, fitness_evaluator):
        """Test handling of malformed test cases."""
        mock_agent = Mock()
        mock_agent.process_input.return_value = {'success': True}
        
        chromosome = Chromosome(genes={'test': 1.0})
        
        # Test cases without required fields
        malformed_cases = [
            {},  # Empty test case
            {'input': {}},  # Missing expected
            {'expected': {}},  # Missing input
        ]
        
        fitness = fitness_evaluator.evaluate_chromosome(chromosome, mock_agent, malformed_cases)
        
        # Should handle gracefully
        assert fitness >= 0.0

    def test_extreme_response_times(self, fitness_evaluator):
        """Test handling of extreme response times."""
        mock_agent = Mock()
        mock_agent.process_input.return_value = {
            'success': True,
            'content': 'Response',
            'processing_time': 999999.0  # Extremely high response time
        }
        
        chromosome = Chromosome(genes={'test': 1.0})
        test_cases = [{'input': {'query': 'test'}, 'expected': {}}]
        
        fitness = fitness_evaluator.evaluate_chromosome(chromosome, mock_agent, test_cases)
        
        # Should penalize high response time
        assert fitness < 0.8

    def test_unicode_and_special_characters(self, fitness_evaluator):
        """Test handling of unicode and special characters in responses."""
        mock_agent = Mock()
        mock_agent.process_input.return_value = {
            'success': True,
            'content': 'Response with émojis 🎉 and spëcial çhars',
            'processing_time': 1.0,
            'category': 'tëst'
        }
        
        chromosome = Chromosome(genes={'test': 1.0})
        test_cases = [
            {
                'input': {'query': 'tëst qüery with émojis 🤔'},
                'expected': {'category': 'tëst'}
            }
        ]
        
        # Should handle unicode gracefully
        fitness = fitness_evaluator.evaluate_chromosome(chromosome, mock_agent, test_cases)
        
        assert fitness >= 0.0
        assert fitness <= 1.0
