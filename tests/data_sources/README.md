# Data Sources Test Suite

This directory contains comprehensive tests for all data source components in the Agentic AI Customer Support system.

## Test Structure

### 📄 Test Files

| Test File | Component | Coverage |
|-----------|-----------|----------|
| `test_pdf_processor.py` | PDFProcessor | Document processing, search, text chunking |
| `test_vector_db_client.py` | VectorDBClient | Vector operations, semantic search, Qdrant integration |
| `test_kafka_consumer.py` | KafkaConsumer | Message processing, event handling, producer/consumer |
| `test_rdbms_connector.py` | EnhancedRDBMSConnector | Database operations, analytics, query interactions |

### 🧪 Test Categories

Each test file includes three types of tests:

#### Unit Tests
- **Purpose**: Test individual methods and functionality
- **Scope**: Isolated component behavior with mocked dependencies
- **Examples**: Initialization, configuration validation, error handling

#### Integration Tests  
- **Purpose**: Test component interactions with external systems
- **Scope**: Component behavior with mocked external dependencies
- **Examples**: Database connections, Kafka message flows, vector operations

#### Performance Tests
- **Purpose**: Validate throughput and response times
- **Scope**: Bulk operations and concurrent processing
- **Examples**: Message processing speed, database operation performance

## Running Tests

### All Data Source Tests
```bash
# Run all data source tests
pytest tests/data_sources/ -v

# Run with coverage
pytest tests/data_sources/ --cov=src.data_sources --cov-report=html
```

### Individual Component Tests
```bash
# PDF Processor tests
pytest tests/data_sources/test_pdf_processor.py -v

# Vector DB Client tests  
pytest tests/data_sources/test_vector_db_client.py -v

# Kafka Consumer tests
pytest tests/data_sources/test_kafka_consumer.py -v

# RDBMS Connector tests
pytest tests/data_sources/test_rdbms_connector.py -v
```

### Test Categories
```bash
# Unit tests only
pytest tests/data_sources/ -m "not integration and not performance" -v

# Integration tests only
pytest tests/data_sources/ -m integration -v

# Performance tests only
pytest tests/data_sources/ -m performance -v
```

## Test Configuration

### Mock Dependencies

Tests use comprehensive mocking to isolate components:

- **PDF Processing**: Mock file system, PyPDF2, scikit-learn
- **Vector Database**: Mock Qdrant client, sentence transformers  
- **Kafka**: Mock Kafka producers/consumers, message handlers
- **Database**: Mock psycopg2 connections, cursors, transactions

### Test Data

Test files include realistic mock data:
- Customer records with proper schema
- Support tickets with various statuses
- Knowledge base articles with metadata
- Query interactions with AI metrics

## Test Coverage

### Current Coverage Targets

| Component | Unit Tests | Integration Tests | Performance Tests |
|-----------|------------|-------------------|-------------------|
| PDFProcessor | ✅ 90%+ | ✅ 80%+ | ✅ 70%+ |
| VectorDBClient | ✅ 90%+ | ✅ 80%+ | ✅ 70%+ |
| KafkaConsumer | ✅ 90%+ | ✅ 80%+ | ✅ 70%+ |
| EnhancedRDBMSConnector | ✅ 95%+ | ✅ 85%+ | ✅ 75%+ |

### Key Test Scenarios

#### PDFProcessor
- ✅ Document loading and initialization
- ✅ Text extraction and chunking
- ✅ TF-IDF search functionality
- ✅ Document metadata management
- ✅ Error handling for corrupt files

#### VectorDBClient  
- ✅ Qdrant connection management
- ✅ Document embedding and indexing
- ✅ Semantic search operations
- ✅ Collection management
- ✅ Performance with large datasets

#### KafkaConsumer
- ✅ Producer/consumer lifecycle
- ✅ Message handler registration
- ✅ Event processing pipelines
- ✅ Error recovery and retry logic
- ✅ High-throughput message processing

#### EnhancedRDBMSConnector
- ✅ Database connection pooling
- ✅ Customer/ticket CRUD operations
- ✅ Knowledge base search
- ✅ Analytics and reporting queries
- ✅ AI interaction logging
- ✅ Performance metrics tracking

## Test Utilities

### Common Test Fixtures

```python
@pytest.fixture
def mock_config():
    """Standard configuration for testing."""
    return {
        'host': 'localhost',
        'port': 5432,
        'database': 'test_db'
    }

@pytest.fixture
def temp_directory():
    """Temporary directory for file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir
```

### Helper Functions

```python
def create_mock_message(message_type, payload):
    """Create mock Kafka message for testing."""
    
def generate_test_customer_data():
    """Generate realistic customer test data."""
    
def mock_database_response(query_type, data):
    """Mock database responses for testing."""
```

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- Pull requests to main branch
- Scheduled nightly builds
- Release tag creation

### Test Reporting

- **Coverage Reports**: Generated for each test run
- **Performance Benchmarks**: Tracked over time
- **Test Results**: Detailed logging and failure analysis

## Contributing

### Adding New Tests

1. **Follow naming convention**: `test_<component>_<functionality>.py`
2. **Include all categories**: Unit, integration, performance tests
3. **Use proper mocking**: Isolate external dependencies
4. **Add documentation**: Clear test descriptions and comments
5. **Update coverage**: Maintain coverage targets

### Test Standards

- **Async Support**: Use `@pytest.mark.asyncio` for async tests
- **Proper Cleanup**: Use fixtures for setup/teardown
- **Clear Assertions**: Descriptive assertion messages
- **Performance Metrics**: Include timing validations
- **Error Scenarios**: Test both success and failure cases

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Mock Dependencies**
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov
```

**Database Tests**
```bash
# Ensure PostgreSQL test database is available
createdb test_customer_support
```

### Debug Mode

```bash
# Run tests with detailed output
pytest tests/data_sources/ -v -s --tb=long

# Run specific test with debugging
pytest tests/data_sources/test_pdf_processor.py::TestPDFProcessor::test_initialization -v -s
```

## See Also

- [Main Data Sources Documentation](../../src/data_sources/README.md)
- [Testing Strategy](../README.md)
- [CI/CD Pipeline](.github/workflows/test.yml)
- [Coverage Reports](./htmlcov/index.html)
