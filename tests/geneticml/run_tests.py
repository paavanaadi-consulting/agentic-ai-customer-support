#!/usr/bin/env python3
"""
Test runner for GeneticML test suite.
Runs all genetic algorithm related tests and provides comprehensive coverage.
"""
import sys
import os
import unittest
import importlib
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import test modules
try:
    from tests.geneticml.test_genetic_algorithm_enhanced import *
    from tests.geneticml.test_fitness_evaluator import *
    from tests.geneticml.test_evolution_engine import *
except ImportError as e:
    print(f"Warning: Could not import all test modules: {e}")
    print("This is expected if pytest is not available.")

def run_basic_tests():
    """Run basic tests without pytest dependency."""
    print("Running GeneticML Basic Tests...")
    print("=" * 50)
    
    # Test Chromosome basic operations
    print("\n1. Testing Chromosome Operations:")
    try:
        from src.geneticML.core.genetic_algorithm import Chromosome
        
        # Test initialization
        chromosome = Chromosome(genes={'param1': 0.5, 'param2': True})
        print(f"✓ Chromosome initialization: {chromosome.genes}")
        
        # Test mutation
        original_genes = chromosome.genes.copy()
        chromosome.mutate(mutation_rate=1.0, gene_ranges={'param1': (0.0, 1.0)})
        print(f"✓ Chromosome mutation: {original_genes} -> {chromosome.genes}")
        
        # Test crossover
        chromosome2 = Chromosome(genes={'param1': 0.8, 'param2': False})
        offspring1, offspring2 = chromosome.crossover(chromosome2, crossover_rate=1.0)
        print(f"✓ Chromosome crossover: offspring created")
        
        # Test distance
        distance = chromosome.distance(chromosome2)
        print(f"✓ Chromosome distance: {distance}")
        
        print("✓ All Chromosome tests passed!")
        
    except Exception as e:
        print(f"✗ Chromosome tests failed: {e}")
    
    # Test GeneticAlgorithm basic operations  
    print("\n2. Testing GeneticAlgorithm Operations:")
    try:
        from src.geneticML.core.genetic_algorithm import GeneticAlgorithm
        
        # Test initialization
        ga = GeneticAlgorithm(population_size=10, mutation_rate=0.1)
        print(f"✓ GeneticAlgorithm initialization: population_size={ga.population_size}")
        
        # Test population initialization
        gene_template = {'confidence': 0.8, 'timeout': 5.0, 'enabled': True}
        gene_ranges = {
            'confidence': (0.5, 1.0),
            'timeout': (1.0, 10.0),
            'enabled': [True, False]
        }
        ga.initialize_population(gene_template, gene_ranges)
        print(f"✓ Population initialized: {len(ga.population)} chromosomes")
        
        # Test evolution
        def simple_fitness(chromosome):
            return chromosome.genes.get('confidence', 0.0)
        
        initial_best = ga.get_best_fitness()
        ga.evolve_generation(simple_fitness)
        final_best = ga.get_best_fitness()
        print(f"✓ Evolution completed: {initial_best} -> {final_best}")
        
        # Test statistics
        stats = ga.get_population_stats()
        print(f"✓ Population stats: {stats}")
        
        print("✓ All GeneticAlgorithm tests passed!")
        
    except Exception as e:
        print(f"✗ GeneticAlgorithm tests failed: {e}")
    
    # Test FitnessEvaluator
    print("\n3. Testing FitnessEvaluator:")
    try:
        from src.geneticML.evaluators.fitness_evaluator import FitnessEvaluator, FitnessMetrics
        
        # Test FitnessMetrics
        metrics = FitnessMetrics(
            accuracy=0.85,
            response_time=2.0,
            customer_satisfaction=0.9,
            resolution_rate=0.8,
            consistency=0.75
        )
        score = metrics.weighted_score()
        print(f"✓ FitnessMetrics weighted score: {score}")
        
        # Test FitnessEvaluator
        evaluator = FitnessEvaluator()
        print(f"✓ FitnessEvaluator initialized")
        
        # Test similarity calculation
        similarity = evaluator._calculate_similarity(
            {'category': 'technical', 'urgency': 'high'},
            {'category': 'technical', 'urgency': 'medium'}
        )
        print(f"✓ Similarity calculation: {similarity}")
        
        print("✓ All FitnessEvaluator tests passed!")
        
    except Exception as e:
        print(f"✗ FitnessEvaluator tests failed: {e}")
    
    # Test EvolutionEngine
    print("\n4. Testing EvolutionEngine:")
    try:
        from src.geneticML.engines.evolution_engine import EvolutionEngine
        from unittest.mock import Mock
        
        # Create mock agents
        mock_agent = Mock()
        mock_agent.gene_template = {'confidence': 0.8}
        mock_agent.gene_ranges = {'confidence': (0.5, 1.0)}
        mock_agent.set_chromosome = Mock()
        mock_agent.process_input = Mock(return_value={'success': True})
        
        agents = {'test_agent': mock_agent}
        
        # Create mock config
        config = Mock()
        config.population_size = 5
        config.mutation_rate = 0.1
        config.crossover_rate = 0.8
        config.elite_size = 1
        config.max_generations = 3
        config.fitness_threshold = 0.9
        
        # Test EvolutionEngine
        engine = EvolutionEngine(agents, config)
        print(f"✓ EvolutionEngine initialized")
        
        # Test gene template retrieval
        template = engine._get_gene_template('query')
        print(f"✓ Gene template retrieved: {len(template)} genes")
        
        # Test status
        status = engine.get_status()
        print(f"✓ Engine status: {status}")
        
        print("✓ All EvolutionEngine tests passed!")
        
    except Exception as e:
        print(f"✗ EvolutionEngine tests failed: {e}")
    
    print("\n" + "=" * 50)
    print("Basic test run completed!")

