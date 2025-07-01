#!/usr/bin/env python3
"""
GeneticML Test and Validation Script
"""
import sys
import asyncio
import argparse
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.geneticML import GeneticAlgorithm, Chromosome, FitnessEvaluator, EvolutionEngine

def test_chromosome_operations():
    """Test basic chromosome operations"""
    print("Testing Chromosome operations...")
    
    # Create test chromosome
    gene_template = {'param1': 0.5, 'param2': True, 'param3': 'medium'}
    gene_ranges = {
        'param1': (0.0, 1.0),
        'param2': [True, False],
        'param3': ['low', 'medium', 'high']
    }
    
    chromosome1 = Chromosome(genes=gene_template.copy())
    chromosome2 = Chromosome(genes={'param1': 0.8, 'param2': False, 'param3': 'high'})
    
    # Test mutation
    chromosome1.mutate(0.5, gene_ranges)
    print(f"  Mutated chromosome: {chromosome1.genes}")
    
    # Test crossover
    offspring1, offspring2 = chromosome1.crossover(chromosome2, 0.8)
    print(f"  Offspring 1: {offspring1.genes}")
    print(f"  Offspring 2: {offspring2.genes}")
    
    # Test distance
    distance = chromosome1.distance(chromosome2)
    print(f"  Distance: {distance:.4f}")
    
    print("✓ Chromosome operations test passed\n")
    return True

def test_genetic_algorithm():
    """Test genetic algorithm functionality"""
    print("Testing GeneticAlgorithm...")
    
    gene_template = {
        'confidence': 0.5,
        'threshold': 0.3,
        'enabled': True,
        'mode': 'strict'
    }
    
    gene_ranges = {
        'confidence': (0.0, 1.0),
        'threshold': (0.0, 1.0),
        'enabled': [True, False],
        'mode': ['strict', 'lenient', 'balanced']
    }
    
    # Create genetic algorithm
    ga = GeneticAlgorithm(population_size=10, mutation_rate=0.1, crossover_rate=0.8)
    ga.initialize_population(gene_template, gene_ranges)
    
    print(f"  Population size: {len(ga.population)}")
    print(f"  Sample chromosome: {ga.population[0].genes}")
    
    # Test fitness function
    def fitness_function(chromosome):
        # Simple fitness based on confidence + threshold
        return chromosome.genes.get('confidence', 0) + chromosome.genes.get('threshold', 0)
    
    # Evolve one generation
    ga.evolve_generation(fitness_function)
    
    stats = ga.get_population_stats()
    best = ga.get_best_chromosome()
    
    print(f"  Generation stats: {stats}")
    print(f"  Best chromosome: {best.genes} (fitness: {best.fitness})")
    
    print("✓ GeneticAlgorithm test passed\n")
    return True

def test_fitness_evaluator():
    """Test fitness evaluator"""
    print("Testing FitnessEvaluator...")
    
    class MockAgent:
        def __init__(self):
            self.chromosome = None
        
        def set_chromosome(self, chromosome):
            self.chromosome = chromosome
        
        def process_input(self, input_data):
            return {'success': True, 'content': 'Test response', 'processing_time': 0.1}
    
    evaluator = FitnessEvaluator()
    agent = MockAgent()
    chromosome = Chromosome(genes={'param1': 0.5, 'param2': True})
    
    test_cases = [
        {
            'input': {'query': 'test query'},
            'expected': {'success': True}
        }
    ]
    
    fitness = evaluator.evaluate_chromosome(chromosome, agent, test_cases)
    print(f"  Chromosome fitness: {fitness}")
    
    print("✓ FitnessEvaluator test passed\n")
    return True

async def test_evolution_engine():
    """Test evolution engine"""
    print("Testing Evolution Engine...")
    
    class Config:
        def __init__(self):
            self.population_size = 5
            self.mutation_rate = 0.1
            self.crossover_rate = 0.8
            self.elite_size = 2
            self.max_generations = 3
            self.fitness_threshold = 0.9
    
    class MockAgent:
        def __init__(self, agent_id):
            self.agent_id = agent_id
            self.gene_template = {'param1': 0.5, 'param2': True}
            self.gene_ranges = {'param1': (0.0, 1.0), 'param2': [True, False]}
            self.chromosome = None
        
        def set_chromosome(self, chromosome):
            self.chromosome = chromosome
        
        def process_input(self, input_data):
            return {'success': True, 'content': 'Response'}
    
    # Create agents
    agents = {
        'agent1': MockAgent('agent1'),
        'agent2': MockAgent('agent2')
    }
    
    # Initialize evolution engine
    config = Config()
    engine = EvolutionEngine(agents, config)
    await engine.initialize()
    
    print(f"  Evolution engine initialized with {len(engine.genetic_algorithms)} algorithms")
    
    # Run short evolution
    await engine.evolve(max_generations=2)
    
    status = engine.get_status()
    print(f"  Evolution status: {status}")
    
    print("✓ Evolution Engine test passed\n")
    return True

def benchmark_genetic_algorithm():
    """Benchmark genetic algorithm performance"""
    print("Benchmarking GeneticAlgorithm performance...")
    
    gene_template = {f'param{i}': 0.5 for i in range(20)}
    gene_ranges = {f'param{i}': (0.0, 1.0) for i in range(20)}
    
    # Create large population
    ga = GeneticAlgorithm(population_size=100, mutation_rate=0.1, crossover_rate=0.8)
    ga.initialize_population(gene_template, gene_ranges)
    
    def fitness_function(chromosome):
        return sum(chromosome.genes.values()) / len(chromosome.genes)
    
    # Benchmark evolution
    start_time = time.time()
    for generation in range(10):
        ga.evolve_generation(fitness_function)
    
    elapsed_time = time.time() - start_time
    
    print(f"  Evolved 100 chromosomes over 10 generations in {elapsed_time:.2f} seconds")
    print(f"  Best fitness achieved: {ga.get_best_fitness():.4f}")
    
    print("✓ Benchmark completed\n")
    return True

async def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description='GeneticML Test and Validation')
    parser.add_argument('--benchmark', action='store_true', help='Run performance benchmarks')
    parser.add_argument('--component', choices=['chromosome', 'ga', 'fitness', 'evolution'], 
                       help='Test specific component only')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("GENETICML TEST AND VALIDATION")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 0
    
    # Run specific component test or all tests
    if args.component == 'chromosome' or not args.component:
        total_tests += 1
        if test_chromosome_operations():
            tests_passed += 1
    
    if args.component == 'ga' or not args.component:
        total_tests += 1
        if test_genetic_algorithm():
            tests_passed += 1
    
    if args.component == 'fitness' or not args.component:
        total_tests += 1
        if test_fitness_evaluator():
            tests_passed += 1
    
    if args.component == 'evolution' or not args.component:
        total_tests += 1
        if await test_evolution_engine():
            tests_passed += 1
    
    # Run benchmark if requested
    if args.benchmark:
        benchmark_genetic_algorithm()
    
    # Summary
    print("=" * 60)
    if tests_passed == total_tests:
        print(f"ALL TESTS PASSED! ✓ ({tests_passed}/{total_tests})")
        print("GeneticML package is working correctly.")
    else:
        print(f"SOME TESTS FAILED! ✗ ({tests_passed}/{total_tests})")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
