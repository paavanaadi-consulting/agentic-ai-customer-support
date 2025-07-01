"""
GeneticML - Machine Learning and Genetic Algorithm Components
for Agentic AI Customer Support System

This package contains all genetic algorithm implementations, fitness evaluators,
and evolution engines for optimizing AI agent performance.
"""

from .core.genetic_algorithm import GeneticAlgorithm, Chromosome
from .evaluators.fitness_evaluator import FitnessEvaluator
from .engines.evolution_engine import EvolutionEngine

__version__ = "1.0.0"
__author__ = "Agentic AI Team"

__all__ = [
    "GeneticAlgorithm",
    "Chromosome", 
    "FitnessEvaluator",
    "EvolutionEngine"
]
