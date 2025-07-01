"""
Evolution engine for managing genetic algorithm across multiple agents
"""
import asyncio
import random
import json
from typing import Dict, Any, List
from datetime import datetime
from src.geneticML.core.genetic_algorithm import GeneticAlgorithm, Chromosome
from src.geneticML.evaluators.fitness_evaluator import FitnessEvaluator
from src.utils.logger import setup_logger

class EvolutionEngine:
    """Manages evolution across all agents in the system"""
    
    def __init__(self, agents: Dict[str, Any], config: Dict[str, Any]):
        self.agents = agents
        self.config = config
        self.logger = setup_logger("EvolutionEngine")
        
        # Genetic algorithms for each agent type
        self.genetic_algorithms = {}
        
        # Fitness evaluator
        self.fitness_evaluator = FitnessEvaluator()
        
        # Training data and test cases
        self.training_data = []
        self.test_cases = []
        
        # Evolution tracking
        self.evolution_history = []
        self.current_generation = 0
        self.best_chromosomes = {}
        
        # Performance tracking
        self.interaction_history = []
    
    async def initialize(self):
        """Initialize the evolution engine"""
        self.logger.info("Initializing evolution engine...")
        
        # Initialize genetic algorithms for each agent
        for agent_id, agent in self.agents.items():
            ga = GeneticAlgorithm(
                population_size=self.config.population_size,
                mutation_rate=self.config.mutation_rate,
                crossover_rate=self.config.crossover_rate,
                elite_size=self.config.elite_size
            )
            
            # Get agent-specific gene template and ranges
            gene_template = agent.gene_template
            gene_ranges = agent.gene_ranges
            
            # Initialize population with agent-specific gene templates
            ga.initialize_population(gene_template, gene_ranges)
            
            self.genetic_algorithms[agent_id] = ga
        
        # Load or generate test cases
        await self._load_test_cases()
        
        self.logger.info("Evolution engine initialized successfully")
    
    def _get_gene_template(self, agent_id: str) -> Dict[str, Any]:
        """Get gene template for specific agent type"""
        templates = {
            'query': {
                'confidence_threshold': 0.8,
                'context_window_size': 1000,
                'classification_detail_level': 'medium',
                'include_sentiment': True,
                'extract_entities': True,
                'urgency_detection': True,
                'response_timeout': 5.0
            },
            'knowledge': {
                'search_depth': 5,
                'relevance_threshold': 0.7,
                'max_sources': 10,
                'include_citations': True,
                'fact_checking_enabled': True,
                'synthesis_level': 'detailed',
                'search_timeout': 10.0
            },
            'response': {
                'tone': 'friendly',
                'length_preference': 'medium',
                'personalization_level': 0.7,
                'empathy_level': 0.8,
                'formality_level': 0.6,
                'include_suggestions': True,
                'response_timeout': 8.0
            }
        }
        
        return templates.get(agent_id, {})
    
    async def _load_test_cases(self):
        """Load or generate test cases for fitness evaluation"""
        # In a real implementation, load from database or files
        self.test_cases = [
            {
                'input': {
                    'query': 'I cannot log into my account',
                    'customer_id': 'test_001',
                    'context': {'previous_attempts': 3}
                },
                'expected': {
                    'category': 'technical',
                    'urgency': 'medium',
                    'sentiment': 'negative'
                }
            },
            {
                'input': {
                    'query': 'How do I change my billing address?',
                    'customer_id': 'test_002',
                    'context': {}
                },
                'expected': {
                    'category': 'billing',
                    'urgency': 'low',
                    'sentiment': 'neutral'
                }
            },
            {
                'input': {
                    'query': 'Your service is terrible! I want a refund!',
                    'customer_id': 'test_003',
                    'context': {'tier': 'premium'}
                },
                'expected': {
                    'category': 'complaint',
                    'urgency': 'high',
                    'sentiment': 'negative'
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
                    'sentiment': 'positive'
                }
            },
            {
                'input': {
                    'query': 'Thank you for the excellent support!',
                    'customer_id': 'test_005',
                    'context': {}
                },
                'expected': {
                    'category': 'general',
                    'urgency': 'low',
                    'sentiment': 'positive'
                }
            }
        ]
    
    async def evolve(self, max_generations: int = None):
        """Run evolution process for specified generations"""
        max_gen = max_generations or self.config.max_generations
        
        self.logger.info(f"Starting evolution for {max_gen} generations...")
        
        for generation in range(max_gen):
            self.current_generation = generation
            
            self.logger.info(f"Generation {generation + 1}/{max_gen}")
            
            # Evolve each agent type
            generation_stats = {}
            for agent_id, ga in self.genetic_algorithms.items():
                stats = await self._evolve_agent(agent_id, ga)
                generation_stats[agent_id] = stats
            
            # Record generation results
            self.evolution_history.append({
                'generation': generation,
                'timestamp': datetime.now().isoformat(),
                'stats': generation_stats
            })
            
            # Check convergence criteria
            if self._check_convergence(generation_stats):
                self.logger.info(f"Convergence achieved at generation {generation + 1}")
                break
            
            # Log progress
            self._log_generation_progress(generation, generation_stats)
        
        # Update agents with best chromosomes
        await self._apply_best_chromosomes()
        
        self.logger.info("Evolution completed!")
    
    async def _evolve_agent(self, agent_id: str, ga: GeneticAlgorithm) -> Dict[str, float]:
        """Evolve a specific agent for one generation"""
        agent = self.agents[agent_id]
        
        # Define fitness function for this agent
        def fitness_function(chromosome):
            return self.fitness_evaluator.evaluate_chromosome(
                chromosome, agent, self.test_cases
            )
        
        # Evolve one generation
        ga.evolve_generation(fitness_function)
        
        # Track best chromosome
        best_chromosome = ga.get_best_chromosome()
        if agent_id not in self.best_chromosomes or \
           best_chromosome.fitness > self.best_chromosomes[agent_id].fitness:
            self.best_chromosomes[agent_id] = best_chromosome
        
        return ga.get_population_stats()
    
    def _check_convergence(self, generation_stats: Dict[str, Dict[str, float]]) -> bool:
        """Check if evolution has converged"""
        fitness_threshold = self.config.fitness_threshold
        
        # Check if all agents have achieved target fitness
        for agent_id, stats in generation_stats.items():
            if stats['best_fitness'] < fitness_threshold:
                return False
        
        return True
    
    def _log_generation_progress(self, generation: int, stats: Dict[str, Dict[str, float]]):
        """Log progress for current generation"""
        for agent_id, agent_stats in stats.items():
            self.logger.info(
                f"Agent {agent_id} - Gen {generation + 1}: "
                f"Best: {agent_stats['best_fitness']:.4f}, "
                f"Avg: {agent_stats['average_fitness']:.4f}, "
                f"Std: {agent_stats['std_fitness']:.4f}"
            )
    
    async def _apply_best_chromosomes(self):
        """Apply best chromosomes to agents"""
        for agent_id, chromosome in self.best_chromosomes.items():
            if agent_id in self.agents:
                self.agents[agent_id].set_chromosome(chromosome)
                self.logger.info(
                    f"Applied best chromosome to {agent_id} "
                    f"(fitness: {chromosome.fitness:.4f})"
                )
    
    async def record_interaction(self, interaction_result: Dict[str, Any]):
        """Record interaction for continuous learning"""
        self.interaction_history.append({
            'timestamp': datetime.now().isoformat(),
            'result': interaction_result
        })
        
        # Trigger adaptive evolution if needed
        if len(self.interaction_history) % 100 == 0:  # Every 100 interactions
            await self._adaptive_evolution()
    
    async def _adaptive_evolution(self):
        """Perform adaptive evolution based on recent interactions"""
        self.logger.info("Performing adaptive evolution based on recent interactions...")
        
        # Analyze recent performance
        recent_interactions = self.interaction_history[-100:]
        
        # Create test cases from recent interactions
        adaptive_test_cases = []
        for interaction in recent_interactions:
            if 'query_analysis' in interaction['result']:
                test_case = {
                    'input': {
                        'query': interaction['result'].get('original_query', ''),
                        'customer_id': interaction['result'].get('customer_id', ''),
                        'context': {}
                    },
                    'expected': interaction['result']['query_analysis'].get('analysis', {})
                }
                adaptive_test_cases.append(test_case)
        
        if adaptive_test_cases:
            # Temporarily use adaptive test cases
            original_test_cases = self.test_cases
            self.test_cases = adaptive_test_cases[-20:]  # Use last 20 interactions
            
            # Run short evolution
            await self.evolve(max_generations=5)
            
            # Restore original test cases
            self.test_cases = original_test_cases
    
    def get_status(self) -> Dict[str, Any]:
        """Get current evolution status"""
        return {
            'current_generation': self.current_generation,
            'total_interactions': len(self.interaction_history),
            'best_fitness_scores': {
                agent_id: chromosome.fitness 
                for agent_id, chromosome in self.best_chromosomes.items()
            },
            'evolution_history_length': len(self.evolution_history),
            'agents_count': len(self.agents),
            'test_cases_count': len(self.test_cases)
        }
    
    def export_results(self) -> Dict[str, Any]:
        """Export evolution results"""
        return {
            'config': self.config.__dict__,
            'evolution_history': self.evolution_history,
            'best_chromosomes': {
                agent_id: {
                    'genes': chromosome.genes,
                    'fitness': chromosome.fitness,
                    'generation': chromosome.generation
                }
                for agent_id, chromosome in self.best_chromosomes.items()
            },
            'final_generation': self.current_generation,
            'total_interactions': len(self.interaction_history)
        }
