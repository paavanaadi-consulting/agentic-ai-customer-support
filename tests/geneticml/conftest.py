"""
Pytest configuration and fixtures for GeneticML tests.
Provides common fixtures, test data, and configuration for genetic algorithm testing.
"""
import pytest
import random
import numpy as np
from unittest.mock import Mock
from typing import Dict, Any, List

# Set random seeds for reproducible tests
random.seed(42)
np.random.seed(42)


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration constants."""
    return {
        'population_size': 10,
        'mutation_rate': 0.1,
        'crossover_rate': 0.8,
        'elite_size': 2,
        'max_generations': 5,
        'fitness_threshold': 0.9,
        'timeout': 30.0
    }


@pytest.fixture
def sample_genes():
    """Provide sample gene dictionary for testing."""
    return {
        'confidence_threshold': 0.8,
        'response_timeout': 5.0,
        'max_retries': 3,
        'enable_feature_a': True,
        'strategy': 'balanced',
        'empathy_level': 0.7,
        'personalization': 0.6
    }


@pytest.fixture
def sample_gene_ranges():
    """Provide sample gene ranges for testing."""
    return {
        'confidence_threshold': (0.5, 1.0),
        'response_timeout': (1.0, 10.0),
        'max_retries': (1, 5),
        'enable_feature_a': [True, False],
        'strategy': ['aggressive', 'balanced', 'conservative'],
        'empathy_level': (0.0, 1.0),
        'personalization': (0.0, 1.0)
    }


@pytest.fixture
def customer_support_gene_template():
    """Provide realistic customer support agent gene template."""
    return {
        'confidence_threshold': 0.8,
        'context_window_size': 1000,
        'classification_detail_level': 'medium',
        'include_sentiment': True,
        'extract_entities': True,
        'urgency_detection': True,
        'response_timeout': 5.0,
        'empathy_level': 0.8,
        'formality_level': 0.6,
        'personalization_level': 0.7,
        'fact_checking_enabled': True,
        'escalation_threshold': 0.9
    }


@pytest.fixture
def customer_support_gene_ranges():
    """Provide realistic gene ranges for customer support agents."""
    return {
        'confidence_threshold': (0.5, 1.0),
        'context_window_size': (500, 2000),
        'classification_detail_level': ['low', 'medium', 'high'],
        'include_sentiment': [True, False],
        'extract_entities': [True, False],
        'urgency_detection': [True, False],
        'response_timeout': (1.0, 10.0),
        'empathy_level': (0.0, 1.0),
        'formality_level': (0.0, 1.0),
        'personalization_level': (0.0, 1.0),
        'fact_checking_enabled': [True, False],
        'escalation_threshold': (0.7, 1.0)
    }


@pytest.fixture
def sample_test_cases():
    """Provide sample test cases for fitness evaluation."""
    return [
        {
            'input': {
                'query': 'I cannot log into my account',
                'customer_id': 'test_001',
                'context': {'previous_attempts': 3}
            },
            'expected': {
                'category': 'authentication',
                'urgency': 'medium',
                'sentiment': 'negative',
                'entities': ['account', 'login'],
                'intent': 'account_access'
            }
        },
        {
            'input': {
                'query': 'How do I change my billing address?',
                'customer_id': 'test_002',
                'context': {'account_type': 'premium'}
            },
            'expected': {
                'category': 'billing',
                'urgency': 'low',
                'sentiment': 'neutral',
                'entities': ['billing', 'address'],
                'intent': 'update_info'
            }
        },
        {
            'input': {
                'query': 'Your service is terrible! I want a refund!',
                'customer_id': 'test_003',
                'context': {'tier': 'premium', 'order_value': 500}
            },
            'expected': {
                'category': 'complaint',
                'urgency': 'high',
                'sentiment': 'very_negative',
                'entities': ['refund', 'service'],
                'intent': 'refund_request',
                'escalation_needed': True
            }
        },
        {
            'input': {
                'query': 'Could you add a dark mode feature?',
                'customer_id': 'test_004',
                'context': {}
            },
            'expected': {
                'category': 'feature_request',
                'urgency': 'low',
                'sentiment': 'positive',
                'entities': ['feature', 'dark mode'],
                'intent': 'feature_suggestion'
            }
        },
        {
            'input': {
                'query': 'Thank you for the excellent support!',
                'customer_id': 'test_005',
                'context': {}
            },
            'expected': {
                'category': 'feedback',
                'urgency': 'low',
                'sentiment': 'positive',
                'entities': ['support'],
                'intent': 'positive_feedback'
            }
        }
    ]


@pytest.fixture
def mock_agent():
    """Provide a mock agent for testing."""
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
    agent.process_input = Mock(return_value={
        'success': True,
        'content': 'Mock response',
        'processing_time': 1.0,
        'confidence': 0.8
    })
    return agent


@pytest.fixture
def mock_agents():
    """Provide multiple mock agents for testing."""
    agents = {}
    
    for agent_id in ['query', 'knowledge', 'response']:
        agent = Mock()
        
        if agent_id == 'query':
            agent.gene_template = {
                'confidence_threshold': 0.8,
                'sentiment_analysis': True,
                'entity_extraction': True
            }
            agent.gene_ranges = {
                'confidence_threshold': (0.5, 1.0),
                'sentiment_analysis': [True, False],
                'entity_extraction': [True, False]
            }
        elif agent_id == 'knowledge':
            agent.gene_template = {
                'search_depth': 5,
                'relevance_threshold': 0.7,
                'fact_checking': True
            }
            agent.gene_ranges = {
                'search_depth': (3, 10),
                'relevance_threshold': (0.5, 0.9),
                'fact_checking': [True, False]
            }
        else:  # response
            agent.gene_template = {
                'empathy_level': 0.8,
                'formality_level': 0.6,
                'personalization': 0.7
            }
            agent.gene_ranges = {
                'empathy_level': (0.0, 1.0),
                'formality_level': (0.0, 1.0),
                'personalization': (0.0, 1.0)
            }
        
        agent.set_chromosome = Mock()
        agent.process_input = Mock(return_value={
            'success': True,
            'content': f'Mock response from {agent_id}',
            'processing_time': 1.0 + random.random(),
            'confidence': 0.7 + random.random() * 0.3
        })
        
        agents[agent_id] = agent
    
    return agents


@pytest.fixture
def mock_evolution_config():
    """Provide mock evolution configuration."""
    config = Mock()
    config.population_size = 10
    config.mutation_rate = 0.1
    config.crossover_rate = 0.8
    config.elite_size = 2
    config.max_generations = 5
    config.fitness_threshold = 0.9
    return config


@pytest.fixture
def fitness_function_simple():
    """Provide a simple fitness function for testing."""
    def fitness_fn(chromosome):
        # Simple fitness based on confidence threshold
        return chromosome.genes.get('confidence_threshold', 0.0)
    return fitness_fn


@pytest.fixture
def fitness_function_customer_support():
    """Provide a realistic customer support fitness function."""
    def fitness_fn(chromosome):
        genes = chromosome.genes
        fitness = 0.0
        
        # Reward appropriate confidence levels
        conf = genes.get('confidence_threshold', 0.0)
        if 0.7 <= conf <= 0.9:
            fitness += 0.2
        
        # Reward reasonable response times
        timeout = genes.get('response_timeout', 0.0)
        if 2.0 <= timeout <= 6.0:
            fitness += 0.2
        
        # Reward high empathy
        empathy = genes.get('empathy_level', 0.0)
        if empathy > 0.7:
            fitness += 0.2
        
        # Reward balanced personalization
        personal = genes.get('personalization_level', 0.0)
        if 0.5 <= personal <= 0.8:
            fitness += 0.2
        
        # Reward fact checking
        if genes.get('fact_checking_enabled', False):
            fitness += 0.1
        
        # Reward appropriate escalation
        escalation = genes.get('escalation_threshold', 0.0)
        if 0.8 <= escalation <= 0.95:
            fitness += 0.1
        
        return min(fitness, 1.0)
    
    return fitness_fn


@pytest.fixture(autouse=True)
def reset_random_state():
    """Reset random state before each test for reproducibility."""
    random.seed(42)
    np.random.seed(42)


# Configure pytest
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test items based on markers."""
    # Mark slow tests
    slow_keywords = ["evolution", "large_population", "performance"]
    
    for item in items:
        # Mark tests as slow if they contain slow keywords
        if any(keyword in item.name.lower() for keyword in slow_keywords):
            item.add_marker(pytest.mark.slow)
        
        # Mark tests as integration if they're in integration test classes
        if "Integration" in str(item.cls):
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)


