# AWS MCP Client

## Overview

The AWS MCP Client provides a seamless integration between the Agentic AI Customer Support System and various AWS services through the Model Context Protocol (MCP). This client enables agents and other system components to leverage AWS cloud services directly, including Lambda, SNS, SQS, S3, and DynamoDB, with built-in error handling and performance optimization.

## Features

- **Direct SDK Integration**: Uses AWS SDK directly when available with fallback to MCP protocol
- **Multi-Service Support**: Integrates with Lambda, SNS, SQS, S3, DynamoDB, and Secrets Manager
- **Robust Error Handling**: Advanced retry and circuit breaking mechanisms
- **Performance Optimization**: Connection pooling and request batching
- **Security**: Supports AWS IAM roles and access key authentication

## Key Components

### AWS MCP Client (`aws_mcp_client.py`)

The client implementation that provides methods to interact with AWS services. It supports both direct SDK calls and WebSocket-based MCP communication.

### AWS MCP Server (`aws_mcp_server.py`)

The server implementation that exposes AWS services through the MCP protocol. It handles request routing, error handling, and provides a consistent interface.

### AWS MCP Wrapper (`aws_mcp_wrapper.py`)

A wrapper for external AWS MCP servers that provides a unified interface for all AWS MCP server implementations.

## Usage Examples

### Basic Usage

```python
from src.mcp.aws_mcp_client import OptimizedAWSMCPClient
from config.settings import CONFIG

# Get AWS configuration
aws_config = CONFIG.get("mcp_aws", {})

# Create and connect AWS MCP client
client = OptimizedAWSMCPClient(
    aws_access_key_id=aws_config.get("aws_access_key_id"),
    aws_secret_access_key=aws_config.get("aws_secret_access_key"),
    region_name=aws_config.get("region_name", "us-east-1")
)

# Connect to AWS MCP server
await client.connect()

# Use AWS services
lambda_functions = await client.list_lambda_functions()
s3_buckets = await client.list_s3_buckets()

# Clean up
await client.disconnect()
```

### Using with MCP Client Manager

```python
from src.mcp.mcp_client_manager import MCPClientManager
from config.settings import CONFIG

# Get AWS configuration
aws_config = CONFIG.get("mcp_aws", {})

# Create MCP client manager
manager = MCPClientManager()

# Add AWS MCP client
await manager.add_aws_client(
    server_id="aws",
    aws_access_key_id=aws_config.get("aws_access_key_id"),
    aws_secret_access_key=aws_config.get("aws_secret_access_key"),
    region_name=aws_config.get("region_name", "us-east-1")
)

# Get the client from manager
aws_client = manager.get_client("aws")

# Use AWS services
response = await aws_client.invoke_lambda(
    function_name="my-function",
    payload={"key": "value"}
)
```

## Key Services and Operations

### Lambda Operations

- `invoke_lambda`: Execute a Lambda function
- `list_lambda_functions`: List available functions

### S3 Operations

- `list_s3_buckets`: List all buckets
- `list_s3_objects`: List objects in a bucket
- `get_s3_object`: Retrieve an object from S3
- `put_s3_object`: Upload an object to S3

### SQS Operations

- `send_sqs_message`: Send a message to a queue
- `receive_sqs_messages`: Receive messages from a queue
- `delete_sqs_message`: Delete a message from a queue

### SNS Operations

- `publish_sns_message`: Publish a message to a topic
- `list_sns_topics`: List available topics

### Secrets Manager Operations

- `get_secret`: Retrieve a secret

### DynamoDB Operations

- `dynamodb_get_item`: Get an item from a table
- `dynamodb_put_item`: Put an item into a table

## Configuration

Configure AWS credentials in `.env` or via environment variables:

```
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_REGION=us-east-1
```

## Testing

A test script is provided to verify AWS MCP functionality:

```bash
python scripts/test_aws_mcp.py --bucket my-bucket --lambda my-function
```

## Error Handling

The client provides detailed error reporting and automatic retries for transient failures:

```python
try:
    result = await aws_client.get_s3_object(bucket="my-bucket", key="my-file.txt")
except AWSClientError as e:
    logger.error(f"AWS operation failed: {e}")
```
