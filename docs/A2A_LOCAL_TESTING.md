# A2A Module Local Testing Guide

This guide will help you test the A2A (Agent-to-Agent) module locally with external MCP integration.

## Prerequisites

1. **Python 3.11+** installed
2. **Docker and Docker Compose** installed
3. **uvx** installed for external MCP packages
4. **API Keys** for LLM providers (optional for basic testing)
5. **AWS credentials** configured (for AWS MCP testing)

## Quick Start (5 minutes)

### 1. Environment Setup

```bash
# Clone and navigate to the repository
cd agentic-ai-customer-support

# Install external MCP packages
./scripts/install_external_mcp.sh

# Copy the local testing environment
cp .env.local.example .env.local

# Copy MCP configuration
cp config/aws_mcp.env.example config/aws_mcp.env

# Edit .env.local with your settings (API keys are optional for basic testing)
nano .env.local

# Configure AWS MCP if testing AWS functionality
nano config/aws_mcp.env
```

### 2. Start Infrastructure Services

```bash
# Start test database, Kafka, and infrastructure
docker-compose -f docker-compose.test.yml up -d

# Wait for services to be ready (about 30 seconds)
docker-compose -f docker-compose.test.yml logs -f

# Verify external MCP packages are available
uvx list | grep -E "(postgres-mcp|kafka-mcp|awslabs)"
```

### 3. Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Run A2A Tests

```bash
# Run the A2A local test script
python scripts/test_a2a_local.py
```

You should see output like:
```
🚀 Starting A2A Module Local Testing with External MCP Integration
==================================================
Initializing external MCP wrappers...
✅ PostgreSQL MCP Wrapper initialized
✅ Kafka MCP Wrapper initialized  
✅ AWS MCP Wrapper initialized

Setting up A2A test agents...
query agent started on port 8101
knowledge agent started on port 8102
response agent started on port 8103

📋 Test Scenario 1: How do I reset my password?
------------------------------
✅ Test passed!
   Processed queries: 1
   Analyzed queries: 1
   Generated responses: 1
   Latest response: To reset your password, please visit our login page and click 'Forgot Password'...
```

## Detailed Testing Options

### Option 1: Full Stack Testing (Recommended)

This tests the complete A2A pipeline with external MCP integration:

```bash
# Start all services
docker-compose -f docker-compose.test.yml up -d

# Run comprehensive tests with external MCP
python scripts/test_a2a_local.py --use-external-mcp

# Run MCP wrapper tests
pytest tests/mcp_servers/ -v

# Run integration tests
pytest tests/ -m integration -v

# Test external MCP packages individually
python scripts/test_external_mcp.py --postgres
python scripts/test_external_mcp.py --kafka  
python scripts/test_external_mcp.py --aws
```

### Option 2: Individual Agent Testing

Test individual agents in isolation:

```bash
# Test Query Agent only
python -c "
import asyncio
from scripts.test_a2a_local import TestQueryAgent
async def test():
    agent = TestQueryAgent('test-query-1')
    await agent.start()
    result = await agent.process_customer_query('Test query', 'test_customer')
    print(f'Result: {result}')
    await agent.stop()
asyncio.run(test())
"
```

### Option 3: MCP Wrapper Testing

Test external MCP wrappers independently:

```bash
# Start only database and test PostgreSQL MCP wrapper
docker-compose -f docker-compose.test.yml up postgres-test -d

# Test PostgreSQL MCP wrapper
python -c "
import asyncio
from mcp.postgres_mcp_wrapper import PostgresMCPWrapper

async def test_postgres_mcp():
    wrapper = PostgresMCPWrapper('postgresql://admin:password@localhost:5433/customer_support_test')
    await wrapper.initialize()
    
    # Test query via external postgres-mcp
    result = await wrapper.call_tool('query', {
        'sql': 'SELECT 1 as test',
        'params': []
    })
    print(f'PostgreSQL MCP Result: {result}')
    
    await wrapper.cleanup()

asyncio.run(test_postgres_mcp())
"

# Test Kafka MCP wrapper
python -c "
import asyncio
from mcp.kafka_mcp_wrapper import KafkaMCPWrapper, ExternalKafkaMCPConfig

async def test_kafka_mcp():
    config = ExternalKafkaMCPConfig(
        bootstrap_servers='localhost:9093',
        topic_name='test-topic',
        group_id='test-group'
    )
    wrapper = KafkaMCPWrapper(config)
    await wrapper.initialize()
    
    # Test topic listing via external kafka-mcp  
    result = await wrapper.call_tool('list-topics', {})
    print(f'Kafka MCP Result: {result}')
    
    await wrapper.cleanup()

asyncio.run(test_kafka_mcp())
"

# Test AWS MCP wrapper (requires AWS credentials)
python -c "
import asyncio
from mcp.aws_mcp_wrapper import AWSMCPWrapper, ExternalMCPConfig

async def test_aws_mcp():
    config = ExternalMCPConfig(
        aws_profile='default',
        aws_region='us-east-1'
    )
    wrapper = AWSMCPWrapper(config)
    await wrapper.initialize()
    
    # Test AWS identity via external AWS MCP
    result = await wrapper.call_tool('get_caller_identity', {})
    print(f'AWS MCP Result: {result}')
    
    await wrapper.cleanup()

asyncio.run(test_aws_mcp())
"
```

