import pytest
from core.fitness_evaluator import FitnessEvaluator, FitnessMetrics

class DummyAgent:
    def set_chromosome(self, chromosome):
        self.chromosome = chromosome
    def process_input(self, input_data):
        # Simulate a successful response
        return {
            'success': True,
            'processing_time': 0.5,
            'content': 'response',
            'category': input_data.get('query', ''),
            'sentiment': 'positive',
            'urgency': 'low'
        }

def test_fitness_metrics_weighted_score():
    metrics = FitnessMetrics(accuracy=1, response_time=1, customer_satisfaction=1, resolution_rate=1, consistency=1)
    score = metrics.weighted_score()
    assert 0 <= score <= 1

def test_evaluate_chromosome():
    evaluator = FitnessEvaluator()
    agent = DummyAgent()
    chromosome = type('Chromosome', (), {})()
    test_cases = [
        {'input': {'query': 'test'}, 'expected': {'category': 'test', 'sentiment': 'positive', 'urgency': 'low'}}
    ]
    fitness = evaluator.evaluate_chromosome(chromosome, agent, test_cases)
    assert 0 <= fitness <= 1

def test_calculate_similarity_exact():
    evaluator = FitnessEvaluator()
    expected = {'category': 'billing'}
    actual = {'category': 'billing'}
    sim = evaluator._calculate_similarity(expected, actual)
    assert sim == 1.0

def test_calculate_similarity_partial():
    evaluator = FitnessEvaluator()
    expected = {'category': 'billing'}
    actual = {'category': 'bill'}
    sim = evaluator._calculate_similarity(expected, actual)
    assert 0 < sim < 1.0
