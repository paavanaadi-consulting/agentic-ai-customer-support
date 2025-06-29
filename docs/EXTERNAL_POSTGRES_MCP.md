# Using External PostgreSQL MCP Package

This repository now integrates with the external `postgres-mcp` package from https://github.com/crystaldba/postgres-mcp for enhanced PostgreSQL operations.

## What is postgres-mcp?

The `postgres-mcp` package is a specialized Model Context Protocol (MCP) server for PostgreSQL databases that provides:

- **Advanced Schema Introspection**: Detailed database schema analysis
- **Query Optimization**: Intelligent query planning and execution
- **Security Features**: Built-in SQL injection protection
- **Connection Pooling**: Efficient database connection management
- **Transaction Management**: ACID compliance and rollback support
- **Full-text Search**: Advanced PostgreSQL search capabilities

## Integration Architecture

```
Our Application
    ↓
PostgresMCPWrapper (our wrapper)
    ↓
postgres-mcp (external package)
    ↓
PostgreSQL Database
```

## Installation

### Option 1: Automatic Installation
```bash
# Run our enhanced installation script
./scripts/install_external_mcp.sh
```

### Option 2: Manual Installation
```bash
# Install base requirements
pip install -r requirements.txt

# Install external postgres-mcp package
pip install git+https://github.com/crystaldba/postgres-mcp.git
```

## Configuration

### Environment Variables
```bash
# Copy and edit the PostgreSQL MCP configuration
cp config/postgres_mcp.env .env.postgres

# Edit connection settings
nano .env.postgres
```

### Connection String Format
```bash
# For PostgreSQL
POSTGRES_MCP_CONNECTION_STRING=postgresql://username:password@host:port/database

# For local testing with SQLite (fallback)
SQLITE_MCP_CONNECTION_STRING=sqlite:///./data/test.db
```

## Usage Examples

### 1. Basic Database Operations
```python
from mcp.postgres_mcp_wrapper import PostgresMCPWrapper

# Initialize wrapper
db_server = PostgresMCPWrapper("postgresql://admin:password@localhost:5432/customer_support")
await db_server.start()

# Execute query
result = await db_server.call_tool("query", {
    "query": "SELECT * FROM customers WHERE customer_id = %s",
    "params": ["customer_123"]
})

# List tables
tables = await db_server.call_tool("list_tables", {"schema": "public"})

# Describe table structure
schema = await db_server.call_tool("describe_table", {
    "table_name": "customers",
    "schema": "public"
})
```

### 2. Customer Support Specific Operations
```python
# Get comprehensive customer context
customer_context = await db_server.call_tool("get_customer_context", {
    "customer_id": "customer_123"
})

# Search knowledge base with full-text search
knowledge_results = await db_server.call_tool("search_knowledge_base", {
    "query": "password reset",
    "limit": 10
})

# Save customer interaction
interaction_result = await db_server.call_tool("save_interaction", {
    "interaction_data": {
        "interaction_id": "int_12345",
        "customer_id": "customer_123",
        "query_text": "How do I reset my password?",
        "agent_response": "Visit the login page and click 'Forgot Password'.",
        "customer_satisfaction": 5
    }
})
```

### 3. Analytics and Reporting
```python
# Get system analytics
analytics = await db_server.call_tool("get_analytics", {
    "days": 7
})
```

## Features Comparison

| Feature | Our Custom DB Server | External postgres-mcp | Combined (Wrapper) |
|---------|---------------------|----------------------|-------------------|
| Basic CRUD | ✅ | ✅ | ✅ |
| Schema Introspection | Limited | ✅ Advanced | ✅ Advanced |
| Query Optimization | Basic | ✅ Intelligent | ✅ Intelligent |
| Security | Basic | ✅ Advanced | ✅ Advanced |
| Connection Pooling | No | ✅ | ✅ |
| Transaction Management | Basic | ✅ Advanced | ✅ Advanced |
| Customer Support Queries | ✅ | No | ✅ |
| Knowledge Base Search | ✅ | No | ✅ |
| Analytics | ✅ | No | ✅ |

## Fallback Mechanism

The wrapper includes intelligent fallback:

1. **Try External Package**: Attempts to use `postgres-mcp` for PostgreSQL operations
2. **Fallback to Custom**: If external package unavailable, falls back to our custom implementation
3. **SQLite Support**: Automatically switches to SQLite for local testing

```python
# Automatic fallback logic in wrapper
try:
    from postgres_mcp import PostgresMCPServer as ExternalPostgresMCPServer
    # Use external package
except ImportError:
    # Fall back to our custom implementation
    from mcp.database_mcp_server import DatabaseMCPServer
```

## Testing

### Unit Tests
```bash
# Test with external package
python -m pytest tests/mcp_servers/test_postgres_mcp_wrapper.py -v

# Test fallback mechanism
python -m pytest tests/mcp_servers/test_database_fallback.py -v
```

### Integration Tests
```bash
# Test full integration
python scripts/test_native.py --scenario database

# Test with PostgreSQL
python scripts/test_native.py --database postgresql

# Test with SQLite fallback
python scripts/test_native.py --database sqlite
```

## Troubleshooting

### Issue: External package not found
```bash
# Solution: Install the package
pip install git+https://github.com/crystaldba/postgres-mcp.git

# Verify installation
python -c "import postgres_mcp; print('✅ Package available')"
```

### Issue: Connection errors
```bash
# Check PostgreSQL connection
psql -h localhost -U admin -d customer_support

# Test connection string
python -c "
import psycopg2
conn = psycopg2.connect('postgresql://admin:password@localhost:5432/customer_support')
print('✅ Connection successful')
conn.close()
"
```

### Issue: Permission errors
```bash
# Grant necessary permissions
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE customer_support TO admin;"
```

## Benefits of Using External Package

1. **Maintenance**: Externally maintained and updated
2. **Performance**: Optimized for PostgreSQL operations
3. **Security**: Built-in security best practices
4. **Features**: Advanced PostgreSQL features
5. **Community**: Shared development and bug fixes
6. **Standards**: Follows MCP protocol standards

## Custom Extensions

Our wrapper adds customer support specific functionality:

- **Customer Context Queries**: Comprehensive customer data retrieval
- **Knowledge Base Search**: Full-text search with relevance scoring
- **Interaction Logging**: Customer interaction tracking
- **Analytics Queries**: Business intelligence and reporting
- **Satisfaction Tracking**: Customer satisfaction metrics

This approach gives us the best of both worlds: the robustness of an external, maintained package for core database operations, plus our custom business logic for customer support specific needs.