## Manual Testing

### 1. Start Services Manually

```bash
# Terminal 1: Start infrastructure
docker-compose -f docker-compose.test.yml up postgres-test kafka-test redis-test

# Terminal 2: Start internal Database MCP Server (if needed)
python scripts/start_mcp_servers.py --server database

# Terminal 3: Test external MCP wrappers
python -c "
import asyncio
from mcp.postgres_mcp_wrapper import PostgresMCPWrapper
from mcp.kafka_mcp_wrapper import KafkaMCPWrapper, ExternalKafkaMCPConfig
from mcp.aws_mcp_wrapper import AWSMCPWrapper, ExternalMCPConfig

async def test_wrappers():
    # Test PostgreSQL wrapper
    db_wrapper = PostgresMCPWrapper('postgresql://admin:password@localhost:5433/customer_support_test')
    await db_wrapper.initialize()
    print('PostgreSQL MCP Wrapper ready')
    
    # Test Kafka wrapper
    kafka_config = ExternalKafkaMCPConfig(
        bootstrap_servers='localhost:9093',
        topic_name='test-topic'
    )
    kafka_wrapper = KafkaMCPWrapper(kafka_config)
    await kafka_wrapper.initialize()
    print('Kafka MCP Wrapper ready')
    
    # Test AWS wrapper (optional)
    try:
        aws_config = ExternalMCPConfig(aws_profile='default', aws_region='us-east-1')
        aws_wrapper = AWSMCPWrapper(aws_config)
        await aws_wrapper.initialize()
        print('AWS MCP Wrapper ready')
    except Exception as e:
        print(f'AWS MCP Wrapper not available: {e}')
    
    await asyncio.sleep(3600)  # Keep running

asyncio.run(test_wrappers())
"

# Terminal 4: Start Query Agent
python -c "
import asyncio
from a2a_protocol.a2a_query_agent import A2AQueryAgent

async def run():
    agent = A2AQueryAgent('query-agent-1')
    await agent.start()
    print('Query agent running on port 8101')
    await asyncio.sleep(3600)  # Run for 1 hour

asyncio.run(run())
"

# Terminal 5: Start Knowledge Agent
python -c "
import asyncio
from a2a_protocol.a2a_knowledge_agent import A2AKnowledgeAgent

async def run():
    agent = A2AKnowledgeAgent('knowledge-agent-1')
    await agent.start()
    print('Knowledge agent running on port 8102')
    await asyncio.sleep(3600)

asyncio.run(run())
"

# Terminal 6: Start Response Agent
python -c "
import asyncio
from a2a_protocol.a2a_response_agent import A2AResponseAgent

async def run():
    agent = A2AResponseAgent('response-agent-1')
    await agent.start()
    print('Response agent running on port 8103')
    await asyncio.sleep(3600)

asyncio.run(run())
"
```

### 2. Send Test Messages

```bash
# Send a test query via WebSocket
python -c "
import asyncio
import websockets
import json

async def send_test():
    uri = 'ws://localhost:8101'
    async with websockets.connect(uri) as websocket:
        message = {
            'message_id': 'test-1',
            'sender_id': 'test-client',
            'receiver_id': 'query-agent-1',
            'message_type': 'customer_query',
            'payload': {
                'query': 'How do I reset my password?',
                'customer_id': 'test_customer_12345'
            },
            'timestamp': '2025-06-23T10:00:00'
        }
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        print(f'Response: {response}')

asyncio.run(send_test())
"
```

## Monitoring and Debugging

### 1. Check Logs

