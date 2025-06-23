# Model Context Protocol (MCP) Integration Guide

## Overview

The Customer Support AI system uses the Model Context Protocol (MCP) to provide modular, tool-based access to various data sources and services. MCP enables agents to interact with databases, cloud services, and message queues through a standardized interface.

## Architecture

### MCP Servers
MCP servers provide specific capabilities to agents:
- **Database MCP Server**: PostgreSQL database operations
- **Kafka MCP Server**: Apache Kafka messaging and streaming
- **AWS MCP Server**: AWS services (S3, Lambda, SSM Parameter Store)

### MCP Client
The MCP client manages connections to multiple MCP servers and provides a unified interface for agents.

## Supported MCP Servers

### 1. Database MCP Server (`database_mcp_server.py`)

**Capabilities**: Database operations for customer support data

**Tools**:
- `query_database`: Execute SQL queries
- `get_customer_context`: Retrieve customer information and history
- `search_knowledge_base`: Search knowledge articles
- `save_interaction`: Store customer interactions
- `get_analytics`: Retrieve system analytics

**Resources**:
- `db://customers`: Customer data
- `db://tickets`: Support tickets
- `db://knowledge_articles`: Knowledge base articles
- `db://interactions`: Customer interactions
- `db://analytics`: System analytics

**Example Usage**:
```python
# Get customer context
result = await mcp_client.call_tool("mcp_database", "get_customer_context", {
    "customer_id": "12345"
})

# Search knowledge base
articles = await mcp_client.call_tool("mcp_database", "search_knowledge_base", {
    "search_term": "password reset",
    "limit": 5
})
```

### 2. Kafka MCP Server (`kafka_mcp_server.py`)

**Capabilities**: Apache Kafka operations for real-time messaging

**Tools**:
- `publish_message`: Send messages to Kafka topics
- `consume_messages`: Consume messages from topics
- `get_topic_metadata`: Get topic information
- `create_topic`: Create new topics
- `list_topics`: List available topics

**Resources**:
- `kafka://topics`: Available topics
- `kafka://consumer-groups`: Consumer groups
- `kafka://brokers`: Broker information

**Example Usage**:
```python
# Publish a message
await mcp_client.call_tool("mcp_kafka", "publish_message", {
    "topic": "customer-queries",
    "message": {"query": "How to reset password?", "customer_id": "12345"},
    "key": "customer-12345"
})

# Consume messages
messages = await mcp_client.call_tool("mcp_kafka", "consume_messages", {
    "topic": "agent-responses",
    "group_id": "response-processors",
    "max_messages": 10
})
```

### 3. AWS MCP Server (`aws_mcp_server.py`)

**Capabilities**: AWS services integration

**Tools**:
- `s3_upload_file`: Upload files to S3
- `s3_download_file`: Download files from S3
- `s3_list_objects`: List S3 objects
- `s3_delete_object`: Delete S3 objects
- `lambda_invoke`: Invoke Lambda functions
- `get_parameter_store_value`: Get SSM parameters

**Resources**:
- `aws://s3/buckets`: Available S3 buckets
- `aws://lambda/functions`: Lambda functions
- `aws://ssm/parameters`: SSM parameters

**Example Usage**:
```python
# Upload a file to S3
await mcp_client.call_tool("mcp_aws", "s3_upload_file", {
    "bucket": "customer-documents",
    "key": "tickets/ticket-12345.pdf",
    "content": file_content,
    "content_type": "application/pdf"
})

# Invoke Lambda function
result = await mcp_client.call_tool("mcp_aws", "lambda_invoke", {
    "function_name": "process-customer-feedback",
    "payload": {"feedback": "Great service!", "customer_id": "12345"}
})
```

## Integration with A2A Agents

### Agent Configuration

Agents can be configured to use MCP servers through configuration:

```python
mcp_config = {
    "servers": {
        "mcp_database": {
            "uri": "ws://localhost:8001"
        },
        "mcp_kafka": {
            "uri": "ws://localhost:8002"
        },
        "mcp_aws": {
            "uri": "ws://localhost:8003"
        }
    }
}

agent = QueryAgent("query-agent-1", "query", mcp_config=mcp_config)
```

### Using MCP in Agents

```python
class QueryAgent(A2AAgent):
    async def process_query(self, query: str, customer_id: str):
        # Get customer context from database
        customer_context = await self.call_mcp_tool(
            "mcp_database", 
            "get_customer_context", 
            {"customer_id": customer_id}
        )
        
        # Search knowledge base
        relevant_articles = await self.call_mcp_tool(
            "mcp_database",
            "search_knowledge_base",
            {"search_term": query, "limit": 3}
        )
        
        # Publish query to Kafka for processing
        await self.call_mcp_tool(
            "mcp_kafka",
            "publish_message",
            {
                "topic": "customer-queries",
                "message": {
                    "query": query,
                    "customer_id": customer_id,
                    "context": customer_context,
                    "articles": relevant_articles
                }
            }
        )
```

## Setup and Configuration

### 1. Environment Setup