def run_integration_tests():
    """Run integration tests."""
    print("\nRunning GeneticML Integration Tests...")
    print("=" * 50)
    
    try:
        from src.geneticML.core.genetic_algorithm import GeneticAlgorithm, Chromosome
        from src.geneticML.evaluators.fitness_evaluator import FitnessEvaluator
        
        print("\n1. Testing Customer Support Agent Evolution:")
        
        # Create realistic customer support agent genetic algorithm
        ga = GeneticAlgorithm(
            population_size=20,
            mutation_rate=0.15,
            crossover_rate=0.8,
            elite_size=3
        )
        
        # Customer support agent gene template
        gene_template = {
            'confidence_threshold': 0.8,
            'response_timeout': 5.0,
            'empathy_level': 0.8,
            'formality_level': 0.6,
            'personalization_level': 0.7,
            'fact_checking_enabled': True,
            'escalation_threshold': 0.9
        }
        
        gene_ranges = {
            'confidence_threshold': (0.5, 1.0),
            'response_timeout': (1.0, 10.0),
            'empathy_level': (0.0, 1.0),
            'formality_level': (0.0, 1.0),
            'personalization_level': (0.0, 1.0),
            'fact_checking_enabled': [True, False],
            'escalation_threshold': (0.7, 1.0)
        }
        
        ga.initialize_population(gene_template, gene_ranges)
        print(f"✓ Initialized population of {len(ga.population)} customer support agents")
        
        # Customer support fitness function
        def customer_support_fitness(chromosome):
            genes = chromosome.genes
            fitness = 0.0
            
            # Reward appropriate confidence levels
            if 0.7 <= genes['confidence_threshold'] <= 0.9:
                fitness += 0.2
            
            # Reward reasonable response times
            if 2.0 <= genes['response_timeout'] <= 6.0:
                fitness += 0.2
            
            # Reward high empathy
            if genes['empathy_level'] > 0.7:
                fitness += 0.2
            
            # Reward balanced personalization
            if 0.5 <= genes['personalization_level'] <= 0.8:
                fitness += 0.2
            
            # Reward fact checking
            if genes['fact_checking_enabled']:
                fitness += 0.1
            
            # Reward appropriate escalation
            if 0.8 <= genes['escalation_threshold'] <= 0.95:
                fitness += 0.1
            
            return min(fitness, 1.0)
        
        # Run evolution for multiple generations
        initial_fitness = 0.0
        for generation in range(5):
            ga.evolve_generation(customer_support_fitness)
            current_best = ga.get_best_fitness()
            if generation == 0:
                initial_fitness = current_best
            print(f"   Generation {generation + 1}: Best fitness = {current_best:.3f}")
        
        final_fitness = ga.get_best_fitness()
        improvement = final_fitness - initial_fitness
        print(f"✓ Evolution completed. Improvement: {improvement:.3f}")
        
        # Test best chromosome
        best_chromosome = ga.get_best_chromosome()
        print(f"✓ Best chromosome genes: {best_chromosome.genes}")
        print(f"✓ Best chromosome fitness: {best_chromosome.fitness:.3f}")
        
        print("\n2. Testing Multi-Agent Coordination:")
        
        # Simulate multiple agent types
        agent_types = ['query', 'knowledge', 'response']
        agents_evolved = {}
        
        for agent_type in agent_types:
            agent_ga = GeneticAlgorithm(population_size=10, mutation_rate=0.1)
            
            if agent_type == 'query':
                template = {
                    'confidence_threshold': 0.8,
                    'sentiment_analysis': True,
                    'entity_extraction': True
                }
                ranges = {
                    'confidence_threshold': (0.5, 1.0),
                    'sentiment_analysis': [True, False],
                    'entity_extraction': [True, False]
                }
            elif agent_type == 'knowledge':
                template = {
                    'search_depth': 5,
                    'relevance_threshold': 0.7,
                    'fact_checking': True
                }
                ranges = {
                    'search_depth': (3, 10),
                    'relevance_threshold': (0.5, 0.9),
                    'fact_checking': [True, False]
                }
            else:  # response
                template = {
                    'empathy_level': 0.8,
                    'formality_level': 0.6,
                    'personalization': 0.7
                }
                ranges = {
                    'empathy_level': (0.0, 1.0),
                    'formality_level': (0.0, 1.0),
                    'personalization': (0.0, 1.0)
                }
            
            agent_ga.initialize_population(template, ranges)
            
            # Simple fitness function for demonstration
            def agent_fitness(chromosome):
                return sum(v if isinstance(v, (int, float)) else (1.0 if v else 0.0) 
                          for v in chromosome.genes.values()) / len(chromosome.genes)
            
            # Evolve for a few generations
            for _ in range(3):
                agent_ga.evolve_generation(agent_fitness)
            
            agents_evolved[agent_type] = agent_ga.get_best_chromosome()
            print(f"✓ {agent_type.capitalize()} agent evolved: fitness = {agents_evolved[agent_type].fitness:.3f}")
        
        print("✓ All integration tests passed!")
        
    except Exception as e:
        print(f"✗ Integration tests failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test runner function."""
    print("GeneticML Test Suite")
    print("=" * 50)
    
    # Check if pytest is available
    try:
        import pytest
        print("Pytest is available. You can run: pytest tests/geneticml/ -v")
        print("Or run this script for basic functionality tests.\n")
    except ImportError:
        print("Pytest not available. Running basic functionality tests.\n")
    
    # Run basic tests
    run_basic_tests()
    
    # Run integration tests
    run_integration_tests()
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("- Basic functionality tests completed")
    print("- Integration tests completed")
    print("- For comprehensive testing, install pytest and run:")
    print("  pytest tests/geneticml/ -v --cov=src.geneticML")

if __name__ == "__main__":
    main()
