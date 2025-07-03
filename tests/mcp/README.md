# MCP Test Suite

Comprehensive test suite for all Model Context Protocol (MCP) modules in the `src/mcp` directory.

## Overview

This test suite provides complete coverage for all MCP client and server implementations, including:

- **Interface compliance testing** - Ensures all implementations follow the MCP interface contract
- **Connection and communication testing** - Tests WebSocket, HTTP, and external process connections
- **Error handling and resilience** - Validates error scenarios and recovery mechanisms
- **Integration testing** - Tests interactions between different MCP components
- **Performance and concurrency** - Tests concurrent operations and performance characteristics

## Test Coverage

### Core MCP Components

| Module | Test File | Coverage Areas |
|--------|-----------|----------------|
| `mcp_client_interface.py` | `test_mcp_client_interface.py` | Abstract interface compliance, method signatures, documentation |
| `mcp_client.py` | `test_mcp_client.py` | WebSocket client, tool/resource calls, error handling, customer support operations |
| `mcp_client_manager.py` | `test_mcp_client_manager.py` | Client registry, routing, AWS integration, concurrency |
| `base_mcp_server.py` | `test_base_mcp_server.py` | Abstract server implementation, message processing, lifecycle |

### Database Integration

| Module | Test File | Coverage Areas |
|--------|-----------|----------------|
| `postgres_mcp_client.py` | `test_postgres_mcp_client.py` | PostgreSQL connections, CRUD operations, caching, analytics |

### Message Queue Integration

| Module | Test File | Coverage Areas |
|--------|-----------|----------------|
| `kafka_mcp_client.py` | `test_kafka_mcp_client.py` | Kafka connections, message pub/sub, topic management, customer support |

### AWS Integration

| Module | Test File | Coverage Areas |
|--------|-----------|----------------|
| `aws_mcp_client.py` | `test_aws_mcp_client.py` | AWS SDK integration, Lambda/SNS/SQS operations, external MCP servers |
| `aws_mcp_wrapper.py` | `test_aws_mcp_wrapper.py` | External AWS MCP server wrapper, package management, fallback handling |

## Running Tests

### Prerequisites

Ensure you have the required testing dependencies:

```bash
pip install pytest pytest-asyncio pytest-cov
```

### Run All Tests

```bash
# Run all MCP tests with coverage
python tests/mcp/run_tests.py

# Run all tests without coverage
python tests/mcp/run_tests.py --no-coverage

# Run all tests in quiet mode
python tests/mcp/run_tests.py --quiet
```

### Run Specific Test Modules

```bash
# Run specific test module
python tests/mcp/run_tests.py --module test_mcp_client

# Run specific test function
python tests/mcp/run_tests.py --module test_mcp_client --function test_websocket_connection
```

### Using pytest directly

```bash
# Run all MCP tests
pytest tests/mcp/ -v

# Run with coverage
pytest tests/mcp/ --cov=src.mcp --cov-report=html

# Run specific test file
pytest tests/mcp/test_mcp_client.py -v

# Run specific test function
pytest tests/mcp/test_mcp_client.py::TestMCPClient::test_websocket_connection -v
```

### List Available Tests

```bash
python tests/mcp/run_tests.py --list
```

## Test Structure

Each test file follows a consistent structure:

### Class-Based Organization
- Tests are organized into classes by functionality area
- Each class focuses on a specific aspect (e.g., connection, tools, errors)
- Fixtures are used for common setup and teardown

### Test Categories

1. **Unit Tests** - Test individual methods and functions
2. **Integration Tests** - Test interactions between components
3. **Error Handling Tests** - Test exception scenarios and recovery
4. **Performance Tests** - Test concurrent operations and timeouts
5. **Configuration Tests** - Test different configuration scenarios

### Mock Strategy

- External dependencies (AWS, Kafka, PostgreSQL) are mocked
- Network calls are mocked to avoid external dependencies
- File system operations use temporary directories
- Async operations use proper async test fixtures

## Test Data and Fixtures

### Common Fixtures

- `mock_config` - Standard configuration for testing
- `mock_logger` - Logger instance for testing
- `temp_dir` - Temporary directory for file operations
- `mock_websocket` - Mocked WebSocket connection
- `mock_aws_session` - Mocked AWS session

### Test Data

- Customer data for customer support scenarios
- Ticket data for helpdesk operations
- Analytics data for reporting tests
- AWS resource identifiers for cloud operations

## Coverage Requirements

- **Minimum Coverage**: 80% for all modules
- **Target Coverage**: 90%+ for critical components
- **Coverage Reports**: Generated in `test-results/mcp-coverage/`

### Coverage Areas

1. **Line Coverage** - All executable lines
2. **Branch Coverage** - All conditional branches
3. **Function Coverage** - All function definitions
4. **Class Coverage** - All class definitions

## Continuous Integration

### GitHub Actions

The test suite is designed to run in CI/CD pipelines:

```yaml
- name: Run MCP Tests
  run: |
    python tests/mcp/run_tests.py --no-coverage
```

### Local Development

For local development, use the test runner with coverage:

```bash
python tests/mcp/run_tests.py
```

## Mock Services

### Database Mocking

PostgreSQL operations are mocked using:
- `asyncpg` connection mocking
- HTTP client mocking for external MCP servers
- Query result simulation

### AWS Service Mocking

AWS services are mocked using:
- `boto3` session and client mocking
- Lambda function invocation simulation
- SNS/SQS message handling simulation

### Kafka Mocking

Kafka operations are mocked using:
- Producer/consumer simulation
- Topic management mocking
- Message serialization testing

## Performance Testing

### Concurrent Operations

Tests validate:
- Multiple simultaneous client connections
- Concurrent tool executions
- Resource access under load
- Connection pool management

### Timeout Handling

Tests validate:
- Connection timeouts
- Operation timeouts
- Retry mechanisms
- Circuit breaker patterns

## Error Scenarios

### Network Errors

- Connection failures
- Network timeouts
- Service unavailability
- DNS resolution failures

### Service Errors

- Authentication failures
- Authorization errors
- Service-specific errors (AWS, Kafka, PostgreSQL)
- Rate limiting

### Data Errors

- Invalid JSON responses
- Missing required fields
- Type conversion errors
- Validation failures

## Debugging Tests

### Verbose Output

Use `-v` flag for detailed test output:

```bash
pytest tests/mcp/test_mcp_client.py -v
```

### Test Isolation

Each test is isolated:
- Fresh mock instances
- Clean configuration
- Independent async event loops
- Temporary resources

### Logging

Test logging can be enabled:

```bash
pytest tests/mcp/ -v --log-cli-level=DEBUG
```

## Contributing

### Adding New Tests

1. Create test file following naming convention: `test_<module_name>.py`
2. Use consistent class and method naming
3. Include comprehensive docstrings
4. Add appropriate fixtures
5. Mock external dependencies
6. Test both success and error scenarios

### Test Quality Guidelines

1. **Isolation** - Tests should not depend on each other
2. **Repeatability** - Tests should produce consistent results
3. **Clarity** - Test purpose should be obvious from name and docstring
4. **Coverage** - Aim for comprehensive path coverage
5. **Performance** - Tests should run efficiently

### Review Process

All test additions should:
- Pass all existing tests
- Maintain or improve coverage percentage
- Follow established patterns
- Include appropriate documentation
