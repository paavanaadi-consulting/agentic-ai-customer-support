# A2A Module Local Testing Guide

This guide will help you test the A2A (Agent-to-Agent) module locally with MCP integration.

## Prerequisites

1. **Python 3.11+** installed
2. **Docker and Docker Compose** installed
3. **API Keys** for LLM providers (optional for basic testing)

## Quick Start (5 minutes)

### 1. Environment Setup

```bash
# Clone and navigate to the repository
cd agentic-ai-customer-support

# Copy the local testing environment
cp .env.local.example .env.local

# Edit .env.local with your settings (API keys are optional for basic testing)
nano .env.local
```

### 2. Start Infrastructure Services

```bash
# Start test database, Kafka, and MCP servers
docker-compose -f docker-compose.test.yml up -d

# Wait for services to be ready (about 30 seconds)
docker-compose -f docker-compose.test.yml logs -f
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
🚀 Starting A2A Module Local Testing
==================================================
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

This tests the complete A2A pipeline with MCP integration:

```bash
# Start all services
docker-compose -f docker-compose.test.yml up -d

# Run comprehensive tests
python scripts/test_a2a_local.py

# Run unit tests
pytest tests/mcp_servers/ -v

# Run integration tests
pytest tests/ -m integration -v
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

### Option 3: MCP Server Testing

Test MCP servers independently:

```bash
# Start only database and test MCP
docker-compose -f docker-compose.test.yml up postgres-test mcp-database-test -d

# Test MCP database operations
python -c "
import asyncio
from mcp.database_mcp_server import DatabaseMCPServer
from data_sources.rdbms_connector import RDBMSConnector

async def test_mcp():
    connector = RDBMSConnector()
    await connector.connect()
    server = DatabaseMCPServer(connector)
    await server.start()
    
    # Test query
    result = await server.call_tool('query_database', {
        'query': 'SELECT 1 as test',
        'params': []
    })
    print(f'MCP Result: {result}')
    
    await connector.disconnect()

asyncio.run(test_mcp())
"
```

## Manual Testing

### 1. Start Services Manually

```bash
# Terminal 1: Start infrastructure
docker-compose -f docker-compose.test.yml up postgres-test kafka-test redis-test

# Terminal 2: Start MCP Database Server
python scripts/start_mcp_servers.py --server database

# Terminal 3: Start MCP Kafka Server  
python scripts/start_mcp_servers.py --server kafka

# Terminal 4: Start Query Agent
python -c "
import asyncio
from scripts.test_a2a_local import TestQueryAgent

async def run():
    agent = TestQueryAgent('query-agent-1')
    await agent.start()
    print('Query agent running on port 8101')
    await asyncio.sleep(3600)  # Run for 1 hour

asyncio.run(run())
"

# Terminal 5: Start Knowledge Agent
python -c "
import asyncio
from scripts.test_a2a_local import TestKnowledgeAgent

async def run():
    agent = TestKnowledgeAgent('knowledge-agent-1')
    await agent.start()
    print('Knowledge agent running on port 8102')
    await asyncio.sleep(3600)

asyncio.run(run())
"

# Terminal 6: Start Response Agent
python -c "
import asyncio
from scripts.test_a2a_local import TestResponseAgent

async def run():
    agent = TestResponseAgent('response-agent-1')
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

# View MCP server logs
docker-compose -f docker-compose.test.yml logs mcp-database-test
docker-compose -f docker-compose.test.yml logs mcp-kafka-test

# View agent-specific logs
grep "query-agent" logs/a2a_test.log
grep "knowledge-agent" logs/a2a_test.log
grep "response-agent" logs/a2a_test.log
```

### 2. Health Checks

```bash
# Check service health
curl http://localhost:8001/health  # MCP Database Server
curl http://localhost:8002/health  # MCP Kafka Server

# Check database connection
docker exec -it $(docker-compose -f docker-compose.test.yml ps -q postgres-test) \
    psql -U admin -d customer_support_test -c "SELECT 1;"

# Check Kafka topics
docker exec -it $(docker-compose -f docker-compose.test.yml ps -q kafka-test) \
    /opt/bitnami/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092
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
# Run multiple queries simultaneously
python -c "
import asyncio
from scripts.test_a2a_local import A2ATestOrchestrator

async def load_test():
    orchestrator = A2ATestOrchestrator()
    await orchestrator.setup_agents()
    
    # Run 10 concurrent queries
    tasks = []
    for i in range(10):
        task = orchestrator.run_test_scenario(
            f'load_test_customer_{i}',
            f'Load test query number {i}'
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    print(f'Completed {len([r for r in results if r[\"success\"]])} out of {len(results)} tests')
    
    await orchestrator.shutdown()

asyncio.run(load_test())
"
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in `.env.local` if needed
2. **Database connection errors**: Ensure PostgreSQL is running and accessible
3. **Kafka connection errors**: Check if Kafka and Zookeeper are running
4. **Agent connection timeouts**: Increase timeouts in agent configuration

### Reset Everything

```bash
# Stop all services
docker-compose -f docker-compose.test.yml down -v

# Clean up logs
rm -rf logs/a2a_test.log

# Restart services
docker-compose -f docker-compose.test.yml up -d

# Wait and test again
sleep 30
python scripts/test_a2a_local.py
```

## Next Steps

After successful local testing:

1. **Production Deployment**: Use the main `docker-compose.yml`
2. **Scaling**: Add multiple instances of each agent type
3. **Monitoring**: Integrate with monitoring tools
4. **Performance Tuning**: Optimize based on load testing results

## Useful Commands

```bash
# Quick test (all-in-one)
make test-a2a-local  # If you add this to Makefile

# Docker cleanup
docker-compose -f docker-compose.test.yml down -v --remove-orphans

# View running processes
ps aux | grep python | grep agent

# Monitor resource usage
docker stats $(docker-compose -f docker-compose.test.yml ps -q)
```
