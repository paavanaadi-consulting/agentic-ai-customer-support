# Confluent Kafka MCP Docker Integration Migration

## Overview
This document describes the migration from a non-existent Python package to using Confluent's official `mcp-confluent` server via Docker for Kafka MCP integration.

## Problem Statement
The original approach attempted to use `https://github.com/modelcontextprotocol/kafka-mcp.git` which:
- Does not exist (404 error)
- Was causing Docker build failures
- Left the system without a working Kafka MCP integration

## Solution: Docker-based Confluent MCP Server

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │  Main App       │◄──►│  mcp-kafka-wrapper (Port 8003) │ │
│  │  (Port 8000)    │    │  (Python)                      │ │
│  └─────────────────┘    └─────────────────┬───────────────┘ │
│                                           │                 │
│                         ┌─────────────────▼───────────────┐ │
│                         │  mcp-kafka (Port 8002)         │ │
│                         │  (Confluent MCP - Node.js)     │ │
│                         └─────────────────┬───────────────┘ │
│                                           │                 │
│                         ┌─────────────────▼───────────────┐ │
│                         │  Kafka Broker                  │ │
│                         │  (Port 9092)                   │ │
│                         └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Services Added/Modified

#### 1. mcp-kafka (New Service)
```yaml
mcp-kafka:
  image: node:18-alpine
  ports:
    - "8002:8002"
  environment:
    - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    - KAFKA_TOPIC_NAME=customer-support
    - KAFKA_GROUP_ID=ai-support-group
  command: >
    sh -c "
      npm install -g @confluentinc/mcp-confluent &&
      npx @confluentinc/mcp-confluent --transport stdio
    "
```

#### 2. mcp-kafka-wrapper (Modified Service)
```yaml
mcp-kafka-wrapper:
  build:
    context: .
    dockerfile: Dockerfile.mcp
  ports:
    - "8003:8003"
  environment:
    - EXTERNAL_KAFKA_MCP_HOST=mcp-kafka
    - EXTERNAL_KAFKA_MCP_PORT=8002
  depends_on:
    - kafka
    - mcp-kafka
```

### Code Changes

#### 1. requirements.txt
**Removed:**
```
kafka-mcp @ git+https://github.com/modelcontextprotocol/kafka-mcp.git
```

**Added:**
```
aiohttp>=3.8.0  # For HTTP communication with Confluent MCP server
```

**Added comment:**
```
# Note: Kafka MCP is handled via Docker using Confluent's mcp-confluent server (Node.js)
# See docker-compose.yml for the mcp-kafka-confluent service
```

#### 2. mcp/kafka_mcp_wrapper.py
**Key changes:**
- Updated `_setup_external_server()` to configure connection to Docker service
- Updated `_call_external_tool()` to use HTTP/aiohttp instead of stdio
- Added external host/port configuration from environment variables
- Maintained the same tool mapping for compatibility

#### 3. docker-compose.yml
**Port assignments:**
- mcp-kafka (Confluent): 8002
- mcp-kafka-wrapper (Python): 8003
- mcp-aws: 8004 (updated from 8003)

#### 4. Installation Scripts
**Updated scripts/install_external_mcp.sh:**
- Removed non-working kafka-mcp installation
- Added note about Docker-based approach
- Updated verification steps

### Benefits of This Approach

#### ✅ **Official Support**
- Uses Confluent's official MCP server
- Maintained by Confluent (Kafka experts)
- Regular updates and bug fixes

#### ✅ **Technology Separation**
- Node.js MCP server runs in its own container
- Python application communicates via HTTP
- Clean separation of concerns

#### ✅ **Docker-Native**
- Fully integrated with existing Docker Compose stack
- Automatic service discovery and networking
- Container orchestration handles lifecycle

#### ✅ **Scalability**
- Can scale MCP server independently
- HTTP communication allows for load balancing
- Can run multiple MCP server instances

#### ✅ **Fallback Strategy**
- BasicKafkaWrapper still available for fallback
- Uses kafka-python for direct Kafka operations
- Graceful degradation when external service unavailable

### Configuration