# Custom assertions for genetic algorithm testing
def assert_valid_chromosome(chromosome, gene_template=None):
    """Assert that a chromosome is valid."""
    from src.geneticML.core.genetic_algorithm import Chromosome
    
    assert isinstance(chromosome, Chromosome)
    assert isinstance(chromosome.genes, dict)
    assert isinstance(chromosome.fitness, (int, float))
    assert isinstance(chromosome.generation, int)
    assert isinstance(chromosome.age, int)
    
    if gene_template:
        assert set(chromosome.genes.keys()) == set(gene_template.keys())


def assert_fitness_improved(initial_fitness, final_fitness, tolerance=0.01):
    """Assert that fitness improved or stayed stable within tolerance."""
    assert final_fitness >= initial_fitness - tolerance, \
        f"Fitness decreased: {initial_fitness} -> {final_fitness}"


def assert_gene_in_range(gene_value, gene_range):
    """Assert that a gene value is within its specified range."""
    if isinstance(gene_range, tuple) and len(gene_range) == 2:
        min_val, max_val = gene_range
        assert min_val <= gene_value <= max_val, \
            f"Gene value {gene_value} not in range [{min_val}, {max_val}]"
    elif isinstance(gene_range, list):
        assert gene_value in gene_range, \
            f"Gene value {gene_value} not in allowed values {gene_range}"


# Make custom assertions available globally
pytest.assert_valid_chromosome = assert_valid_chromosome
pytest.assert_fitness_improved = assert_fitness_improved
pytest.assert_gene_in_range = assert_gene_in_range
