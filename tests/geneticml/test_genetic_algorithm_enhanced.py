"""
Enhanced test suite for GeneticAlgorithm and Chromosome classes.
Tests genetic operations, evolution processes, and optimization algorithms.
"""
import pytest
import random
import numpy as np
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from src.geneticML.core.genetic_algorithm import GeneticAlgorithm, Chromosome


class TestChromosome:
    """Test cases for Chromosome class."""

    def test_chromosome_initialization_default(self):
        """Test Chromosome initialization with default values."""
        chromosome = Chromosome()
        
        assert isinstance(chromosome.genes, dict)
        assert chromosome.fitness == 0.0
        assert chromosome.generation == 0
        assert chromosome.age == 0

    def test_chromosome_initialization_custom(self):
        """Test Chromosome initialization with custom values."""
        genes = {'param1': 0.5, 'param2': True, 'param3': 'medium'}
        chromosome = Chromosome(
            genes=genes,
            fitness=0.8,
            generation=5,
            age=3
        )
        
        assert chromosome.genes == genes
        assert chromosome.fitness == 0.8
        assert chromosome.generation == 5
        assert chromosome.age == 3

    def test_chromosome_post_init(self):
        """Test chromosome post-initialization behavior."""
        # Test with None genes
        chromosome = Chromosome(genes=None)
        assert chromosome.genes == {}
        
        # Test with empty genes
        chromosome = Chromosome(genes={})
        assert chromosome.genes == {}

    def test_mutation_numeric_genes(self):
        """Test mutation of numeric genes."""
        genes = {'param1': 0.5, 'param2': 1.0, 'param3': 10}
        chromosome = Chromosome(genes=genes)
        
        gene_ranges = {
            'param1': (0.0, 1.0),
            'param2': (0.0, 2.0),
            'param3': (5, 15)
        }
        
        # Force mutation with 100% rate
        original_genes = chromosome.genes.copy()
        chromosome.mutate(mutation_rate=1.0, gene_ranges=gene_ranges)
        
        # Verify genes changed (with small probability they might be the same)
        # Check that values are within bounds
        assert 0.0 <= chromosome.genes['param1'] <= 1.0
        assert 0.0 <= chromosome.genes['param2'] <= 2.0
        assert 5 <= chromosome.genes['param3'] <= 15

    def test_mutation_boolean_genes(self):
        """Test mutation of boolean genes."""
        genes = {'flag1': True, 'flag2': False}
        chromosome = Chromosome(genes=genes)
        
        # Force mutation
        chromosome.mutate(mutation_rate=1.0)
        
        # Boolean values should flip
        assert chromosome.genes['flag1'] is False
        assert chromosome.genes['flag2'] is True

    def test_mutation_string_genes(self):
        """Test mutation of string/categorical genes."""
        genes = {'category': 'medium', 'type': 'A'}
        chromosome = Chromosome(genes=genes)
        
        gene_ranges = {
            'category': ['low', 'medium', 'high'],
            'type': ['A', 'B', 'C']
        }
        
        chromosome.mutate(mutation_rate=1.0, gene_ranges=gene_ranges)
        
        # Values should be from the allowed ranges
        assert chromosome.genes['category'] in ['low', 'medium', 'high']
        assert chromosome.genes['type'] in ['A', 'B', 'C']

    def test_mutation_rate_effect(self):
        """Test effect of different mutation rates."""
        genes = {'param1': 0.5, 'param2': 0.7, 'param3': 0.9}
        
        # Test with 0% mutation rate
        chromosome_no_mutation = Chromosome(genes=genes.copy())
        original_genes = chromosome_no_mutation.genes.copy()
        chromosome_no_mutation.mutate(mutation_rate=0.0)
        assert chromosome_no_mutation.genes == original_genes
        
        # Test with low mutation rate (should mostly preserve genes)
        chromosome_low_mutation = Chromosome(genes=genes.copy())
        chromosome_low_mutation.mutate(mutation_rate=0.1)
        # Most genes should remain unchanged (probabilistic test)

    def test_crossover_successful(self):
        """Test successful crossover between chromosomes."""
        genes1 = {'param1': 0.5, 'param2': True, 'param3': 'high'}
        genes2 = {'param1': 0.8, 'param2': False, 'param3': 'low'}
        
        chromosome1 = Chromosome(genes=genes1, generation=1)
        chromosome2 = Chromosome(genes=genes2, generation=2)
        
        offspring1, offspring2 = chromosome1.crossover(chromosome2, crossover_rate=1.0)
        
        # Offspring should have mixed genes from parents
        assert offspring1.genes is not None
        assert offspring2.genes is not None
        assert offspring1.generation == 3  # max(1, 2) + 1
        assert offspring2.generation == 3

    def test_crossover_no_common_genes(self):
        """Test crossover with no common genes."""
        genes1 = {'param1': 0.5}
        genes2 = {'param2': 0.8}
        
        chromosome1 = Chromosome(genes=genes1)
        chromosome2 = Chromosome(genes=genes2)
        
        offspring1, offspring2 = chromosome1.crossover(chromosome2, crossover_rate=1.0)
        
        # Should return copies of original chromosomes
        assert offspring1.genes == genes1
        assert offspring2.genes == genes2

    def test_crossover_rate_effect(self):
        """Test effect of crossover rate."""
        genes1 = {'param1': 0.5, 'param2': True}
        genes2 = {'param1': 0.8, 'param2': False}
        
        chromosome1 = Chromosome(genes=genes1)
        chromosome2 = Chromosome(genes=genes2)
        
        # Test with 0% crossover rate
        offspring1, offspring2 = chromosome1.crossover(chromosome2, crossover_rate=0.0)
        assert offspring1.genes == genes1
        assert offspring2.genes == genes2

    def test_copy_chromosome(self):
        """Test chromosome copying."""
        genes = {'param1': 0.5, 'param2': True}
        original = Chromosome(
            genes=genes,
            fitness=0.8,
            generation=3,
            age=2
        )
        
        copy_chromosome = original.copy()
        
        # Verify all attributes copied
        assert copy_chromosome.genes == original.genes
        assert copy_chromosome.fitness == original.fitness
        assert copy_chromosome.generation == original.generation
        assert copy_chromosome.age == original.age
        
        # Verify deep copy (modifying copy shouldn't affect original)
        copy_chromosome.genes['param1'] = 0.9
        assert original.genes['param1'] == 0.5

    def test_distance_calculation(self):
        """Test genetic distance calculation between chromosomes."""
        genes1 = {'param1': 0.5, 'param2': True, 'param3': 'high'}
        genes2 = {'param1': 0.8, 'param2': True, 'param3': 'low'}
        
        chromosome1 = Chromosome(genes=genes1)
        chromosome2 = Chromosome(genes=genes2)
        
        distance = chromosome1.distance(chromosome2)
        
        assert 0.0 <= distance <= 1.0
        
        # Distance should be > 0 for different chromosomes
        assert distance > 0.0

    def test_distance_identical_chromosomes(self):
        """Test distance between identical chromosomes."""
        genes = {'param1': 0.5, 'param2': True}
        chromosome1 = Chromosome(genes=genes)
        chromosome2 = Chromosome(genes=genes.copy())
        
        distance = chromosome1.distance(chromosome2)
        
        assert distance == 0.0

    def test_distance_empty_chromosomes(self):
        """Test distance calculation with empty chromosomes."""
        chromosome1 = Chromosome(genes={})
        chromosome2 = Chromosome(genes={'param1': 0.5})
        
        distance = chromosome1.distance(chromosome2)
        
        assert distance == 1.0

    def test_distance_no_common_genes(self):
        """Test distance with no common genes."""
        chromosome1 = Chromosome(genes={'param1': 0.5})
        chromosome2 = Chromosome(genes={'param2': 0.8})
        
        distance = chromosome1.distance(chromosome2)
        
        assert distance == 1.0


