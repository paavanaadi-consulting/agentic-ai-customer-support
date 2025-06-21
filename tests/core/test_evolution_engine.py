from core.evolution_engine import EvolutionEngine

class DummyAgent:
    def __init__(self, agent_id):
        self.agent_id = agent_id
    async def process_input(self, data):
        return {"result": "ok"}

def test_evolution_engine_init():
    agents = {"a": DummyAgent("a"), "b": DummyAgent("b")}
    config = {"population_size": 2, "mutation_rate": 0.1, "crossover_rate": 0.8, "elite_size": 1, "max_generations": 2, "fitness_threshold": 0.9}
    engine = EvolutionEngine(agents=agents, config=config)
    assert engine.agents == agents
    assert engine.config == config
