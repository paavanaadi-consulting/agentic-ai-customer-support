# API Test Suite

This directory contains comprehensive tests for the `src/api` module of the Agentic AI Customer Support system.

## Overview

The test suite covers all aspects of the API module:

- **Schemas**: Pydantic model validation and serialization
- **Routes**: HTTP endpoint functionality and error handling
- **Dependencies**: Service injection and factory integration
- **Kafka Routes**: Streaming and messaging functionality
- **Application**: FastAPI app configuration and middleware
- **Integration**: End-to-end workflows and service integration

## Test Structure

```
tests/api/
├── conftest.py              # Test configuration and fixtures
├── test_schemas.py          # Schema validation tests
├── test_routes.py           # API route tests
├── test_kafka_routes.py     # Kafka/streaming route tests
├── test_dependencies.py     # Dependency injection tests
├── test_api_main.py         # Application configuration tests
├── test_integration.py      # Integration and E2E tests
├── run_tests.py            # Test runner script
└── README.md               # This file
```

## Running Tests

### Using the Test Runner

The recommended way to run tests is using the provided test runner:

```bash
# Run all tests
python tests/api/run_tests.py

# Run specific test types
python tests/api/run_tests.py --type unit
python tests/api/run_tests.py --type integration
python tests/api/run_tests.py --type kafka
python tests/api/run_tests.py --type performance

# Run with coverage
python tests/api/run_tests.py --coverage

# Run with verbose output
python tests/api/run_tests.py --verbose

# Run tests in parallel
python tests/api/run_tests.py --parallel
```

### Using pytest Directly

You can also run tests directly with pytest:

```bash
# Run all API tests
pytest tests/api/

# Run specific test file
pytest tests/api/test_schemas.py

# Run with coverage
pytest tests/api/ --cov=src.api --cov-report=html

# Run specific test class
pytest tests/api/test_routes.py::TestQueryEndpoints

# Run specific test method
pytest tests/api/test_routes.py::TestQueryEndpoints::test_process_query_success
```

## Test Categories

### Unit Tests

**Files**: `test_schemas.py`, `test_routes.py`, `test_dependencies.py`, `test_api_main.py`

These tests focus on individual components in isolation:

- Schema validation and serialization
- Individual route handlers
- Dependency injection mechanisms
- Application configuration

**Example**:
```bash
python tests/api/run_tests.py --type unit
```

### Integration Tests

**File**: `test_integration.py`

These tests verify interactions between components:

- End-to-end workflows
- Service integration
- Cross-cutting concerns
- Data consistency

**Example**:
```bash
python tests/api/run_tests.py --type integration
```

### Kafka/Streaming Tests

**File**: `test_kafka_routes.py`

These tests focus on real-time messaging and streaming:

- Message publishing and consuming
- Topic management
- Streaming queries
- Consumer management

**Example**:
```bash
python tests/api/run_tests.py --type kafka
```

### Performance Tests

Performance tests are marked with `@pytest.mark.slow` and can be run separately:

```bash
python tests/api/run_tests.py --type performance
```

## Test Fixtures

The `conftest.py` file provides comprehensive fixtures:

### Service Mocks
- `mock_query_service`
- `mock_ticket_service`
- `mock_customer_service`
- `mock_feedback_service`
- `mock_analytics_service`
- `mock_kafka_client`

### Test Data
- `sample_query_request`/`sample_query_response`
- `sample_ticket_request`/`sample_ticket_response`
- `sample_customer_request`/`sample_customer_response`
- `sample_feedback_request`/`sample_feedback_response`
- `sample_kafka_message_request`/`sample_kafka_message_response`

### Utilities
- `mock_service_dependencies` - Patches all service dependencies
- `test_client` - FastAPI test client
- Helper functions for generating test data

## Writing New Tests

### Test Naming Convention

- Test files: `test_<module>.py`
- Test classes: `Test<Component><Aspect>`
- Test methods: `test_<action>_<condition>`

**Example**:
```python
class TestQueryEndpoints:
    def test_process_query_success(self):
        """Test successful query processing."""
        pass
    
    def test_process_query_invalid_input(self):
        """Test query processing with invalid input."""
        pass
```