class TestGeneticAlgorithm:
    """Test cases for GeneticAlgorithm class."""

    @pytest.fixture
    def genetic_algorithm(self):
        """Create a GeneticAlgorithm instance for testing."""
        return GeneticAlgorithm(
            population_size=10,
            mutation_rate=0.1,
            crossover_rate=0.8,
            elite_size=2,
            selection_method="tournament",
            tournament_size=3
        )

    @pytest.fixture
    def sample_gene_template(self):
        """Create a sample gene template for testing."""
        return {
            'confidence_threshold': 0.8,
            'timeout': 5.0,
            'max_retries': 3,
            'enable_cache': True,
            'strategy': 'balanced'
        }

    @pytest.fixture
    def sample_gene_ranges(self):
        """Create sample gene ranges for testing."""
        return {
            'confidence_threshold': (0.5, 1.0),
            'timeout': (1.0, 10.0),
            'max_retries': (1, 5),
            'enable_cache': [True, False],
            'strategy': ['aggressive', 'balanced', 'conservative']
        }

    def test_genetic_algorithm_initialization(self, genetic_algorithm):
        """Test GeneticAlgorithm initialization."""
        assert genetic_algorithm.population_size == 10
        assert genetic_algorithm.mutation_rate == 0.1
        assert genetic_algorithm.crossover_rate == 0.8
        assert genetic_algorithm.elite_size == 2
        assert genetic_algorithm.selection_method == "tournament"
        assert genetic_algorithm.tournament_size == 3
        assert genetic_algorithm.population == []
        assert genetic_algorithm.generation == 0
        assert genetic_algorithm.best_fitness_history == []
        assert genetic_algorithm.average_fitness_history == []
        assert genetic_algorithm.diversity_history == []

    def test_initialize_population(self, genetic_algorithm, sample_gene_template, sample_gene_ranges):
        """Test population initialization."""
        genetic_algorithm.initialize_population(sample_gene_template, sample_gene_ranges)
        
        assert len(genetic_algorithm.population) == 10
        
        # Verify all chromosomes have the correct genes
        for chromosome in genetic_algorithm.population:
            assert set(chromosome.genes.keys()) == set(sample_gene_template.keys())
            
            # Verify gene values are within ranges
            assert 0.5 <= chromosome.genes['confidence_threshold'] <= 1.0
            assert 1.0 <= chromosome.genes['timeout'] <= 10.0
            assert 1 <= chromosome.genes['max_retries'] <= 5
            assert chromosome.genes['enable_cache'] in [True, False]
            assert chromosome.genes['strategy'] in ['aggressive', 'balanced', 'conservative']

    def test_create_random_chromosome(self, genetic_algorithm, sample_gene_template, sample_gene_ranges):
        """Test random chromosome creation."""
        genetic_algorithm.gene_ranges = sample_gene_ranges
        
        chromosome = genetic_algorithm._create_random_chromosome(sample_gene_template)
        
        assert isinstance(chromosome, Chromosome)
        assert len(chromosome.genes) == len(sample_gene_template)
        
        # Verify gene types and ranges
        assert isinstance(chromosome.genes['confidence_threshold'], (int, float))
        assert isinstance(chromosome.genes['timeout'], (int, float))
        assert isinstance(chromosome.genes['max_retries'], int)
        assert isinstance(chromosome.genes['enable_cache'], bool)
        assert isinstance(chromosome.genes['strategy'], str)

    def test_evolve_generation(self, genetic_algorithm, sample_gene_template):
        """Test evolution of a single generation."""
        genetic_algorithm.initialize_population(sample_gene_template)
        
        # Mock fitness function
        def mock_fitness_function(chromosome):
            # Simple fitness based on confidence threshold
            return chromosome.genes.get('confidence_threshold', 0.0)
        
        initial_generation = genetic_algorithm.generation
        initial_population_size = len(genetic_algorithm.population)
        
        genetic_algorithm.evolve_generation(mock_fitness_function)
        
        # Verify generation advanced
        assert genetic_algorithm.generation == initial_generation + 1
        assert len(genetic_algorithm.population) == initial_population_size
        
        # Verify fitness tracking
        assert len(genetic_algorithm.best_fitness_history) == 1
        assert len(genetic_algorithm.average_fitness_history) == 1
        assert len(genetic_algorithm.diversity_history) == 1

    def test_evaluate_population(self, genetic_algorithm, sample_gene_template):
        """Test population fitness evaluation."""
        genetic_algorithm.initialize_population(sample_gene_template)
        
        def fitness_function(chromosome):
            return chromosome.genes['confidence_threshold']
        
        genetic_algorithm._evaluate_population(fitness_function)
        
        # Verify all chromosomes have fitness values
        for chromosome in genetic_algorithm.population:
            assert chromosome.fitness > 0.0

    def test_evaluate_population_with_errors(self, genetic_algorithm, sample_gene_template):
        """Test population evaluation with fitness function errors."""
        genetic_algorithm.initialize_population(sample_gene_template)
        
        def error_fitness_function(chromosome):
            raise ValueError("Fitness calculation failed")
        
        # Should not crash, should assign 0.0 fitness
        genetic_algorithm._evaluate_population(error_fitness_function)
        
        for chromosome in genetic_algorithm.population:
            assert chromosome.fitness == 0.0

    def test_update_statistics(self, genetic_algorithm, sample_gene_template):
        """Test statistics update."""
        genetic_algorithm.initialize_population(sample_gene_template)
        
        # Set some fitness values
        for i, chromosome in enumerate(genetic_algorithm.population):
            chromosome.fitness = i / len(genetic_algorithm.population)
        
        genetic_algorithm._update_statistics()
        
        assert len(genetic_algorithm.best_fitness_history) == 1
        assert len(genetic_algorithm.average_fitness_history) == 1
        assert len(genetic_algorithm.diversity_history) == 1
        
        # Verify values are reasonable
        assert genetic_algorithm.best_fitness_history[0] >= 0.0
        assert genetic_algorithm.average_fitness_history[0] >= 0.0
        assert genetic_algorithm.diversity_history[0] >= 0.0

    def test_calculate_diversity(self, genetic_algorithm):
        """Test diversity calculation."""
        # Create chromosomes with known diversity
        chromosome1 = Chromosome(genes={'param1': 0.0, 'param2': True})
        chromosome2 = Chromosome(genes={'param1': 1.0, 'param2': False})
        chromosome3 = Chromosome(genes={'param1': 0.5, 'param2': True})
        
        genetic_algorithm.population = [chromosome1, chromosome2, chromosome3]
        
        diversity = genetic_algorithm._calculate_diversity()
        
        assert 0.0 <= diversity <= 1.0
        assert diversity > 0.0  # Should have some diversity

    def test_calculate_diversity_empty_population(self, genetic_algorithm):
        """Test diversity calculation with empty/small population."""
        # Empty population
        genetic_algorithm.population = []
        assert genetic_algorithm._calculate_diversity() == 0.0
        
        # Single chromosome
        genetic_algorithm.population = [Chromosome(genes={'param1': 0.5})]
        assert genetic_algorithm._calculate_diversity() == 0.0

    def test_create_next_generation(self, genetic_algorithm, sample_gene_template):
        """Test next generation creation."""
        genetic_algorithm.initialize_population(sample_gene_template)
        
        # Set fitness values
        for i, chromosome in enumerate(genetic_algorithm.population):
            chromosome.fitness = i / len(genetic_algorithm.population)
        
        new_population = genetic_algorithm._create_next_generation()
        
        assert len(new_population) == genetic_algorithm.population_size
        
        # Verify all chromosomes are valid
        for chromosome in new_population:
            assert isinstance(chromosome, Chromosome)
            assert len(chromosome.genes) > 0

    def test_select_elite(self, genetic_algorithm, sample_gene_template):
        """Test elite selection."""
        genetic_algorithm.initialize_population(sample_gene_template)
        
        # Set fitness values
        for i, chromosome in enumerate(genetic_algorithm.population):
            chromosome.fitness = i / len(genetic_algorithm.population)
        
        elite = genetic_algorithm._select_elite()
        
        assert len(elite) == genetic_algorithm.elite_size
        
        # Verify elite are the best chromosomes
        elite_fitness = [c.fitness for c in elite]
        assert elite_fitness == sorted(elite_fitness, reverse=True)

    def test_tournament_selection(self, genetic_algorithm, sample_gene_template):
        """Test tournament selection."""
        genetic_algorithm.initialize_population(sample_gene_template)
        
        # Set fitness values
        for i, chromosome in enumerate(genetic_algorithm.population):
            chromosome.fitness = random.random()
        
        selected = genetic_algorithm._tournament_selection()
        
        assert isinstance(selected, Chromosome)
        assert selected in genetic_algorithm.population

    def test_roulette_selection(self, genetic_algorithm, sample_gene_template):
        """Test roulette wheel selection."""
        genetic_algorithm.initialize_population(sample_gene_template)
        
        # Set fitness values
        for i, chromosome in enumerate(genetic_algorithm.population):
            chromosome.fitness = random.random()
        
        selected = genetic_algorithm._roulette_selection()
        
        assert isinstance(selected, Chromosome)
        assert selected in genetic_algorithm.population

    def test_roulette_selection_zero_fitness(self, genetic_algorithm, sample_gene_template):
        """Test roulette selection with zero fitness values."""
        genetic_algorithm.initialize_population(sample_gene_template)
        
        # Set all fitness to zero
        for chromosome in genetic_algorithm.population:
            chromosome.fitness = 0.0
        
        selected = genetic_algorithm._roulette_selection()
        
        assert isinstance(selected, Chromosome)
        assert selected in genetic_algorithm.population

    def test_rank_selection(self, genetic_algorithm, sample_gene_template):
        """Test rank-based selection."""
        genetic_algorithm.initialize_population(sample_gene_template)
        
        # Set fitness values
        for i, chromosome in enumerate(genetic_algorithm.population):
            chromosome.fitness = random.random()
        
        selected = genetic_algorithm._rank_selection()
        
        assert isinstance(selected, Chromosome)
        assert selected in genetic_algorithm.population

    def test_get_best_chromosome(self, genetic_algorithm, sample_gene_template):
        """Test getting best chromosome."""
        genetic_algorithm.initialize_population(sample_gene_template)
        
        # Set fitness values with known best
        best_fitness = 0.95
        for i, chromosome in enumerate(genetic_algorithm.population):
            if i == 0:
                chromosome.fitness = best_fitness
            else:
                chromosome.fitness = random.uniform(0.0, 0.9)
        
        best = genetic_algorithm.get_best_chromosome()
        
        assert best is not None
        assert best.fitness == best_fitness

    def test_get_best_chromosome_empty_population(self, genetic_algorithm):
        """Test getting best chromosome from empty population."""
        best = genetic_algorithm.get_best_chromosome()
        assert best is None

    def test_get_best_fitness(self, genetic_algorithm, sample_gene_template):
        """Test getting best fitness value."""
        genetic_algorithm.initialize_population(sample_gene_template)
        
        # Set fitness values
        best_fitness = 0.95
        genetic_algorithm.population[0].fitness = best_fitness
        
        assert genetic_algorithm.get_best_fitness() == best_fitness

    def test_get_population_stats(self, genetic_algorithm, sample_gene_template):
        """Test getting population statistics."""
        genetic_algorithm.initialize_population(sample_gene_template)
        
        # Set known fitness values
        fitness_values = [0.1, 0.3, 0.5, 0.7, 0.9, 0.2, 0.4, 0.6, 0.8, 1.0]
        for i, chromosome in enumerate(genetic_algorithm.population):
            chromosome.fitness = fitness_values[i]
        
        stats = genetic_algorithm.get_population_stats()
        
        assert 'best_fitness' in stats
        assert 'average_fitness' in stats
        assert 'std_fitness' in stats
        assert 'diversity' in stats
        
        assert stats['best_fitness'] == 1.0
        assert abs(stats['average_fitness'] - 0.55) < 0.01

    def test_get_population_stats_empty(self, genetic_algorithm):
        """Test getting statistics from empty population."""
        stats = genetic_algorithm.get_population_stats()
        
        assert stats['best_fitness'] == 0.0
        assert stats['average_fitness'] == 0.0
        assert stats['std_fitness'] == 0.0
        assert stats['diversity'] == 0.0

    def test_get_evolution_history(self, genetic_algorithm, sample_gene_template):
        """Test getting evolution history."""
        genetic_algorithm.initialize_population(sample_gene_template)
        
        # Run a few generations
        def fitness_function(chromosome):
            return random.random()
        
        for _ in range(3):
            genetic_algorithm.evolve_generation(fitness_function)
        
        history = genetic_algorithm.get_evolution_history()
        
        assert 'best_fitness' in history
        assert 'average_fitness' in history
        assert 'diversity' in history
        
        assert len(history['best_fitness']) == 3
        assert len(history['average_fitness']) == 3
        assert len(history['diversity']) == 3

    def test_set_gene_ranges(self, genetic_algorithm, sample_gene_ranges):
        """Test setting gene ranges."""
        genetic_algorithm.set_gene_ranges(sample_gene_ranges)
        
        assert genetic_algorithm.gene_ranges == sample_gene_ranges

    def test_export_population(self, genetic_algorithm, sample_gene_template):
        """Test population export."""
        genetic_algorithm.initialize_population(sample_gene_template)
        
        # Set some values
        genetic_algorithm.population[0].fitness = 0.8
        genetic_algorithm.population[0].generation = 5
        genetic_algorithm.population[0].age = 3
        
        exported = genetic_algorithm.export_population()
        
        assert len(exported) == len(genetic_algorithm.population)
        
        # Verify structure
        first_export = exported[0]
        assert 'genes' in first_export
        assert 'fitness' in first_export
        assert 'generation' in first_export
        assert 'age' in first_export

    def test_import_population(self, genetic_algorithm):
        """Test population import."""
        population_data = [
            {
                'genes': {'param1': 0.5, 'param2': True},
                'fitness': 0.8,
                'generation': 2,
                'age': 1
            },
            {
                'genes': {'param1': 0.7, 'param2': False},
                'fitness': 0.6,
                'generation': 1,
                'age': 2
            }
        ]
        
        genetic_algorithm.import_population(population_data)
        
        assert len(genetic_algorithm.population) == 2
        
        # Verify imported data
        first_chromosome = genetic_algorithm.population[0]
        assert first_chromosome.genes == {'param1': 0.5, 'param2': True}
        assert first_chromosome.fitness == 0.8
        assert first_chromosome.generation == 2
        assert first_chromosome.age == 1


