"""
Performance benchmark tests for GeneticML components.
Tests performance characteristics, scalability, and optimization efficiency.
"""
import sys
import os
import time
import statistics
import random
import numpy as np
from typing import List, Dict, Any
from unittest.mock import Mock
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.geneticML.core.genetic_algorithm import GeneticAlgorithm, Chromosome
from src.geneticML.evaluators.fitness_evaluator import FitnessEvaluator
from src.geneticML.engines.evolution_engine import EvolutionEngine


class PerformanceBenchmark:
    """Performance benchmark suite for GeneticML components."""
    
    def __init__(self):
        self.results = {}
    
    def benchmark_chromosome_operations(self, num_iterations: int = 1000):
        """Benchmark basic chromosome operations."""
        print(f"Benchmarking Chromosome Operations ({num_iterations} iterations)...")
        
        # Setup
        genes = {f'param_{i}': random.random() for i in range(10)}
        gene_ranges = {f'param_{i}': (0.0, 1.0) for i in range(10)}
        
        # Benchmark mutation
        mutation_times = []
        for _ in range(num_iterations):
            chromosome = Chromosome(genes=genes.copy())
            
            start_time = time.time()
            chromosome.mutate(mutation_rate=0.1, gene_ranges=gene_ranges)
            mutation_times.append(time.time() - start_time)
        
        avg_mutation_time = statistics.mean(mutation_times)
        
        # Benchmark crossover
        crossover_times = []
        chromosome1 = Chromosome(genes=genes.copy())
        chromosome2 = Chromosome(genes={f'param_{i}': random.random() for i in range(10)})
        
        for _ in range(num_iterations):
            start_time = time.time()
            offspring1, offspring2 = chromosome1.crossover(chromosome2, crossover_rate=1.0)
            crossover_times.append(time.time() - start_time)
        
        avg_crossover_time = statistics.mean(crossover_times)
        
        # Benchmark distance calculation
        distance_times = []
        for _ in range(num_iterations):
            start_time = time.time()
            distance = chromosome1.distance(chromosome2)
            distance_times.append(time.time() - start_time)
        
        avg_distance_time = statistics.mean(distance_times)
        
        self.results['chromosome_operations'] = {
            'mutation_time_ms': avg_mutation_time * 1000,
            'crossover_time_ms': avg_crossover_time * 1000,
            'distance_time_ms': avg_distance_time * 1000,
            'iterations': num_iterations
        }
        
        print(f"  Mutation: {avg_mutation_time * 1000:.4f} ms/operation")
        print(f"  Crossover: {avg_crossover_time * 1000:.4f} ms/operation")
        print(f"  Distance: {avg_distance_time * 1000:.4f} ms/operation")
    
    def benchmark_population_sizes(self, sizes: List[int] = None):
        """Benchmark genetic algorithm with different population sizes."""
        if sizes is None:
            sizes = [10, 25, 50, 100, 200]
        
        print(f"Benchmarking Population Sizes: {sizes}")
        
        gene_template = {f'param_{i}': 0.5 for i in range(5)}
        gene_ranges = {f'param_{i}': (0.0, 1.0) for i in range(5)}
        
        def simple_fitness(chromosome):
            return sum(chromosome.genes.values()) / len(chromosome.genes)
        
        size_results = {}
        
        for size in sizes:
            print(f"  Testing population size: {size}")
            
            ga = GeneticAlgorithm(
                population_size=size,
                mutation_rate=0.1,
                crossover_rate=0.8,
                elite_size=max(1, size // 10)
            )
            
            # Initialization time
            start_time = time.time()
            ga.initialize_population(gene_template, gene_ranges)
            init_time = time.time() - start_time
            
            # Evolution time (single generation)
            start_time = time.time()
            ga.evolve_generation(simple_fitness)
            evolution_time = time.time() - start_time
            
            # Memory usage approximation (rough estimate)
            memory_kb = size * 0.1  # Rough estimate: 0.1KB per chromosome
            
            size_results[size] = {
                'init_time_ms': init_time * 1000,
                'evolution_time_ms': evolution_time * 1000,
                'memory_estimate_kb': memory_kb,
                'time_per_chromosome_ms': (evolution_time * 1000) / size
            }
            
            print(f"    Init: {init_time * 1000:.2f} ms")
            print(f"    Evolution: {evolution_time * 1000:.2f} ms")
            print(f"    Time/chromosome: {(evolution_time * 1000) / size:.4f} ms")
        
        self.results['population_sizes'] = size_results
    
    def benchmark_generation_count(self, generations: List[int] = None):
        """Benchmark evolution over different generation counts."""
        if generations is None:
            generations = [5, 10, 20, 50]
        
        print(f"Benchmarking Generation Counts: {generations}")
        
        gene_template = {'confidence': 0.8, 'speed': 0.5, 'accuracy': 0.7}
        gene_ranges = {
            'confidence': (0.5, 1.0),
            'speed': (0.0, 1.0),
            'accuracy': (0.0, 1.0)
        }
        
        def fitness_function(chromosome):
            genes = chromosome.genes
            return (genes['confidence'] + genes['speed'] + genes['accuracy']) / 3.0
        
        generation_results = {}
        
        for gen_count in generations:
            print(f"  Testing {gen_count} generations")
            
            ga = GeneticAlgorithm(population_size=30, mutation_rate=0.1, crossover_rate=0.8)
            ga.initialize_population(gene_template, gene_ranges)
            
            start_time = time.time()
            initial_fitness = ga.get_best_fitness()
            
            for generation in range(gen_count):
                ga.evolve_generation(fitness_function)
            
            total_time = time.time() - start_time
            final_fitness = ga.get_best_fitness()
            improvement = final_fitness - initial_fitness
            
            generation_results[gen_count] = {
                'total_time_s': total_time,
                'time_per_generation_ms': (total_time * 1000) / gen_count,
                'initial_fitness': initial_fitness,
                'final_fitness': final_fitness,
                'improvement': improvement,
                'improvement_rate': improvement / gen_count if gen_count > 0 else 0
            }
            
            print(f"    Total time: {total_time:.2f} s")
            print(f"    Per generation: {(total_time * 1000) / gen_count:.2f} ms")
            print(f"    Fitness improvement: {improvement:.4f}")
        
        self.results['generation_counts'] = generation_results
    
    def benchmark_fitness_evaluation(self, evaluation_counts: List[int] = None):
        """Benchmark fitness evaluation performance."""
        if evaluation_counts is None:
            evaluation_counts = [100, 500, 1000, 2000]
        
        print(f"Benchmarking Fitness Evaluation: {evaluation_counts}")
        
        evaluator = FitnessEvaluator()
        
        # Create mock agent and test cases
        mock_agent = Mock()
        mock_agent.set_chromosome = Mock()
        mock_agent.process_input = Mock(return_value={
            'success': True,
            'content': 'Mock response',
            'processing_time': 0.001,
            'category': 'test',
            'confidence': 0.8
        })
        
        test_cases = [
            {
                'input': {'query': f'Test query {i}'},
                'expected': {'category': 'test', 'confidence': 0.8}
            }
            for i in range(50)  # 50 test cases
        ]
        
        evaluation_results = {}
        
        for eval_count in evaluation_counts:
            print(f"  Testing {eval_count} evaluations")
            
            chromosomes = [
                Chromosome(genes={
                    'confidence': random.random(),
                    'timeout': random.uniform(1.0, 10.0),
                    'retries': random.randint(1, 5)
                })
                for _ in range(eval_count)
            ]
            
            start_time = time.time()
            
            for chromosome in chromosomes:
                fitness = evaluator.evaluate_chromosome(chromosome, mock_agent, test_cases)
            
            total_time = time.time() - start_time
            
            evaluation_results[eval_count] = {
                'total_time_s': total_time,
                'time_per_evaluation_ms': (total_time * 1000) / eval_count,
                'evaluations_per_second': eval_count / total_time if total_time > 0 else 0
            }
            
            print(f"    Total time: {total_time:.2f} s")
            print(f"    Per evaluation: {(total_time * 1000) / eval_count:.4f} ms")
            print(f"    Evaluations/second: {eval_count / total_time:.1f}")
        
        self.results['fitness_evaluation'] = evaluation_results
    
    def benchmark_selection_methods(self, population_size: int = 100, iterations: int = 1000):
        """Benchmark different selection methods."""
        print(f"Benchmarking Selection Methods (pop={population_size}, iter={iterations})")
        
        gene_template = {'param1': 0.5, 'param2': 0.7}
        
        selection_methods = ['tournament', 'roulette', 'rank']
        selection_results = {}
        
        for method in selection_methods:
            print(f"  Testing {method} selection")
            
            ga = GeneticAlgorithm(
                population_size=population_size,
                selection_method=method,
                tournament_size=5
            )
            ga.initialize_population(gene_template)
            
            # Set random fitness values
            for chromosome in ga.population:
                chromosome.fitness = random.random()
            
            start_time = time.time()
            
            for _ in range(iterations):
                selected = ga._select_parent()
            
            total_time = time.time() - start_time
            
            selection_results[method] = {
                'total_time_s': total_time,
                'time_per_selection_us': (total_time * 1_000_000) / iterations,
                'selections_per_second': iterations / total_time if total_time > 0 else 0
            }
            
            print(f"    Time per selection: {(total_time * 1_000_000) / iterations:.2f} μs")
            print(f"    Selections/second: {iterations / total_time:.0f}")
        
        self.results['selection_methods'] = selection_results
    
    def benchmark_convergence_detection(self):
        """Benchmark convergence detection and optimization efficiency."""
        print("Benchmarking Convergence Detection")
        
        gene_template = {
            'confidence': 0.8,
            'empathy': 0.7,
            'speed': 0.6,
            'accuracy': 0.9
        }
        
        gene_ranges = {
            'confidence': (0.5, 1.0),
            'empathy': (0.0, 1.0),
            'speed': (0.0, 1.0),
            'accuracy': (0.0, 1.0)
        }
        
        def convergence_fitness(chromosome):
            # Fitness function with clear optimum
            genes = chromosome.genes
            target_genes = {'confidence': 0.85, 'empathy': 0.8, 'speed': 0.75, 'accuracy': 0.95}
            
            distance = sum(abs(genes[k] - target_genes[k]) for k in target_genes.keys())
            return 1.0 - (distance / 4.0)  # Normalize to 0-1 range
        
        convergence_results = {}
        
        # Test different configurations
        configs = [
            {'population_size': 20, 'mutation_rate': 0.1, 'name': 'standard'},
            {'population_size': 50, 'mutation_rate': 0.05, 'name': 'large_low_mutation'},
            {'population_size': 10, 'mutation_rate': 0.2, 'name': 'small_high_mutation'}
        ]
        
        for config in configs:
            print(f"  Testing {config['name']} configuration")
            
            ga = GeneticAlgorithm(
                population_size=config['population_size'],
                mutation_rate=config['mutation_rate'],
                crossover_rate=0.8,
                elite_size=max(1, config['population_size'] // 10)
            )
            
            ga.initialize_population(gene_template, gene_ranges)
            
            start_time = time.time()
            initial_fitness = ga.get_best_fitness()
            
            # Evolve until convergence or max generations
            max_generations = 50
            converged_generation = None
            fitness_threshold = 0.95
            
            for generation in range(max_generations):
                ga.evolve_generation(convergence_fitness)
                current_best = ga.get_best_fitness()
                
                if current_best >= fitness_threshold and converged_generation is None:
                    converged_generation = generation + 1
                    break
            
            total_time = time.time() - start_time
            final_fitness = ga.get_best_fitness()
            
            convergence_results[config['name']] = {
                'total_time_s': total_time,
                'generations_run': converged_generation or max_generations,
                'converged': converged_generation is not None,
                'convergence_generation': converged_generation,
                'initial_fitness': initial_fitness,
                'final_fitness': final_fitness,
                'improvement': final_fitness - initial_fitness,
                'time_to_convergence': total_time if converged_generation else None
            }
            
            print(f"    Generations: {converged_generation or max_generations}")
            print(f"    Final fitness: {final_fitness:.4f}")
            print(f"    Converged: {converged_generation is not None}")
        
        self.results['convergence_detection'] = convergence_results
    
    def run_full_benchmark(self):
        """Run complete performance benchmark suite."""
        print("Running GeneticML Performance Benchmark Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all benchmarks
        self.benchmark_chromosome_operations(1000)
        print()
        
        self.benchmark_population_sizes([10, 25, 50, 100])
        print()
        
        self.benchmark_generation_count([5, 10, 20])
        print()
        
        self.benchmark_fitness_evaluation([100, 500, 1000])
        print()
        
        self.benchmark_selection_methods(50, 500)
        print()
        
        self.benchmark_convergence_detection()
        print()
        
        total_time = time.time() - start_time
        
        print("=" * 60)
        print(f"Benchmark completed in {total_time:.2f} seconds")
        
        return self.results
    
    def print_summary(self):
        """Print benchmark results summary."""
        print("\nBenchmark Results Summary")
        print("=" * 40)
        
        if 'chromosome_operations' in self.results:
            ops = self.results['chromosome_operations']
            print(f"Chromosome Operations ({ops['iterations']} iterations):")
            print(f"  Mutation: {ops['mutation_time_ms']:.4f} ms")
            print(f"  Crossover: {ops['crossover_time_ms']:.4f} ms")
            print(f"  Distance: {ops['distance_time_ms']:.4f} ms")
        
        if 'population_sizes' in self.results:
            print(f"\nPopulation Size Performance:")
            for size, data in self.results['population_sizes'].items():
                print(f"  Size {size}: {data['evolution_time_ms']:.2f} ms/generation")
        
        if 'selection_methods' in self.results:
            print(f"\nSelection Method Performance:")
            for method, data in self.results['selection_methods'].items():
                print(f"  {method}: {data['time_per_selection_us']:.2f} μs/selection")
        
        if 'convergence_detection' in self.results:
            print(f"\nConvergence Performance:")
            for config, data in self.results['convergence_detection'].items():
                convergence = "Yes" if data['converged'] else "No"
                print(f"  {config}: {data['generations_run']} generations, converged: {convergence}")


def run_performance_benchmark():
    """Run the performance benchmark suite."""
    benchmark = PerformanceBenchmark()
    results = benchmark.run_full_benchmark()
    benchmark.print_summary()
    return results


if __name__ == "__main__":
    run_performance_benchmark()
