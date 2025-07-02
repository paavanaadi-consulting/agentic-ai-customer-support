# External AWS MCP Server Integration

## Overview

This document explains how to integrate official external AWS MCP server packages with the Agentic AI Customer Support System. These official packages provide optimal performance and reliability whe### Performance Considerations

Using external AWS MCP servers can improve performance by:

1. Reducing latency through optimized connections
2. Providing service-specific optimizations
3. Enabling advanced features not available through generic SDK usage

However, there is overhead in starting and managing external MCP server processes. For very lightweight operations, direct SDK usage might be more efficient.

## Complete Example

A complete example is provided in `examples/external_aws_mcp_example.py`. This example demonstrates:

1. Using AWS Lambda Tool MCP Server
2. Using AWS Messaging MCP Server for SNS and SQS
3. Using all external MCP servers together through the client manager

To run the example:

```bash
# Run all examples
python examples/external_aws_mcp_example.py

# Run only the Lambda example
python examples/external_aws_mcp_example.py --example lambda

# Run only the messaging example
python examples/external_aws_mcp_example.py --example messaging
```

For more detailed examples, see the test script at `scripts/test_external_aws_mcp.py`.ting with AWS services through the Model Context Protocol (MCP).

By using the official external AWS MCP servers, the system gains several benefits:

- Direct access to AWS services through optimized channels
- Improved security through specialized client implementations
- Enhanced functionality specific to each AWS service
- Reduced latency for common operations
- Automatic retry and error handling tailored to each service

## Supported External AWS MCP Servers

The system supports the following official AWS MCP servers:

1. **AWS Lambda Tool MCP Server** - For Lambda function execution
   - Optimized for function invocation and response handling
   - Support for synchronous and asynchronous invocations
   - Advanced payload processing and error reporting

2. **Amazon SNS/SQS MCP Server** - For messaging and queue operations
   - Unified interface for SNS topic publishing
   - SQS message sending, receiving, and deletion
   - Support for message attributes and batch operations

3. **Amazon MQ MCP Server** - For message broker operations
   - Connect to Amazon MQ brokers
   - Send and receive messages from queues and topics
   - Support for ActiveMQ and RabbitMQ broker types

## Integration Configuration

### Prerequisites

- Installed AWS SDK for Python (Boto3)
- AWS credentials configured in environment variables or configuration files
- Python 3.8 or higher

### Package Installation

The system will automatically try to install these packages when needed, but you can pre-install them:

```bash
# Install AWS Lambda Tool MCP Server
pip install awslabs-lambda-tool-mcp-server

# Install Amazon SNS/SQS MCP Server
pip install aws-messaging-mcp-server

# Install Amazon MQ MCP Server
pip install amazon-mq-mcp-server
```

### Configuration Options

When initializing the AWS MCP client, you can specify which external servers to use:

```python
from src.mcp.mcp_client_manager import MCPClientManager

# Initialize client manager
manager = MCPClientManager()

# Add AWS client with external MCP servers
await manager.add_aws_client(
    server_id="aws",
    aws_access_key_id="YOUR_ACCESS_KEY",
    aws_secret_access_key="YOUR_SECRET_KEY",
    region_name="us-west-2",
    use_external_mcp_servers=True,
    service_types=["lambda", "sns", "sqs", "mq"]
)
```

## Architecture

The integration follows this architecture:

1. **Service Discovery**: The system detects which official AWS MCP server packages are available
2. **Dynamic Server Management**: External MCP servers are started as needed and managed via subprocesses
3. **Connection Management**: Connections to external servers are maintained efficiently
4. **Fallback Mechanism**: If an external server is unavailable, the system falls back to direct SDK usage

## Port Configuration

By default, the external MCP servers use these ports:
- Lambda Tool MCP Server: 8766
- Messaging (SNS/SQS) MCP Server: 8767
- MQ MCP Server: 8768

## Usage Examples

### Using Lambda Tool MCP Server