```bash
# View all logs
tail -f logs/a2a_test.log

# View infrastructure logs
docker-compose -f docker-compose.test.yml logs postgres-test
docker-compose -f docker-compose.test.yml logs kafka-test

# View agent-specific logs
grep "query-agent" logs/a2a_test.log
grep "knowledge-agent" logs/a2a_test.log  
grep "response-agent" logs/a2a_test.log

# View MCP wrapper logs
grep "PostgresMCPWrapper" logs/a2a_test.log
grep "KafkaMCPWrapper" logs/a2a_test.log
grep "AWSMCPWrapper" logs/a2a_test.log
```

### 2. Health Checks

```bash
# Check external MCP packages
uvx list | grep -E "(postgres-mcp|kafka-mcp|awslabs)"

# Test external MCP connectivity
python -c "
import asyncio
from mcp.postgres_mcp_wrapper import PostgresMCPWrapper

async def health_check():
    try:
        wrapper = PostgresMCPWrapper('postgresql://admin:password@localhost:5433/customer_support_test')
        await wrapper.initialize()
        print('✅ PostgreSQL MCP Wrapper: OK')
        await wrapper.cleanup()
    except Exception as e:
        print(f'❌ PostgreSQL MCP Wrapper: {e}')

asyncio.run(health_check())
"

# Check database connection
docker exec -it $(docker-compose -f docker-compose.test.yml ps -q postgres-test) \
    psql -U admin -d customer_support_test -c "SELECT 1;"

# Check Kafka topics
docker exec -it $(docker-compose -f docker-compose.test.yml ps -q kafka-test) \
    /opt/bitnami/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# Check AWS credentials (if configured)
aws sts get-caller-identity
```

### 3. Debug Agent Communication

```bash
# Monitor WebSocket traffic (install websocat first)
# brew install websocat  # On macOS

# Connect to query agent
websocat ws://localhost:8101

# Connect to knowledge agent
websocat ws://localhost:8102

# Connect to response agent
websocat ws://localhost:8103
```

## Performance Testing

### Load Testing

```bash
# Run multiple queries simultaneously with external MCP
python -c "
import asyncio
from scripts.test_a2a_local import A2ATestOrchestrator

async def load_test():
    orchestrator = A2ATestOrchestrator(use_external_mcp=True)
    await orchestrator.setup_agents()
    
    # Run 10 concurrent queries
    tasks = []
    for i in range(10):
        task = orchestrator.run_test_scenario(
            f'load_test_customer_{i}',
            f'Load test query number {i} with external MCP'
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    success_count = len([r for r in results if r['success']])
    print(f'Completed {success_count} out of {len(results)} tests with external MCP')
    
    await orchestrator.shutdown()

asyncio.run(load_test())
"

# Test external MCP performance
python scripts/benchmark_external_mcp.py --postgres --kafka --aws
```

## Troubleshooting

### Common Issues

1. **External MCP package not found**: Run `./scripts/install_external_mcp.sh` to install packages
2. **uvx command not found**: Install uvx with `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. **PostgreSQL connection errors**: Ensure PostgreSQL is running and accessible
4. **Kafka connection errors**: Check if Kafka and Zookeeper are running
5. **AWS credentials not configured**: Run `aws configure` or set environment variables
6. **Agent connection timeouts**: Increase timeouts in agent configuration
7. **MCP wrapper initialization failures**: Check external package availability with `uvx list`

### Reset Everything

```bash
# Stop all services
docker-compose -f docker-compose.test.yml down -v

# Clean up logs
rm -rf logs/a2a_test.log

# Reinstall external MCP packages
./scripts/install_external_mcp.sh

# Restart services
docker-compose -f docker-compose.test.yml up -d

# Wait and test again
sleep 30
python scripts/test_a2a_local.py --use-external-mcp
```

## Next Steps

After successful local testing:

1. **Production Deployment**: Use the main `docker-compose.yml` with external MCP wrappers
2. **Scaling**: Add multiple instances of each agent type
3. **External MCP Monitoring**: Monitor external package health and performance
4. **Performance Tuning**: Optimize based on load testing results with external MCP packages

## Useful Commands

```bash
# Quick test (all-in-one)
make test-a2a-local  # If you add this to Makefile

# Test external MCP packages
uvx list | grep -E "(postgres-mcp|kafka-mcp|awslabs)"

# Update external MCP packages
uvx upgrade postgres-mcp
uvx upgrade kafka-mcp
uvx upgrade awslabs.lambda-tool-mcp-server

# Docker cleanup
docker-compose -f docker-compose.test.yml down -v --remove-orphans

# View running processes
ps aux | grep python | grep agent

# Monitor resource usage
docker stats $(docker-compose -f docker-compose.test.yml ps -q)

# Test MCP wrapper connectivity
python scripts/test_external_mcp.py --all --verbose
```
