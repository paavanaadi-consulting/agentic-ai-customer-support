# GeneticML Test Suite

This directory contains comprehensive test cases for the `src/geneticML` module, which implements genetic algorithms and evolution strategies for optimizing AI agent performance in the customer support system.

## Test Structure

### Core Test Modules

1. **`test_genetic_algorithm_enhanced.py`** - Enhanced comprehensive tests for GeneticAlgorithm and Chromosome classes
2. **`test_fitness_evaluator.py`** - Comprehensive tests for fitness evaluation and metrics
3. **`test_evolution_engine.py`** - Tests for evolution engine and multi-agent coordination

### Test Coverage

The test suite covers:

- **Chromosome Operations**: Mutation, crossover, distance calculation, copying
- **Genetic Algorithm**: Population management, selection methods, evolution cycles
- **Fitness Evaluation**: Metrics calculation, similarity assessment, performance scoring
- **Evolution Engine**: Multi-agent coordination, adaptive evolution, convergence detection
- **Integration Scenarios**: Customer support optimization, multi-objective evolution
- **Error Handling**: Edge cases, malformed data, exception scenarios

## Running Tests

### Method 1: Using pytest (Recommended)

If you have pytest installed:

```bash
# Run all geneticML tests
pytest tests/geneticml/ -v

# Run specific test file
pytest tests/geneticml/test_genetic_algorithm_enhanced.py -v

# Run with coverage
pytest tests/geneticml/ -v --cov=src.geneticML --cov-report=html

# Run specific test class
pytest tests/geneticml/test_fitness_evaluator.py::TestFitnessEvaluator -v

# Run specific test method
pytest tests/geneticml/test_evolution_engine.py::TestEvolutionEngine::test_initialize_engine -v
```

### Method 2: Using the Test Runner Script

For basic functionality testing without pytest:

```bash
# Run the test runner script
python tests/geneticml/run_tests.py

# Or make it executable and run
chmod +x tests/geneticml/run_tests.py
./tests/geneticml/run_tests.py
```

### Method 3: Using Python unittest

```bash
# From project root
python -m unittest discover tests/geneticml/ -v
```

## Test Categories

### Unit Tests

- **Chromosome Class Tests**
  - Initialization and default values
  - Mutation operations (numeric, boolean, categorical)
  - Crossover operations and offspring generation
  - Distance calculation between chromosomes
  - Copy operations and deep copying

- **GeneticAlgorithm Class Tests**
  - Population initialization and management
  - Selection methods (tournament, roulette, rank)
  - Evolution cycles and generation progression
  - Statistics tracking and history
  - Elite preservation and diversity calculation

- **FitnessEvaluator Tests**
  - Fitness metrics calculation
  - Weighted scoring systems
  - Similarity assessment algorithms
  - Performance evaluation pipelines

- **EvolutionEngine Tests**
  - Multi-agent coordination
  - Adaptive evolution based on interactions
  - Convergence detection
  - Configuration management

### Integration Tests

- **Customer Support Agent Evolution**
  - Realistic gene templates for support agents
  - Multi-objective fitness optimization
  - Performance improvement tracking

- **Multi-Agent System Tests**
  - Query, Knowledge, and Response agent coordination
  - Cross-agent optimization strategies
  - System-wide performance metrics

### Performance Tests

- **Large Population Handling**
  - Testing with populations of 50+ chromosomes
  - Performance benchmarking
  - Memory usage optimization

- **Convergence Analysis**
  - Testing convergence detection algorithms
  - Diversity maintenance strategies
  - Premature convergence prevention

### Error Handling Tests

- **Edge Cases**
  - Empty populations
  - Zero mutation rates
  - Invalid gene ranges
  - Malformed fitness functions

- **Exception Scenarios**
  - Agent failures during evaluation
  - Invalid configuration parameters
  - Memory constraints

## Test Data and Fixtures

### Common Fixtures

- **Mock Agents**: Simulated customer support agents with realistic gene templates
- **Gene Templates**: Pre-defined gene structures for different agent types
- **Gene Ranges**: Validation ranges for genetic parameters
- **Test Cases**: Sample customer queries and expected responses

