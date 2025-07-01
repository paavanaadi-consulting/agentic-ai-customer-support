"""
Core genetic algorithm implementation for agent evolution
"""
import random
import copy
import numpy as np
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

@dataclass
class Chromosome:
    """Represents a chromosome containing agent configuration genes"""
    genes: Dict[str, Any] = field(default_factory=dict)
    fitness: float = 0.0
    generation: int = 0
    age: int = 0
    
    def __post_init__(self):
        """Initialize chromosome with default values"""
        if not self.genes:
            self.genes = {}
    
    def mutate(self, mutation_rate: float, gene_ranges: Dict[str, tuple] = None):
        """Apply mutation to chromosome genes"""
        gene_ranges = gene_ranges or {}
        
        for gene_name, gene_value in self.genes.items():
            if random.random() < mutation_rate:
                if isinstance(gene_value, (int, float)):
                    # Numeric mutation
                    if gene_name in gene_ranges:
                        min_val, max_val = gene_ranges[gene_name]
                        # Gaussian mutation with bounds
                        mutation_strength = (max_val - min_val) * 0.1
                        new_value = gene_value + random.gauss(0, mutation_strength)
                        self.genes[gene_name] = max(min_val, min(max_val, new_value))
                    else:
                        # Default numeric mutation
                        mutation_strength = abs(gene_value) * 0.1 if gene_value != 0 else 0.1
                        self.genes[gene_name] = gene_value + random.gauss(0, mutation_strength)
                        
                elif isinstance(gene_value, bool):
                    # Boolean flip
                    self.genes[gene_name] = not gene_value
                    
                elif isinstance(gene_value, str):
                    # String mutation (for categorical values)
                    if gene_name in gene_ranges and isinstance(gene_ranges[gene_name], list):
                        possible_values = gene_ranges[gene_name]
                        self.genes[gene_name] = random.choice(possible_values)
    
    def crossover(self, other: 'Chromosome', crossover_rate: float) -> tuple['Chromosome', 'Chromosome']:
        """Perform crossover with another chromosome"""
        if random.random() > crossover_rate:
            return copy.deepcopy(self), copy.deepcopy(other)
        
        # Single-point crossover for dictionaries
        genes1 = copy.deepcopy(self.genes)
        genes2 = copy.deepcopy(other.genes)
        
        # Get common genes
        common_genes = set(genes1.keys()) & set(genes2.keys())
        if not common_genes:
            return copy.deepcopy(self), copy.deepcopy(other)
        
        # Choose crossover point
        gene_list = list(common_genes)
        if len(gene_list) > 1:
            crossover_point = random.randint(1, len(gene_list) - 1)
            genes_to_swap = gene_list[crossover_point:]
            
            # Swap genes after crossover point
            for gene in genes_to_swap:
                genes1[gene], genes2[gene] = genes2[gene], genes1[gene]
        
        # Create offspring
        offspring1 = Chromosome(genes=genes1, generation=max(self.generation, other.generation) + 1)
        offspring2 = Chromosome(genes=genes2, generation=max(self.generation, other.generation) + 1)
        
        return offspring1, offspring2
    
    def copy(self) -> 'Chromosome':
        """Create a deep copy of the chromosome"""
        return Chromosome(
            genes=copy.deepcopy(self.genes),
            fitness=self.fitness,
            generation=self.generation,
            age=self.age
        )
    
    def distance(self, other: 'Chromosome') -> float:
        """Calculate genetic distance between chromosomes"""
        if not self.genes or not other.genes:
            return 1.0
        
        common_genes = set(self.genes.keys()) & set(other.genes.keys())
        if not common_genes:
            return 1.0
        
        total_distance = 0.0
        for gene in common_genes:
            val1, val2 = self.genes[gene], other.genes[gene]
            
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # Normalize numeric distance
                max_val = max(abs(val1), abs(val2), 1.0)
                total_distance += abs(val1 - val2) / max_val
            elif isinstance(val1, bool) and isinstance(val2, bool):
                total_distance += 0.0 if val1 == val2 else 1.0
            elif isinstance(val1, str) and isinstance(val2, str):
                total_distance += 0.0 if val1 == val2 else 1.0
            else:
                total_distance += 1.0
        
        return total_distance / len(common_genes)

