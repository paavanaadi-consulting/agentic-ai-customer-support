# External Kafka MCP Integration

This document describes the integration with the external Kafka MCP server package, which replaces our custom Kafka MCP implementation with a more comprehensive, community-maintained solution.

## Overview

The Kafka MCP Wrapper (`mcp/kafka_mcp_wrapper.py`) provides a unified interface to the external [`pavanjava/kafka_mcp_server`](https://github.com/pavanjava/kafka_mcp_server) package, with automatic fallback to our custom implementation if the external package is not available.

## Architecture

```
KafkaMCPWrapper (our wrapper)
    ↓
├── External Kafka MCP Server (preferred)
│   ├── pavanjava/kafka_mcp_server
│   ├── Comprehensive tools and features
│   └── Installed via pip or uvx
└── Custom Kafka MCP Server (fallback)
    ├── mcp/kafka_mcp_server.py
    ├── Basic tools
    └── Always available
```

## External Package Features

The external `pavanjava/kafka_mcp_server` package provides:

### Tools Available
- **kafka-publish**: Publish messages to topics
- **kafka-consume**: Consume messages from topics  
- **create-topic**: Create new Kafka topics
- **delete-topic**: Delete existing topics
- **list-topics**: List all available topics
- **topic-config**: Get/update topic configurations
- **cluster-health**: Check cluster health status
- **cluster-metadata**: Get cluster metadata information

### Advantages over Custom Implementation
- ✅ **Async Support**: Built with aiokafka for better performance
- ✅ **Comprehensive Features**: Full topic and cluster management
- ✅ **Better Error Handling**: Robust error handling and logging
- ✅ **Configuration Management**: Uses Pydantic for settings
- ✅ **Modern MCP Patterns**: Follows latest MCP server patterns
- ✅ **Community Maintained**: Actively maintained external package

## Configuration

### Environment Variables

Set these environment variables for the external Kafka server:

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
TOPIC_NAME=your-topic-name
IS_TOPIC_READ_FROM_BEGINNING=False
DEFAULT_GROUP_ID_FOR_CONSUMER=kafka-mcp-group
```

### Python Configuration

```python
from mcp.kafka_mcp_wrapper import KafkaMCPWrapper, ExternalKafkaMCPConfig

# Configure Kafka MCP
kafka_config = ExternalKafkaMCPConfig(
    bootstrap_servers="localhost:9092",
    topic_name="customer-support", 
    group_id="ai-support-group",
    use_uvx=True,  # Use uvx for package management
    fallback_to_custom=True  # Enable fallback to custom server
)

# Create wrapper
kafka_server = KafkaMCPWrapper(kafka_config)

# Initialize (checks external availability, sets up fallback if needed)
await kafka_server.initialize()
```

## Installation

### Option 1: Via pip (Automatic)

The wrapper automatically attempts to install the external package:

```bash
pip install git+https://github.com/pavanjava/kafka_mcp_server.git
```

### Option 2: Via uvx (Recommended)

```bash
uvx install git+https://github.com/pavanjava/kafka_mcp_server.git
```

### Option 3: Via requirements.txt

Already included in our `requirements.txt`:

```
kafka-mcp-server @ git+https://github.com/pavanjava/kafka_mcp_server.git
```

## Usage Examples

### Basic Usage

```python
# Initialize wrapper
kafka_wrapper = KafkaMCPWrapper(kafka_config)
await kafka_wrapper.initialize()

# Publish message (external server)
result = await kafka_wrapper.call_tool('publish_message', {
    'topic': 'customer-queries',
    'message': {'customer_id': '123', 'query': 'Help with billing'},
    'key': 'customer-123'
})

# Create topic (external server feature)
result = await kafka_wrapper.call_tool('create_topic', {
    'topic_name': 'new-topic',
    'num_partitions': 3,
    'replication_factor': 2
})

# Check cluster health (external server feature)
result = await kafka_wrapper.call_tool('cluster_health', {})
```

### Integration in Main Application

The main application automatically uses the wrapper:

```python
# In main.py
kafka_cfg = CONFIG.get('mcp_kafka', {})
if kafka_cfg:
    kafka_config = ExternalKafkaMCPConfig(
        bootstrap_servers=kafka_cfg.get('bootstrap_servers', 'localhost:9092'),
        topic_name=kafka_cfg.get('topic_name', 'customer-support'),
        group_id=kafka_cfg.get('group_id', 'ai-support-group')
    )
    self.mcp_services['kafka'] = KafkaMCPWrapper(kafka_config)
```

## Fallback Behavior

### When External Package is Not Available

1. **Detection**: Wrapper checks if external package can be installed/imported
2. **Fallback**: Automatically falls back to custom `KafkaMCPServer`
3. **Limited Features**: Only basic tools available in fallback mode
4. **Transparent**: Application code doesn't need to change

### Available Tools in Fallback Mode

- `publish_message`: Basic message publishing
- `consume_messages`: Basic message consumption
- `get_topic_metadata`: Basic topic information
- `list_topics`: List available topics

## Tool Name Mapping

The wrapper maps our internal tool names to external server tool names:

| Internal Tool Name | External Tool Name | Description |
|-------------------|-------------------|-------------|
| `publish_message` | `kafka-publish` | Publish messages |
| `consume_messages` | `kafka-consume` | Consume messages |
| `create_topic` | `create-topic` | Create topics |
| `delete_topic` | `delete-topic` | Delete topics |
| `list_topics` | `list-topics` | List topics |
| `get_topic_metadata` | `cluster-metadata` | Get metadata |
| `get_topic_config` | `topic-config` | Topic config |
| `cluster_health` | `cluster-health` | Cluster health |

## Docker Integration

The wrapper includes Docker support:

```python
# In docker-compose.yml
command: ["python", "-c", "from mcp.kafka_mcp_wrapper import KafkaMCPWrapper, ExternalKafkaMCPConfig; import asyncio; config = ExternalKafkaMCPConfig(bootstrap_servers='kafka:9092'); asyncio.run(KafkaMCPWrapper(config).start_as_server())"]
```

## Testing

Run tests specific to the Kafka wrapper:

```bash
pytest tests/mcp_servers/test_kafka_mcp.py -v
```

## Troubleshooting

### External Package Installation Issues

1. **Check uvx**: Ensure uvx is installed: `uvx --help`
2. **Manual Install**: Try `pip install git+https://github.com/pavanjava/kafka_mcp_server.git`
3. **Fallback Mode**: Set `fallback_to_custom=True` in config

### Connection Issues

1. **Check Kafka**: Ensure Kafka broker is running
2. **Network**: Verify bootstrap_servers address
3. **Permissions**: Check Kafka topic permissions

### Tool Availability

```python
# Check which tools are available
tools = kafka_wrapper.get_available_tools()
print(f"Available tools: {tools}")

# Check configuration
config_info = kafka_wrapper.get_config_info()
print(f"External available: {config_info['external_available']}")
print(f"Using fallback: {config_info['using_custom_fallback']}")
```

## Migration from Custom Server

### Before (Custom Server)
```python
from mcp.kafka_mcp_server import KafkaMCPServer

kafka_server = KafkaMCPServer("localhost:9092")
await kafka_server.start()
```

### After (External Wrapper)
```python
from mcp.kafka_mcp_wrapper import KafkaMCPWrapper, ExternalKafkaMCPConfig

kafka_config = ExternalKafkaMCPConfig(
    bootstrap_servers="localhost:9092",
    topic_name="default-topic",
    group_id="default-group"
)
kafka_wrapper = KafkaMCPWrapper(kafka_config)
await kafka_wrapper.initialize()
```

### Breaking Changes

1. **Tool Names**: Some tool names changed (see mapping table)
2. **Configuration**: Now requires `ExternalKafkaMCPConfig`
3. **Initialization**: Use `initialize()` instead of `start()`
4. **New Features**: Many new tools available with external server

## Future Improvements

- **Health Monitoring**: Enhanced cluster monitoring capabilities
- **Schema Registry**: Support for Confluent Schema Registry
- **Security**: Enhanced security features (SASL, SSL)
- **Metrics**: Better metrics and observability
- **Stream Processing**: Kafka Streams integration

## References

- [External Kafka MCP Server](https://github.com/pavanjava/kafka_mcp_server)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