class TestGeneticAlgorithmIntegration:
    """Integration tests for GeneticAlgorithm with realistic scenarios."""

    @pytest.fixture
    def realistic_gene_template(self):
        """Create realistic gene template for customer support agent."""
        return {
            'confidence_threshold': 0.8,
            'response_timeout': 5.0,
            'max_context_length': 1000,
            'sentiment_analysis_enabled': True,
            'urgency_detection_enabled': True,
            'personalization_level': 0.7,
            'empathy_level': 0.8,
            'formality_level': 0.6,
            'fact_checking_enabled': True,
            'escalation_threshold': 0.9
        }

    @pytest.fixture
    def realistic_gene_ranges(self):
        """Create realistic gene ranges."""
        return {
            'confidence_threshold': (0.5, 1.0),
            'response_timeout': (1.0, 10.0),
            'max_context_length': (500, 2000),
            'sentiment_analysis_enabled': [True, False],
            'urgency_detection_enabled': [True, False],
            'personalization_level': (0.0, 1.0),
            'empathy_level': (0.0, 1.0),
            'formality_level': (0.0, 1.0),
            'fact_checking_enabled': [True, False],
            'escalation_threshold': (0.7, 1.0)
        }

    def test_customer_support_agent_evolution(self, realistic_gene_template, realistic_gene_ranges):
        """Test evolution of customer support agent parameters."""
        ga = GeneticAlgorithm(
            population_size=20,
            mutation_rate=0.15,
            crossover_rate=0.8,
            elite_size=3,
            selection_method="tournament"
        )
        
        ga.initialize_population(realistic_gene_template, realistic_gene_ranges)
        
        def customer_support_fitness(chromosome):
            """Fitness function optimizing for customer support performance."""
            genes = chromosome.genes
            
            # Base fitness
            fitness = 0.0
            
            # Reward high confidence but not too high
            conf = genes['confidence_threshold']
            if 0.7 <= conf <= 0.9:
                fitness += 0.2
            
            # Reward reasonable response times
            timeout = genes['response_timeout']
            if 2.0 <= timeout <= 6.0:
                fitness += 0.15
            
            # Reward sentiment analysis and urgency detection
            if genes['sentiment_analysis_enabled']:
                fitness += 0.1
            if genes['urgency_detection_enabled']:
                fitness += 0.1
            
            # Reward balanced personalization and empathy
            if 0.6 <= genes['personalization_level'] <= 0.8:
                fitness += 0.1
            if 0.7 <= genes['empathy_level'] <= 0.9:
                fitness += 0.1
            
            # Reward fact checking
            if genes['fact_checking_enabled']:
                fitness += 0.1
            
            # Reward appropriate escalation threshold
            if 0.8 <= genes['escalation_threshold'] <= 0.95:
                fitness += 0.15
            
            return min(fitness, 1.0)
        
        # Run evolution for multiple generations
        for generation in range(10):
            ga.evolve_generation(customer_support_fitness)
        
        # Verify improvement over generations
        best_fitness = ga.get_best_fitness()
        assert best_fitness > 0.5  # Should achieve reasonable fitness
        
        # Verify evolution history
        history = ga.get_evolution_history()
        assert len(history['best_fitness']) == 10
        
        # Generally, fitness should improve (allowing for some variance)
        first_gen_fitness = history['best_fitness'][0]
        last_gen_fitness = history['best_fitness'][-1]
        assert last_gen_fitness >= first_gen_fitness * 0.8  # Allow some variance

    def test_multi_objective_optimization(self, realistic_gene_template, realistic_gene_ranges):
        """Test optimization of multiple conflicting objectives."""
        ga = GeneticAlgorithm(population_size=15, mutation_rate=0.1, crossover_rate=0.9)
        ga.initialize_population(realistic_gene_template, realistic_gene_ranges)
        
        def multi_objective_fitness(chromosome):
            """Fitness balancing speed, accuracy, and customer satisfaction."""
            genes = chromosome.genes
            
            # Speed component (favor shorter timeouts)
            speed_score = 1.0 - (genes['response_timeout'] - 1.0) / 9.0
            
            # Accuracy component (favor fact checking and appropriate confidence)
            accuracy_score = 0.0
            if genes['fact_checking_enabled']:
                accuracy_score += 0.5
            accuracy_score += genes['confidence_threshold'] * 0.5
            
            # Customer satisfaction (favor empathy and personalization)
            satisfaction_score = (genes['empathy_level'] + genes['personalization_level']) / 2.0
            
            # Weighted combination
            fitness = (0.3 * speed_score + 0.4 * accuracy_score + 0.3 * satisfaction_score)
            return fitness
        
        # Evolve for several generations
        for _ in range(8):
            ga.evolve_generation(multi_objective_fitness)
        
        # Verify optimization worked
        best_chromosome = ga.get_best_chromosome()
        assert best_chromosome is not None
        assert best_chromosome.fitness > 0.6

    def test_convergence_detection(self, realistic_gene_template, realistic_gene_ranges):
        """Test detection of population convergence."""
        ga = GeneticAlgorithm(
            population_size=10,
            mutation_rate=0.05,  # Low mutation for faster convergence
            crossover_rate=0.9,
            elite_size=3
        )
        ga.initialize_population(realistic_gene_template, realistic_gene_ranges)
        
        def simple_fitness(chromosome):
            # Simple fitness favoring high confidence
            return chromosome.genes['confidence_threshold']
        
        # Evolve until convergence
        max_generations = 20
        convergence_threshold = 0.01  # Very small diversity indicates convergence
        
        for generation in range(max_generations):
            ga.evolve_generation(simple_fitness)
            
            diversity = ga._calculate_diversity()
            if diversity < convergence_threshold:
                break
        
        # Should converge before max generations (usually)
        final_diversity = ga._calculate_diversity()
        assert final_diversity >= 0.0  # Always non-negative

    def test_performance_with_large_population(self, realistic_gene_template, realistic_gene_ranges):
        """Test performance with larger population sizes."""
        ga = GeneticAlgorithm(
            population_size=50,  # Larger population
            mutation_rate=0.1,
            crossover_rate=0.8,
            elite_size=5
        )
        ga.initialize_population(realistic_gene_template, realistic_gene_ranges)
        
        def performance_fitness(chromosome):
            # Composite fitness function
            genes = chromosome.genes
            return (genes['confidence_threshold'] + genes['empathy_level']) / 2.0
        
        # Single generation should complete in reasonable time
        import time
        start_time = time.time()
        ga.evolve_generation(performance_fitness)
        elapsed = time.time() - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert elapsed < 5.0  # 5 seconds threshold
        
        # Verify population size maintained
        assert len(ga.population) == 50