class GeneticAlgorithm:
    """Genetic algorithm implementation for agent evolution"""
    
    def __init__(self, 
                 population_size: int = 50,
                 mutation_rate: float = 0.1,
                 crossover_rate: float = 0.8,
                 elite_size: int = 5,
                 selection_method: str = "tournament",
                 tournament_size: int = 3):
        
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_size = elite_size
        self.selection_method = selection_method
        self.tournament_size = tournament_size
        
        self.population: List[Chromosome] = []
        self.generation = 0
        self.best_fitness_history: List[float] = []
        self.average_fitness_history: List[float] = []
        self.diversity_history: List[float] = []
        
        self.gene_ranges: Dict[str, Any] = {}
        self.logger = logging.getLogger("GeneticAlgorithm")
    
    def initialize_population(self, gene_template: Dict[str, Any], gene_ranges: Dict[str, Any] = None):
        """Initialize population with random chromosomes based on gene template"""
        self.gene_ranges = gene_ranges or {}
        self.population = []
        
        for _ in range(self.population_size):
            chromosome = self._create_random_chromosome(gene_template)
            self.population.append(chromosome)
        
        self.logger.info(f"Initialized population with {len(self.population)} chromosomes")
    
    def _create_random_chromosome(self, gene_template: Dict[str, Any]) -> Chromosome:
        """Create a random chromosome based on gene template"""
        genes = {}
        
        for gene_name, default_value in gene_template.items():
            if gene_name in self.gene_ranges:
                gene_range = self.gene_ranges[gene_name]
                
                if isinstance(gene_range, tuple) and len(gene_range) == 2:
                    # Numeric range
                    min_val, max_val = gene_range
                    if isinstance(default_value, int):
                        genes[gene_name] = random.randint(int(min_val), int(max_val))
                    else:
                        genes[gene_name] = random.uniform(min_val, max_val)
                        
                elif isinstance(gene_range, list):
                    # Categorical values
                    genes[gene_name] = random.choice(gene_range)
                else:
                    genes[gene_name] = default_value
            else:
                # Use default with some variation
                if isinstance(default_value, (int, float)):
                    variation = abs(default_value) * 0.2 if default_value != 0 else 0.2
                    genes[gene_name] = default_value + random.gauss(0, variation)
                elif isinstance(default_value, bool):
                    genes[gene_name] = random.choice([True, False])
                else:
                    genes[gene_name] = default_value
        
        return Chromosome(genes=genes, generation=0)
    
    def evolve_generation(self, fitness_function: Callable[[Chromosome], float]):
        """Evolve the population for one generation"""
        # Evaluate fitness
        self._evaluate_population(fitness_function)
        
        # Track statistics
        self._update_statistics()
        
        # Select parents and create next generation
        new_population = self._create_next_generation()
        
        # Update population
        self.population = new_population
        self.generation += 1
        
        # Age existing chromosomes
        for chromosome in self.population:
            chromosome.age += 1
        
        self.logger.debug(f"Generation {self.generation} completed. "
                         f"Best fitness: {self.get_best_fitness():.4f}")
    
    def _evaluate_population(self, fitness_function: Callable[[Chromosome], float]):
        """Evaluate fitness for all chromosomes in population"""
        for chromosome in self.population:
            try:
                chromosome.fitness = fitness_function(chromosome)
            except Exception as e:
                self.logger.warning(f"Fitness evaluation failed: {str(e)}")
                chromosome.fitness = 0.0
    
    def _update_statistics(self):
        """Update generation statistics"""
        fitnesses = [c.fitness for c in self.population]
        
        best_fitness = max(fitnesses)
        average_fitness = np.mean(fitnesses)
        diversity = self._calculate_diversity()
        
        self.best_fitness_history.append(best_fitness)
        self.average_fitness_history.append(average_fitness)
        self.diversity_history.append(diversity)
    
    def _calculate_diversity(self) -> float:
        """Calculate population diversity"""
        if len(self.population) < 2:
            return 0.0
        
        total_distance = 0.0
        comparisons = 0
        
        for i in range(len(self.population)):
            for j in range(i + 1, len(self.population)):
                total_distance += self.population[i].distance(self.population[j])
                comparisons += 1
        
        return total_distance / comparisons if comparisons > 0 else 0.0
    
    def _create_next_generation(self) -> List[Chromosome]:
        """Create the next generation through selection, crossover, and mutation"""
        new_population = []
        
        # Elitism: keep best chromosomes
        elite = self._select_elite()
        new_population.extend([c.copy() for c in elite])
        
        # Generate offspring to fill remaining population
        while len(new_population) < self.population_size:
            # Selection
            parent1 = self._select_parent()
            parent2 = self._select_parent()
            
            # Crossover
            offspring1, offspring2 = parent1.crossover(parent2, self.crossover_rate)
            
            # Mutation
            offspring1.mutate(self.mutation_rate, self.gene_ranges)
            offspring2.mutate(self.mutation_rate, self.gene_ranges)
            
            # Add to new population
            new_population.append(offspring1)
            if len(new_population) < self.population_size:
                new_population.append(offspring2)
        
        # Ensure exact population size
        return new_population[:self.population_size]
    
    def _select_elite(self) -> List[Chromosome]:
        """Select elite chromosomes for next generation"""
        sorted_population = sorted(self.population, key=lambda c: c.fitness, reverse=True)
        return sorted_population[:self.elite_size]
    
    def _select_parent(self) -> Chromosome:
        """Select a parent using the specified selection method"""
        if self.selection_method == "tournament":
            return self._tournament_selection()
        elif self.selection_method == "roulette":
            return self._roulette_selection()
        elif self.selection_method == "rank":
            return self._rank_selection()
        else:
            return random.choice(self.population)
    
    def _tournament_selection(self) -> Chromosome:
        """Tournament selection"""
        tournament = random.sample(self.population, min(self.tournament_size, len(self.population)))
        return max(tournament, key=lambda c: c.fitness)
    
    def _roulette_selection(self) -> Chromosome:
        """Roulette wheel selection"""
        fitnesses = [c.fitness for c in self.population]
        min_fitness = min(fitnesses)
        
        # Ensure positive fitness values
        adjusted_fitnesses = [f - min_fitness + 0.1 for f in fitnesses]
        total_fitness = sum(adjusted_fitnesses)
        
        if total_fitness == 0:
            return random.choice(self.population)
        
        # Spin the wheel
        spin = random.uniform(0, total_fitness)
        current = 0
        
        for i, fitness in enumerate(adjusted_fitnesses):
            current += fitness
            if current >= spin:
                return self.population[i]
        
        return self.population[-1]
    
    def _rank_selection(self) -> Chromosome:
        """Rank-based selection"""
        sorted_population = sorted(self.population, key=lambda c: c.fitness)
        ranks = list(range(1, len(sorted_population) + 1))
        total_rank = sum(ranks)
        
        spin = random.uniform(0, total_rank)
        current = 0
        
        for i, rank in enumerate(ranks):
            current += rank
            if current >= spin:
                return sorted_population[i]
        
        return sorted_population[-1]
    
    def get_best_chromosome(self) -> Optional[Chromosome]:
        """Get the best chromosome from current population"""
        if not self.population:
            return None
        return max(self.population, key=lambda c: c.fitness)
    
    def get_best_fitness(self) -> float:
        """Get the best fitness from current population"""
        best = self.get_best_chromosome()
        return best.fitness if best else 0.0
    
    def get_population_stats(self) -> Dict[str, float]:
        """Get population statistics"""
        if not self.population:
            return {'best_fitness': 0.0, 'average_fitness': 0.0, 'std_fitness': 0.0, 'diversity': 0.0}
        
        fitnesses = [c.fitness for c in self.population]
        return {
            'best_fitness': max(fitnesses),
            'average_fitness': np.mean(fitnesses),
            'std_fitness': np.std(fitnesses),
            'diversity': self._calculate_diversity()
        }
    
    def get_evolution_history(self) -> Dict[str, List[float]]:
        """Get evolution history"""
        return {
            'best_fitness': self.best_fitness_history,
            'average_fitness': self.average_fitness_history,
            'diversity': self.diversity_history
        }
    
    def set_gene_ranges(self, gene_ranges: Dict[str, Any]):
        """Set valid ranges for genes"""
        self.gene_ranges = gene_ranges
    
    def export_population(self) -> List[Dict[str, Any]]:
        """Export current population"""
        return [
            {
                'genes': c.genes,
                'fitness': c.fitness,
                'generation': c.generation,
                'age': c.age
            }
            for c in self.population
        ]
    
    def import_population(self, population_data: List[Dict[str, Any]]):
        """Import population from data"""
        self.population = []
        for data in population_data:
            chromosome = Chromosome(
                genes=data['genes'],
                fitness=data['fitness'],
                generation=data['generation'],
                age=data['age']
            )
            self.population.append(chromosome)
