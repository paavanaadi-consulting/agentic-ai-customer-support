from core.fitness_evaluator import FitnessEvaluator

def test_fitness_evaluator_basic():
    evaluator = FitnessEvaluator()
    result = evaluator.evaluate({"score": 0.8})
    assert isinstance(result, dict)
