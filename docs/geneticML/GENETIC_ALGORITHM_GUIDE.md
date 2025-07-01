# Genetic Algorithm Implementation Guide

## Overview

The genetic algorithm has been successfully implemented and integrated into the agentic AI customer support system. This document explains how the genetic algorithm works, its components, and how to use it.

## 🧬 Architecture

### Core Components

1. **Chromosome** (`src/geneticML/core/genetic_algorithm.py`)
   - Represents agent configuration as genes
   - Supports mutation, crossover, and distance calculation
   - Handles different gene types (numeric, boolean, categorical)

2. **GeneticAlgorithm** (`src/geneticML/core/genetic_algorithm.py`)
   - Manages population of chromosomes
   - Implements selection, crossover, mutation operations
   - Tracks evolution statistics and history

3. **FitnessEvaluator** (`src/geneticML/evaluators/fitness_evaluator.py`)
   - Evaluates chromosome performance using test cases
   - Calculates multi-dimensional fitness metrics
   - Provides weighted scoring system

4. **EvolutionEngine** (`src/geneticML/engines/evolution_engine.py`)
   - Orchestrates evolution across multiple agents
   - Manages test cases and fitness evaluation
   - Handles adaptive evolution based on real interactions

## 🎯 How It Works

### Agent Gene Templates

Each agent type has specific genes that control its behavior:

#### Query Agent Genes
```python
{
    'confidence_threshold': 0.8,        # Confidence threshold for analysis
    'context_window_size': 1000,        # Context processing window
    'include_sentiment': True,          # Enable sentiment analysis
    'extract_entities': True,           # Enable entity extraction
    'urgency_detection': True,          # Enable urgency detection
    'response_timeout': 5.0,            # Processing timeout
    'max_analysis_depth': 3,            # Analysis depth level
    'language_detection_enabled': True  # Language detection
}
```

#### Knowledge Agent Genes
```python
{
    'search_depth': 5,                  # Knowledge search depth
    'relevance_threshold': 0.7,         # Relevance filtering threshold
    'max_sources': 10,                  # Maximum knowledge sources
    'include_citations': True,          # Include source citations
    'fact_checking_enabled': True,      # Enable fact checking
    'synthesis_level': 'detailed',      # Synthesis complexity
    'search_timeout': 10.0,             # Search timeout
    'confidence_boost': 1.0,            # Confidence multiplier
    'source_diversity': 0.8             # Source diversity requirement
}
```

#### Response Agent Genes
```python
{
    'tone': 'friendly',                 # Response tone
    'length_preference': 'medium',      # Response length
    'personalization_level': 0.7,      # Personalization degree
    'empathy_level': 0.8,              # Empathy level
    'formality_level': 0.6,            # Formality level
    'include_suggestions': True,        # Include helpful suggestions
    'response_timeout': 8.0,            # Response generation timeout
    'creativity_level': 0.5,           # Creative response generation
    'solution_focus': 0.9              # Focus on providing solutions
}
```

### Evolution Process

1. **Initialization**: Create random population of chromosomes for each agent
2. **Evaluation**: Test chromosomes using predefined test cases
3. **Selection**: Choose best performing chromosomes as parents
4. **Crossover**: Combine parent chromosomes to create offspring
5. **Mutation**: Introduce random variations to maintain diversity
6. **Replacement**: Replace old population with new generation
7. **Iteration**: Repeat until convergence or maximum generations

### Fitness Evaluation

Fitness is calculated based on multiple metrics:

- **Accuracy**: Percentage of successful responses
- **Response Time**: Processing speed (normalized)
- **Customer Satisfaction**: Quality of responses
- **Resolution Rate**: Meaningful response generation
- **Consistency**: Variance in performance

## 🚀 Usage

### Basic Usage

```python
from src.geneticML.engines.evolution_engine import EvolutionEngine
from a2a_protocol.a2a_query_agent import A2AQueryAgent
from a2a_protocol.a2a_knowledge_agent import A2AKnowledgeAgent
from a2a_protocol.a2a_response_agent import A2AResponseAgent

# Create agents
agents = {
    'query': A2AQueryAgent(api_key="your_api_key"),
    'knowledge': A2AKnowledgeAgent(api_key="your_api_key"),
    'response': A2AResponseAgent(api_key="your_api_key")
}

# Create evolution engine
config = {
    'population_size': 50,
    'mutation_rate': 0.1,
    'crossover_rate': 0.8,
    'elite_size': 5,
    'max_generations': 100,
    'fitness_threshold': 0.9
}

engine = EvolutionEngine(agents=agents, config=config)

# Initialize and run evolution
await engine.initialize()
await engine.evolve(max_generations=50)

# Get results
status = engine.get_status()
results = engine.export_results()
```

### Manual Chromosome Application

