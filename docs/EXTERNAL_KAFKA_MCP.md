# Official MCP Kafka Integration

This document describes the integration with the official Kafka MCP server from the Model Context Protocol organization, which provides a comprehensive, officially-maintained Kafka integration.

## Overview

The Kafka MCP Wrapper (`mcp/kafka_mcp_wrapper.py`) provides a unified interface to the official [`modelcontextprotocol/kafka-mcp`](https://github.com/modelcontextprotocol/kafka-mcp) package, with automatic fallback to our custom implementation if the official package is not available.

## Architecture

```
KafkaMCPWrapper (our wrapper)
    ↓
├── Official MCP Kafka Server (preferred)
│   ├── modelcontextprotocol/kafka-mcp
│   ├── Official MCP implementation
│   ├── Comprehensive tools and features
│   └── Installed via pip or uvx
└── Basic Kafka Wrapper (fallback)
    ├── BasicKafkaWrapper class
    ├── Uses kafka-python directly
    └── Always available with kafka-python installed
```

## Official Package Features

The official `modelcontextprotocol/kafka-mcp` package provides:

### Tools Available
- **kafka_publish**: Publish messages to Kafka topics
- **kafka_consume**: Consume messages from topics  
- **kafka_list_topics**: List all available topics
- **kafka_describe_topic**: Get detailed topic information
- **kafka_create_topic**: Create new Kafka topics (if supported)
- **kafka_delete_topic**: Delete existing topics (if supported)
- **kafka_describe_cluster**: Get cluster information
- **kafka_consumer_groups**: Manage consumer groups

### Advantages over Custom Implementation
- ✅ **Official Support**: Maintained by the MCP organization
- ✅ **Standard Compliance**: Follows official MCP specifications
- ✅ **Latest Features**: Access to newest MCP capabilities
- ✅ **Community Support**: Backed by the MCP community
- ✅ **Better Integration**: Seamless integration with MCP ecosystem
- ✅ **Comprehensive Features**: Full Kafka management capabilities

## Configuration

### Environment Variables

Set these environment variables for the official Kafka server:

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_NAME=customer-support
KAFKA_GROUP_ID=ai-support-group
KAFKA_AUTO_OFFSET_RESET=earliest
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

The wrapper automatically attempts to install the official package:

```bash
pip install git+https://github.com/modelcontextprotocol/kafka-mcp.git
```

### Option 2: Via uvx (Recommended)

```bash
uvx install git+https://github.com/modelcontextprotocol/kafka-mcp.git
```

### Option 3: Via requirements.txt

Already included in our `requirements.txt`:
```
kafka-mcp @ git+https://github.com/modelcontextprotocol/kafka-mcp.git
```

## Usage Examples

### Basic Usage

```python
# Initialize wrapper
kafka_wrapper = KafkaMCPWrapper(kafka_config)
await kafka_wrapper.initialize()

# Publish message (official server)
result = await kafka_wrapper.call_tool('publish_message', {
    'topic': 'customer-queries',
    'message': {'customer_id': '123', 'query': 'Help with billing'},
    'key': 'customer-123'
})

# Create topic (official server feature)
result = await kafka_wrapper.call_tool('create_topic', {
    'topic_name': 'new-topic',
    'partitions': 3,
    'replication_factor': 1,
    'config': {}
})

# Describe cluster (official server feature)
result = await kafka_wrapper.call_tool('describe_cluster', {})
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

### When Official Package is Not Available

1. **Detection**: Wrapper checks if official package can be installed/imported
2. **Fallback**: Automatically falls back to `BasicKafkaWrapper` using kafka-python
3. **Limited Features**: Only basic tools available in fallback mode
4. **Transparent**: Application code doesn't need to change

### Available Tools in Fallback Mode

- `publish_message`: Basic message publishing
- `consume_messages`: Basic message consumption
- `get_topic_metadata`: Basic topic information
- `list_topics`: List available topics

## Tool Name Mapping

The wrapper maps our internal tool names to official MCP tool names:

| Internal Tool Name | Official Tool Name | Description |
|-------------------|-------------------|-------------|
| `publish_message` | `kafka_publish` | Publish messages |
| `consume_messages` | `kafka_consume` | Consume messages |
| `create_topic` | `kafka_create_topic` | Create topics |
| `delete_topic` | `kafka_delete_topic` | Delete topics |
| `list_topics` | `kafka_list_topics` | List topics |
| `get_topic_metadata` | `kafka_describe_topic` | Get topic details |
| `describe_cluster` | `kafka_describe_cluster` | Cluster info |
| `consumer_groups` | `kafka_consumer_groups` | Consumer groups |

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

### Official Package Installation Issues

1. **Check uvx**: Ensure uvx is installed: `uvx --help`
2. **Manual Install**: Try `pip install git+https://github.com/modelcontextprotocol/kafka-mcp.git`
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
print(f"Official available: {config_info['external_available']}")
print(f"Using fallback: {config_info['using_custom_fallback']}")
```

## Migration from Custom Server

### Before (Basic Kafka Operations)
```python
from kafka import KafkaProducer, KafkaConsumer

producer = KafkaProducer(bootstrap_servers="localhost:9092")
consumer = KafkaConsumer("topic-name", bootstrap_servers="localhost:9092")
```

### After (Official Wrapper)
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
4. **New Features**: Many new tools available with official server

## Future Improvements

- **Health Monitoring**: Enhanced cluster monitoring capabilities
- **Schema Registry**: Support for Confluent Schema Registry
- **Security**: Enhanced security features (SASL, SSL)
- **Metrics**: Better metrics and observability
- **Stream Processing**: Kafka Streams integration

## References

- [Official MCP Kafka Server](https://github.com/modelcontextprotocol/kafka-mcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
