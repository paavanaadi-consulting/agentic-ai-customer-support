#!/bin/bash
# GeneticML Evolution Engine Standalone Runner

set -e

echo "Starting GeneticML Evolution Engine..."

# Configuration
POPULATION_SIZE=${POPULATION_SIZE:-50}
MUTATION_RATE=${MUTATION_RATE:-0.1}
CROSSOVER_RATE=${CROSSOVER_RATE:-0.8}
MAX_GENERATIONS=${MAX_GENERATIONS:-100}
ELITE_SIZE=${ELITE_SIZE:-5}

# Export environment variables
export POPULATION_SIZE
export MUTATION_RATE
export CROSSOVER_RATE
export MAX_GENERATIONS
export ELITE_SIZE

echo "Evolution Configuration:"
echo "  Population Size: $POPULATION_SIZE"
echo "  Mutation Rate: $MUTATION_RATE"
echo "  Crossover Rate: $CROSSOVER_RATE"
echo "  Max Generations: $MAX_GENERATIONS"
echo "  Elite Size: $ELITE_SIZE"

# Run evolution engine
python -c "
import asyncio
import os
from src.geneticML import EvolutionEngine, GeneticAlgorithm, FitnessEvaluator

class Config:
    def __init__(self):
        self.population_size = int(os.environ.get('POPULATION_SIZE', 50))
        self.mutation_rate = float(os.environ.get('MUTATION_RATE', 0.1))
        self.crossover_rate = float(os.environ.get('CROSSOVER_RATE', 0.8))
        self.max_generations = int(os.environ.get('MAX_GENERATIONS', 100))
        self.elite_size = int(os.environ.get('ELITE_SIZE', 5))
        self.fitness_threshold = 0.9

class MockAgent:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.gene_template = {
            'param1': 0.5,
            'param2': True,
            'param3': 'medium'
        }
        self.gene_ranges = {
            'param1': (0.0, 1.0),
            'param2': [True, False],
            'param3': ['low', 'medium', 'high']
        }
        self.chromosome = None
    
    def set_chromosome(self, chromosome):
        self.chromosome = chromosome
    
    def process_input(self, input_data):
        return {'success': True, 'content': 'Mock response'}

async def main():
    print('Initializing GeneticML standalone evolution...')
    
    # Create mock agents
    agents = {
        'agent1': MockAgent('agent1'),
        'agent2': MockAgent('agent2'),
        'agent3': MockAgent('agent3')
    }
    
    # Initialize evolution engine
    config = Config()
    engine = EvolutionEngine(agents, config)
    await engine.initialize()
    
    # Run evolution
    await engine.evolve(max_generations=5)  # Short run for demo
    
    # Print results
    status = engine.get_status()
    print('Evolution completed!')
    print(f'Best fitness scores: {status[\"best_fitness_scores\"]}')

asyncio.run(main())
"

echo "GeneticML Evolution Engine completed successfully!"