```python
# Get AWS client from manager
aws_client = manager.get_client("aws")

# Invoke Lambda function (uses Lambda Tool MCP if available)
response = await aws_client.invoke_lambda(
    function_name="my-function",
    payload={"key": "value"},
    invocation_type="RequestResponse"
)

# You can also pass additional parameters specific to Lambda
response = await aws_client.invoke_lambda(
    function_name="my-function",
    payload={"key": "value"},
    invocation_type="Event",  # Asynchronous invocation
    client_context={"custom": "context"},
    qualifier="prod"  # Version or alias
)
```

### Using Messaging MCP Server for SNS

```python
# Get AWS client from manager
aws_client = manager.get_client("aws")

# Publish SNS message (uses Messaging MCP if available)
response = await aws_client.publish_sns_message(
    topic_arn="arn:aws:sns:us-west-2:123456789012:my-topic",
    message="Hello from MCP!",
    subject="Test Message"
)

# You can also publish structured messages
response = await aws_client.publish_sns_message(
    topic_arn="arn:aws:sns:us-west-2:123456789012:my-topic",
    message=json.dumps({
        "default": "Default message",
        "email": "Email message",
        "sms": "SMS message"
    }),
    subject="Structured Message",
    message_structure="json",
    message_attributes={
        "priority": "high",
        "timestamp": str(datetime.now().isoformat())
    }
)
```

### Using Messaging MCP Server for SQS

```python
# Get AWS client from manager
aws_client = manager.get_client("aws")

# Send SQS message (uses Messaging MCP if available)
response = await aws_client.send_sqs_message(
    queue_url="https://sqs.us-west-2.amazonaws.com/123456789012/my-queue",
    message_body="Hello from MCP!",
    message_attributes={"attr1": "value1"}
)
```

### Using MQ MCP Server

```python
# Get AWS client from manager
aws_client = manager.get_client("aws")

# Send message to Amazon MQ broker (uses MQ MCP if available)
response = await aws_client.send_mq_message(
    broker_id="b-12345678-1234-1234-1234-123456789012",
    destination_type="queue",
    destination_name="my-queue",
    message_body="Hello from MQ MCP!"
)
```

## Advanced Configuration

### Custom External Server Configuration

You can customize the external MCP server configuration:

```python
# Custom external MCP server configuration
mcp_servers = {
    "lambda": {
        "package": "awslabs.lambda-tool-mcp-server",
        "port": 9000  # Custom port
    },
    "messaging": {
        "package": "aws.messaging-mcp-server",
        "port": 9001  # Custom port
    }
}

# Add AWS client with custom MCP server configuration
await manager.add_aws_client(
    server_id="aws-custom",
    use_external_mcp_servers=True,
    mcp_servers=mcp_servers
)
```

## Troubleshooting

### Connection Issues

If you're experiencing connection issues with external MCP servers:

1. Check if the required packages are installed correctly
2. Verify port availability (use `netstat -an | grep PORT` to check if the port is in use)
3. Check logs for error messages (default log level is INFO)
4. Ensure AWS credentials are correctly configured

### Package Installation Issues

If automatic package installation fails:

1. Install the packages manually using the provided script:
   ```bash
   ./scripts/install_aws_mcp_packages.sh --all
   ```

2. Or install individual packages:
   ```bash
   ./scripts/install_aws_mcp_packages.sh --lambda
   ./scripts/install_aws_mcp_packages.sh --messaging
   ./scripts/install_aws_mcp_packages.sh --mq
   ```

3. Check for Python version compatibility (Python 3.8+ recommended)
4. Check network connectivity to PyPI or your private package repository

### Testing the Integration

You can test the external AWS MCP server integration using the provided test script:

```bash
./scripts/run_external_aws_mcp_test.sh --test all
```

Or test specific services:

```bash
./scripts/run_external_aws_mcp_test.sh --test lambda --lambda my-function
./scripts/run_external_aws_mcp_test.sh --test messaging --topic my-topic-arn --queue my-queue-url
./scripts/run_external_aws_mcp_test.sh --test mq --broker my-broker-id
```

## Performance Considerations

Using external AWS MCP servers can improve performance by:

1. Reducing latency through optimized connections
2. Providing service-specific optimizations
3. Enabling advanced features not available through generic SDK usage

However, there is overhead in starting and managing external MCP server processes. For very lightweight operations, direct SDK usage might be more efficient.