```python
from core.genetic_algorithm import Chromosome

# Create custom chromosome
custom_genes = {
    'confidence_threshold': 0.9,
    'include_sentiment': True,
    'response_timeout': 3.0
}

chromosome = Chromosome(genes=custom_genes)

# Apply to agent
agent = A2AQueryAgent(api_key="your_api_key")
agent.set_chromosome(chromosome)

# Test the agent
test_input = {'query': 'I need help with my account'}
result = agent.process_input(test_input)
```

### Continuous Learning

The system supports adaptive evolution based on real interactions:

```python
# Record interaction results
interaction_result = {
    'original_query': 'User query here',
    'query_analysis': {...},
    'knowledge_search': {...},
    'response_generation': {...},
    'customer_feedback': 4.5  # Customer satisfaction score
}

await engine.record_interaction(interaction_result)
# Adaptive evolution triggers automatically every 100 interactions
```

## 📊 Monitoring and Analysis

### Evolution Statistics

```python
# Get current status
status = engine.get_status()
print(f"Generation: {status['current_generation']}")
print(f"Best fitness: {status['best_fitness_scores']}")

# Get evolution history
history = engine.export_results()
for gen_data in history['evolution_history']:
    print(f"Gen {gen_data['generation']}: {gen_data['stats']}")
```

### Individual Agent Performance

```python
# Get agent-specific metrics
for agent_id, ga in engine.genetic_algorithms.items():
    stats = ga.get_population_stats()
    best = ga.get_best_chromosome()
    print(f"{agent_id}: Best fitness = {best.fitness}")
    print(f"  Genes: {best.genes}")
```

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Genetic Algorithm Settings
POPULATION_SIZE=50
MUTATION_RATE=0.1
CROSSOVER_RATE=0.8
ELITE_SIZE=5
MAX_GENERATIONS=100
FITNESS_THRESHOLD=0.9
```

### Custom Gene Ranges

You can customize gene ranges for specific use cases:

```python
# Custom gene ranges for Query Agent
custom_ranges = {
    'confidence_threshold': (0.5, 0.95),  # Narrower range
    'context_window_size': (500, 2000),   # Specific window sizes
    'response_timeout': (2.0, 10.0)       # Faster responses
}

agent = A2AQueryAgent(api_key="your_api_key")
# Apply custom ranges during evolution
engine.genetic_algorithms['query'].set_gene_ranges(custom_ranges)
```

## 🧪 Testing

Run the test suite to verify the implementation:

```bash
python tests/geneticml/test_genetic_algorithm.py
```

This tests:
- Chromosome operations (mutation, crossover, distance)
- Genetic algorithm functionality
- Agent genetic support
- Fitness evaluation
- Evolution engine integration

## 📈 Performance Tuning

### Population Size
- Larger populations: Better exploration, slower evolution
- Smaller populations: Faster evolution, may miss optimal solutions
- Recommended: 30-100 for production

### Mutation Rate
- Higher rates: More exploration, slower convergence
- Lower rates: Faster convergence, may get stuck in local optima
- Recommended: 0.05-0.2

### Crossover Rate
- Higher rates: More exploitation of good solutions
- Lower rates: More reliance on mutation for diversity
- Recommended: 0.6-0.9

### Elite Size
- Preserves best solutions across generations
- Should be 5-20% of population size
- Prevents regression but may slow evolution

## 🔄 Integration with Main System

The genetic algorithm is integrated into the main system through:

1. **Automatic Initialization**: Agents get default gene templates
2. **Runtime Evolution**: Background evolution based on performance
3. **Adaptive Learning**: Continuous improvement from real interactions
4. **Configuration Management**: Gene settings through environment variables

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **API Key Issues**: Set proper API keys for LLM providers
3. **Memory Usage**: Large populations may consume significant memory
4. **Convergence**: Adjust mutation rate if evolution stagnates

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed evolution progress
await engine.evolve(max_generations=10)
```

## 🔮 Future Enhancements

Planned improvements:

1. **Multi-objective Optimization**: Optimize for multiple fitness criteria
2. **Distributed Evolution**: Scale across multiple machines
3. **Advanced Selection Methods**: Implement NSGA-II, SPEA2
4. **Dynamic Gene Addition**: Add new genes during evolution
5. **Transfer Learning**: Share knowledge between agent types

## 📝 Best Practices

1. **Start Small**: Begin with small populations and few generations
2. **Monitor Convergence**: Track fitness progress to avoid overfitting
3. **Regular Evaluation**: Periodically test on new data
4. **Backup Best Chromosomes**: Save successful configurations
5. **A/B Testing**: Compare evolved vs. default configurations

---

This genetic algorithm implementation provides a powerful foundation for evolving and optimizing AI agent behavior in the customer support system. The system continuously learns and improves, adapting to changing requirements and customer needs.