#### Environment Variables
```bash
# For Confluent MCP Server
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_NAME=customer-support
KAFKA_GROUP_ID=ai-support-group
KAFKA_AUTO_OFFSET_RESET=earliest

# For Python Wrapper
EXTERNAL_KAFKA_MCP_HOST=mcp-kafka
EXTERNAL_KAFKA_MCP_PORT=8002
```

#### Python Configuration
```python
from mcp.kafka_mcp_wrapper import KafkaMCPWrapper, ExternalKafkaMCPConfig

# Configure Kafka MCP
kafka_config = ExternalKafkaMCPConfig(
    bootstrap_servers="kafka:9092",
    topic_name="customer-support", 
    group_id="ai-support-group",
    fallback_to_custom=True  # Enable fallback to BasicKafkaWrapper
)

# Create wrapper (will connect to Docker service)
kafka_server = KafkaMCPWrapper(kafka_config)
await kafka_server.initialize()
```

### Tool Mapping (Unchanged)
The wrapper maintains the same tool mapping for backward compatibility:

| Internal Tool Name | Confluent Tool Name | Description |
|-------------------|-------------------|-------------|
| `publish_message` | `kafka_publish` | Publish messages |
| `consume_messages` | `kafka_consume` | Consume messages |
| `create_topic` | `kafka_create_topic` | Create topics |
| `delete_topic` | `kafka_delete_topic` | Delete topics |
| `list_topics` | `kafka_list_topics` | List topics |
| `get_topic_metadata` | `kafka_describe_topic` | Get topic details |
| `describe_cluster` | `kafka_describe_cluster` | Cluster info |
| `consumer_groups` | `kafka_consumer_groups` | Consumer groups |

### Usage Examples

#### Starting the Stack
```bash
# Start all services including Confluent MCP
docker-compose up -d

# Check service health
docker-compose ps
docker-compose logs mcp-kafka
docker-compose logs mcp-kafka-wrapper
```

#### Testing Integration
```python
# The same Python code works as before
result = await kafka_wrapper.call_tool('publish_message', {
    'topic': 'customer-queries',
    'message': {'customer_id': '123', 'query': 'Help with billing'},
    'key': 'customer-123'
})

# New Confluent-specific features
result = await kafka_wrapper.call_tool('describe_cluster', {})
```

### Migration Checklist

- [x] Remove non-existent package from requirements.txt
- [x] Add aiohttp dependency for HTTP communication
- [x] Update pyproject.toml dependencies
- [x] Modify docker-compose.yml to include Confluent MCP service
- [x] Update mcp/kafka_mcp_wrapper.py for HTTP communication
- [x] Update installation scripts
- [x] Update port assignments (AWS moved to 8004)
- [x] Update documentation
- [x] Add environment variable configuration
- [x] Test Docker build process
- [ ] Integration testing with actual Kafka cluster
- [ ] Performance testing vs. direct kafka-python
- [ ] Documentation for troubleshooting

### Troubleshooting

#### Service Not Starting
```bash
# Check Confluent MCP server logs
docker-compose logs mcp-kafka

# Check if Node.js dependencies installed correctly
docker-compose exec mcp-kafka npm list -g
```

#### Connection Issues
```bash
# Test HTTP connectivity
curl -X POST http://localhost:8002/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

#### Fallback Testing
```bash
# Stop Confluent service to test fallback
docker-compose stop mcp-kafka

# Check wrapper falls back to BasicKafkaWrapper
docker-compose logs mcp-kafka-wrapper
```

### Future Improvements

1. **Health Checks**: Add HTTP health checks for Confluent MCP service
2. **Metrics**: Expose Confluent MCP metrics via HTTP endpoints
3. **Security**: Add authentication between wrapper and Confluent service
4. **Load Balancing**: Support multiple Confluent MCP instances
5. **WebSocket**: Consider WebSocket for real-time communication

## Conclusion

This Docker-based approach provides a robust, officially-supported Kafka MCP integration that:
- Solves the non-existent package problem
- Uses proven, maintained software (Confluent's MCP server)
- Maintains backward compatibility
- Provides clear separation of concerns
- Enables future scaling and improvements

The migration ensures the system can build and deploy successfully while providing comprehensive Kafka functionality through Confluent's expertise.