class TestGeneticAlgorithmEdgeCases:
    """Test edge cases and error conditions for GeneticAlgorithm."""

    def test_very_small_population(self):
        """Test behavior with very small population size."""
        ga = GeneticAlgorithm(population_size=2, elite_size=1)
        
        gene_template = {'param1': 0.5}
        ga.initialize_population(gene_template)
        
        def simple_fitness(chromosome):
            return chromosome.genes['param1']
        
        # Should handle small population gracefully
        ga.evolve_generation(simple_fitness)
        
        assert len(ga.population) == 2

    def test_elite_size_larger_than_population(self):
        """Test behavior when elite size exceeds population size."""
        ga = GeneticAlgorithm(population_size=5, elite_size=10)
        
        gene_template = {'param1': 0.5}
        ga.initialize_population(gene_template)
        
        # Set fitness values
        for chromosome in ga.population:
            chromosome.fitness = random.random()
        
        elite = ga._select_elite()
        
        # Should not exceed population size
        assert len(elite) <= len(ga.population)

    def test_extreme_mutation_rates(self):
        """Test behavior with extreme mutation rates."""
        ga = GeneticAlgorithm(population_size=5, mutation_rate=2.0)  # >100% rate
        
        gene_template = {'param1': 0.5, 'param2': True}
        ga.initialize_population(gene_template)
        
        def simple_fitness(chromosome):
            return 0.5
        
        # Should handle extreme rates gracefully
        ga.evolve_generation(simple_fitness)
        
        assert len(ga.population) == 5

    def test_zero_population_size(self):
        """Test behavior with zero population size."""
        ga = GeneticAlgorithm(population_size=0)
        
        gene_template = {'param1': 0.5}
        ga.initialize_population(gene_template)
        
        assert len(ga.population) == 0
        
        # Should handle empty population
        def simple_fitness(chromosome):
            return 0.5
        
        ga.evolve_generation(simple_fitness)

    def test_invalid_selection_method(self):
        """Test behavior with invalid selection method."""
        ga = GeneticAlgorithm(selection_method="invalid_method")
        
        gene_template = {'param1': 0.5}
        ga.initialize_population(gene_template)
        
        # Should fall back to random selection
        for chromosome in ga.population:
            chromosome.fitness = random.random()
        
        selected = ga._select_parent()
        assert selected in ga.population

    def test_empty_gene_template(self):
        """Test initialization with empty gene template."""
        ga = GeneticAlgorithm(population_size=5)
        
        ga.initialize_population({})  # Empty template
        
        # Should create chromosomes with empty genes
        assert len(ga.population) == 5
        for chromosome in ga.population:
            assert chromosome.genes == {}

    def test_fitness_function_returning_none(self):
        """Test handling of fitness function returning None."""
        ga = GeneticAlgorithm(population_size=3)
        
        gene_template = {'param1': 0.5}
        ga.initialize_population(gene_template)
        
        def none_fitness(chromosome):
            return None
        
        # Should handle None gracefully (likely by treating as 0.0)
        try:
            ga.evolve_generation(none_fitness)
        except Exception as e:
            pytest.fail(f"Should handle None fitness gracefully: {e}")

    def test_fitness_function_returning_negative(self):
        """Test handling of fitness function returning negative values."""
        ga = GeneticAlgorithm(population_size=3)
        
        gene_template = {'param1': 0.5}
        ga.initialize_population(gene_template)
        
        def negative_fitness(chromosome):
            return -0.5  # Negative fitness
        
        ga.evolve_generation(negative_fitness)
        
        # Algorithm should handle negative fitness
        for chromosome in ga.population:
            assert chromosome.fitness == -0.5