### Using Fixtures

```python
def test_query_processing(self, test_client, mock_service_dependencies, sample_query_request):
    """Test query processing with fixtures."""
    # Configure mock
    mock_service_dependencies['query_service'].process_query.return_value = expected_response
    
    # Make request
    response = test_client.post("/queries", json=sample_query_request.model_dump())
    
    # Assertions
    assert response.status_code == 200
```

### Mocking Services

```python
def test_service_interaction(self, mock_query_service):
    """Test service interaction."""
    # Setup mock behavior
    mock_query_service.process_query.return_value = mock_response
    
    # Test the interaction
    result = some_function_that_uses_service(mock_query_service)
    
    # Verify mock was called correctly
    mock_query_service.process_query.assert_called_once_with(expected_args)
```

## Test Markers

The test suite uses pytest markers for categorization:

- `@pytest.mark.slow` - Performance/long-running tests
- `@pytest.mark.skip` - Temporarily skipped tests
- `@pytest.mark.parametrize` - Parameterized tests

## Coverage Requirements

The test suite aims for high coverage:

- **Statements**: >90%
- **Branches**: >85%
- **Functions**: >95%

Generate coverage reports:
```bash
python tests/api/run_tests.py --coverage
```

View HTML coverage report:
```bash
open htmlcov/index.html
```

## Common Test Patterns

### Testing API Endpoints

```python
def test_endpoint_success(self, test_client, mock_service_dependencies):
    """Test successful endpoint response."""
    # Setup
    mock_service_dependencies['service'].method.return_value = expected_result
    
    # Action
    response = test_client.post("/endpoint", json=request_data)
    
    # Assert
    assert response.status_code == 200
    assert response.json()["field"] == expected_value
```

### Testing Error Handling

```python
def test_endpoint_error(self, test_client, mock_service_dependencies):
    """Test endpoint error handling."""
    # Setup
    mock_service_dependencies['service'].method.side_effect = Exception("Error")
    
    # Action
    response = test_client.post("/endpoint", json=request_data)
    
    # Assert
    assert response.status_code == 500
    assert "error message" in response.json()["detail"]
```

### Testing Schema Validation

```python
def test_schema_validation(self):
    """Test schema validation."""
    # Valid data
    valid_data = {"field": "value"}
    schema = Schema(**valid_data)
    assert schema.field == "value"
    
    # Invalid data
    with pytest.raises(ValidationError):
        Schema(**invalid_data)
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `src` directory is in PYTHONPATH
2. **Mock Issues**: Verify mock patches target the correct import path
3. **Async Issues**: Use `@pytest.mark.asyncio` for async tests
4. **Database Issues**: Use mocks instead of real database connections

### Debugging Tests

```bash
# Run single test with maximum verbosity
pytest tests/api/test_routes.py::test_specific_test -vvs

# Drop into debugger on failure
pytest tests/api/ --pdb

# Show local variables in tracebacks
pytest tests/api/ -l
```

## Contributing

When adding new features to the API:

1. Write tests first (TDD approach)
2. Ensure comprehensive coverage
3. Add appropriate test categories
4. Update fixtures if needed
5. Document test patterns

### Pull Request Checklist

- [ ] New tests for all new functionality
- [ ] All existing tests pass
- [ ] Coverage requirements met
- [ ] Tests are properly categorized
- [ ] Documentation updated

## Dependencies

Test dependencies are defined in the project's requirements files:

- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-xdist` - Parallel test execution
- `httpx` - Async HTTP client for testing
- `fastapi[testing]` - FastAPI test utilities

## Performance Considerations

- Use mocks to avoid external dependencies
- Run performance tests separately
- Consider parallel execution for large test suites
- Monitor test execution time

## Security Testing

The test suite includes security-focused tests:

- Input validation
- Data isolation
- Error information disclosure
- Authentication/authorization (when implemented)

## Continuous Integration

The test suite is designed to work with CI/CD pipelines:

```yaml
# Example CI configuration
test:
  script:
    - python tests/api/run_tests.py --coverage --parallel
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pydantic Testing](https://pydantic-docs.helpmanual.io/usage/validation_decorator/)
- [Mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
