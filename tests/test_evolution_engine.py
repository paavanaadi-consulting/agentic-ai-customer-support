import pytest
import asyncio
from core.evolution_engine import EvolutionEngine

class DummyAgent:
    def set_chromosome(self, chromosome):
        self.chromosome = chromosome
    def process_input(self, input_data):
        return {
            'success': True,
            'processing_time': 0.5,
            'content': 'response',
            'category': input_data.get('query', ''),
            'sentiment': 'positive',
            'urgency': 'low'
        }

def get_config():
    class Config:
        population_size = 2
        mutation_rate = 0.1
        crossover_rate = 0.5
        elite_size = 1
        max_generations = 1
        fitness_threshold = 0.1
    return Config()

@pytest.mark.asyncio
async def test_evolution_engine_initialize():
    agents = {'query': DummyAgent()}
    config = get_config()
    engine = EvolutionEngine(agents, config)
    await engine.initialize()
    assert 'query' in engine.genetic_algorithms

@pytest.mark.asyncio
async def test_evolution_engine_evolve():
    agents = {'query': DummyAgent()}
    config = get_config()
    engine = EvolutionEngine(agents, config)
    await engine.initialize()
    await engine.evolve(max_generations=1)
    assert engine.current_generation == 0 or engine.current_generation == 1

@pytest.mark.asyncio
async def test_record_interaction_and_status():
    agents = {'query': DummyAgent()}
    config = get_config()
    engine = EvolutionEngine(agents, config)
    await engine.initialize()
    await engine.record_interaction({'query_analysis': {'analysis': {'category': 'test'}}})
    status = engine.get_status()
    assert status['total_interactions'] == 1