### Realistic Scenarios

The tests include realistic customer support scenarios:

- Password reset requests
- Billing inquiries and refund requests
- Feature requests and feedback
- Escalation scenarios
- Multi-language support needs

## Genetic Algorithm Parameters

### Default Test Parameters

```python
# Standard test configuration
population_size = 20
mutation_rate = 0.15
crossover_rate = 0.8
elite_size = 3
max_generations = 10
fitness_threshold = 0.85
```

### Agent-Specific Gene Templates

#### Query Agent
```python
gene_template = {
    'confidence_threshold': 0.8,
    'context_window_size': 1000,
    'sentiment_analysis_enabled': True,
    'entity_extraction_enabled': True,
    'urgency_detection_enabled': True
}
```

#### Knowledge Agent
```python
gene_template = {
    'search_depth': 5,
    'relevance_threshold': 0.7,
    'max_sources': 10,
    'fact_checking_enabled': True,
    'synthesis_level': 'detailed'
}
```

#### Response Agent
```python
gene_template = {
    'empathy_level': 0.8,
    'formality_level': 0.6,
    'personalization_level': 0.7,
    'response_length': 'medium',
    'tone': 'friendly'
}
```

## Fitness Evaluation Metrics

### Primary Metrics

1. **Accuracy**: Percentage of correct responses (0.0 - 1.0)
2. **Response Time**: Processing speed (lower is better)
3. **Customer Satisfaction**: User satisfaction score (0.0 - 1.0)
4. **Resolution Rate**: Percentage of successfully resolved queries
5. **Consistency**: Reliability across different query types

### Weighted Scoring

```python
default_weights = {
    'accuracy': 0.25,
    'response_time': 0.20,
    'customer_satisfaction': 0.25,
    'resolution_rate': 0.20,
    'consistency': 0.10
}
```

## Continuous Integration

### Running Tests in CI/CD

```yaml
# Example GitHub Actions configuration
- name: Run GeneticML Tests
  run: |
    pip install pytest pytest-cov
    pytest tests/geneticml/ -v --cov=src.geneticML --cov-report=xml
```

### Test Requirements

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock numpy
```

## Expected Test Results

### Success Criteria

- All unit tests should pass
- Integration tests should show fitness improvement over generations
- Performance tests should complete within reasonable time limits
- Error handling tests should gracefully handle edge cases

### Typical Output

```
tests/geneticml/test_genetic_algorithm_enhanced.py::TestChromosome::test_mutation_numeric_genes PASSED
tests/geneticml/test_fitness_evaluator.py::TestFitnessEvaluator::test_evaluate_chromosome_successful_cases PASSED
tests/geneticml/test_evolution_engine.py::TestEvolutionEngine::test_full_evolution_cycle PASSED

========================= 150 passed in 45.2s =========================
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the project root is in Python path
2. **Missing Dependencies**: Install required packages (numpy, pytest)
3. **Slow Tests**: Some evolution tests may take time due to genetic algorithm iterations
4. **Random Failures**: Genetic algorithms use randomness; some tests may occasionally fail

### Debug Mode

```python
# Enable debug logging in tests
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When adding new tests:

1. Follow the existing naming conventions
2. Include docstrings explaining test purpose
3. Use appropriate fixtures for setup
4. Test both success and failure scenarios
5. Include realistic data in integration tests

## Performance Benchmarks

### Expected Performance

- **Small Population (10)**: ~0.1s per generation
- **Medium Population (50)**: ~0.5s per generation  
- **Large Population (100)**: ~1.0s per generation

### Memory Usage

- Each chromosome: ~1KB
- Population of 100: ~100KB
- Full evolution (50 generations): ~5MB

## Related Documentation

- [GeneticML Module Documentation](../../src/geneticML/README.md)
- [Customer Support Architecture](../../docs/ARCHITECTURE.md)
- [AI Agent Integration Guide](../../docs/AI_INTEGRATION.md)