Create a `.env` file with MCP server configurations:

```env
# Database MCP
DB_MCP_HOST=localhost
DB_MCP_PORT=8001
DATABASE_URL=postgresql://user:password@localhost:5432/customer_support

# Kafka MCP
KAFKA_MCP_HOST=localhost
KAFKA_MCP_PORT=8002
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# AWS MCP
AWS_MCP_HOST=localhost
AWS_MCP_PORT=8003
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
```

### 2. Starting MCP Servers

```python
# Start all MCP servers
import asyncio
from mcp.database_mcp_server import DatabaseMCPServer
from mcp.kafka_mcp_server import KafkaMCPServer
from mcp.aws_mcp_server import AWSMCPServer
from data_sources.rdbms_connector import RDBMSConnector

async def start_mcp_servers():
    # Database MCP
    db_connector = RDBMSConnector()
    await db_connector.connect()
    db_server = DatabaseMCPServer(db_connector)
    await db_server.start()
    
    # Kafka MCP
    kafka_server = KafkaMCPServer("localhost:9092")
    await kafka_server.start()
    
    # AWS MCP
    aws_server = AWSMCPServer(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    )
    await aws_server.start()
    
    print("All MCP servers started successfully")

if __name__ == "__main__":
    asyncio.run(start_mcp_servers())
```

### 3. Agent Integration

```python
from a2a_protocol.base_a2a_agent import A2AAgent

# Configure MCP connections for agents
mcp_config = {
    "servers": {
        "mcp_database": {"uri": "ws://localhost:8001"},
        "mcp_kafka": {"uri": "ws://localhost:8002"},
        "mcp_aws": {"uri": "ws://localhost:8003"}
    }
}

# Create agent with MCP integration
agent = QueryAgent("query-agent", "query", mcp_config=mcp_config)
await agent.start()
```

## Development and Testing

### Running Tests

```bash
# Run all MCP tests
pytest tests/mcp_servers/ -v

# Run specific MCP server tests
pytest tests/mcp_servers/test_postgres_mcp.py -v
pytest tests/mcp_servers/test_kafka_mcp.py -v
pytest tests/mcp_servers/test_aws_mcp.py -v

# Run with coverage
pytest tests/mcp_servers/ --cov=mcp --cov-report=html
```

### Adding New MCP Servers

1. **Create the MCP Server**:
   ```python
   from mcp.base_mcp_server import BaseMCPServer
   
   class CustomMCPServer(BaseMCPServer):
       def __init__(self, config):
           tools = ['custom_tool']
           resources = ['custom://resource']
           super().__init__(
               server_id="mcp_custom",
               name="Custom MCP Server",
               capabilities=['tools', 'resources'],
               tools=tools,
               resources=resources
           )
   ```

2. **Implement Required Methods**:
   ```python
   async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
       # Implement tool logic
       pass
   
   async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
       # Implement resource retrieval
       pass
   ```

3. **Add Tests**:
   ```python
   # tests/mcp_servers/test_custom_mcp.py
   import pytest
   from mcp.custom_mcp_server import CustomMCPServer
   
   class TestCustomMCPServer:
       @pytest.fixture
       def custom_server(self):
           return CustomMCPServer(config)
       
       @pytest.mark.asyncio
       async def test_custom_tool(self, custom_server):
           result = await custom_server.call_tool('custom_tool', {})
           assert result['success'] is True
   ```

## Best Practices

### 1. Error Handling
- Always wrap MCP calls in try-catch blocks
- Provide meaningful error messages
- Implement retry logic for transient failures

### 2. Resource Management
- Close MCP connections properly
- Use connection pooling for high-traffic scenarios
- Monitor connection health

### 3. Security
- Use environment variables for sensitive configuration
- Implement proper authentication for MCP servers
- Validate all input parameters

### 4. Performance
- Cache frequently accessed data
- Use async/await for non-blocking operations
- Implement connection pooling where appropriate

## Troubleshooting

### Common Issues

1. **Connection Failures**:
   - Check server status and network connectivity
   - Verify configuration parameters
   - Review server logs

2. **Tool Not Found**:
   - Ensure tool is registered in server
   - Check tool name spelling
   - Verify server capabilities

3. **Resource Access Errors**:
   - Check resource URI format
   - Verify permissions
   - Review resource availability

### Monitoring and Logging

Enable logging for MCP operations:

```python
import logging

# Configure MCP logging
logging.getLogger("MCP").setLevel(logging.DEBUG)

# Enable detailed logging for specific servers
logging.getLogger("MCP.Database MCP Server").setLevel(logging.DEBUG)
```

## Future Enhancements

1. **Additional MCP Servers**:
   - Redis MCP for caching
   - Elasticsearch MCP for search
   - Email MCP for notifications

2. **Advanced Features**:
   - Load balancing across MCP servers
   - Automatic failover and recovery
   - Real-time monitoring dashboard

3. **Integration Improvements**:
   - GraphQL interface for MCP
   - WebSocket streaming for real-time data
   - Batch operation support
