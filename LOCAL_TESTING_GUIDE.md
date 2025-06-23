# Testing the Repository Locally Without Docker

This guide will walk you through testing the agentic AI customer support system locally on your macOS machine without using Docker components.

## Quick Start (15 minutes)

### Step 1: Prerequisites Check

Make sure you have:
- **Python 3.11+** installed (`python3 --version`)
- **Git** installed
- **Internet connection** for package installation

### Step 2: Set Up the Environment

```bash
# Navigate to your repository
cd /Users/ashokasangapallar/Desktop/studyrepos/agentic-ai-customer-support

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### Step 3: Quick Configuration

```bash
# Copy the example environment file
cp .env.local.example .env.local

# The default settings work for local testing without Docker
# You can edit .env.local if you want to add API keys later
```

### Step 4: Run the Native Setup Script

```bash
# This will set up SQLite database, create test data, and configure everything
python scripts/setup_native.py
```

### Step 5: Run Local Tests

```bash
# Run the native test suite
python scripts/test_native.py

# Or run individual unit tests
python -m pytest tests/ -v
```

## What Happens During Local Testing

### 1. Database Layer
- Uses **SQLite** instead of PostgreSQL
- Creates a local `data/test.db` file
- Pre-populated with sample customers and knowledge articles

### 2. Message Queue Layer  
- Uses **in-memory queues** instead of Kafka
- Simulates message passing between agents
- No external services required

### 3. MCP (Model Context Protocol) Layer
- **MCP servers run as local Python processes**
- Database MCP server connects to SQLite
- Kafka MCP server uses in-memory simulation
- AWS MCP server uses mock implementations

### 4. A2A (Agent-to-Agent) Layer
- **Query Agent**: Processes incoming customer queries
- **Knowledge Agent**: Searches knowledge base and articles
- **Response Agent**: Generates appropriate responses
- All agents communicate via local message passing

## Testing Scenarios

### Scenario 1: Basic Query Processing
```bash
# Test a simple customer query
python -c "
import asyncio
import sys
sys.path.append('.')

from scripts.test_native import test_basic_query

asyncio.run(test_basic_query())
"
```

### Scenario 2: Knowledge Base Search
```bash
# Test knowledge article retrieval
python -c "
import asyncio
import sys
sys.path.append('.')

from scripts.test_native import test_knowledge_search

asyncio.run(test_knowledge_search())
"
```

### Scenario 3: Full A2A Pipeline
```bash
# Test complete agent interaction
python scripts/test_native.py --scenario full
```

## Troubleshooting

### Issue: Import Errors
**Solution**: Make sure you're in the virtual environment and all dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: SQLite Permission Errors
**Solution**: Ensure the data directory is writable:
```bash
mkdir -p data logs
chmod 755 data logs
```

### Issue: Port Already in Use
**Solution**: The native tests use high port numbers (8101-8104) that are usually free. If you get port errors:
```bash
# Check what's using the ports
lsof -i :8101
lsof -i :8102

# Kill processes if needed
kill -9 <PID>
```

### Issue: Missing API Keys
**Solution**: The system works without API keys for basic testing. To add them:
```bash
# Edit .env.local and add your keys
nano .env.local

# Add these lines:
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
```

## File Structure After Setup

```
agentic-ai-customer-support/
├── data/
│   ├── test.db           # SQLite database
│   └── schema.sql        # Database schema
├── logs/
│   └── native_test.log   # Test execution logs
├── scripts/
│   ├── setup_native.py   # Setup script
│   └── test_native.py    # Test runner
└── .env.local           # Local configuration
```

## Advanced Testing

### Individual Component Testing

**Test MCP Database Server:**
```bash
python -c "
import asyncio
from mcp.database_mcp_server import DatabaseMCPServer

async def test():
    server = DatabaseMCPServer()
    await server.start()
    print('Database MCP server started')
    await server.stop()

asyncio.run(test())
"
```

**Test Query Agent:**
```bash
python -c "
import asyncio
from a2a_protocol.base_a2a_agent import BaseA2AAgent

async def test():
    agent = BaseA2AAgent('test-agent')
    await agent.start()
    result = await agent.process_message({'type': 'query', 'data': 'test'})
    print(f'Agent result: {result}')
    await agent.stop()

asyncio.run(test())
"
```

### Performance Testing

```bash
# Run performance tests
python scripts/test_native.py --performance

# Run with verbose logging
python scripts/test_native.py --verbose

# Run specific test patterns
python -m pytest tests/ -k "test_mcp" -v
```

## What's Different from Docker Setup

| Component | Docker Version | Local Version |
|-----------|---------------|---------------|
| Database | PostgreSQL container | SQLite file |
| Message Queue | Kafka container | In-memory queues |
| Cache | Redis container | In-memory cache |
| MCP Servers | Separate containers | Local Python processes |
| Network | Docker network | localhost/127.0.0.1 |

## Next Steps

1. **Run the basic tests** to verify everything works
2. **Add your API keys** to .env.local for LLM integration
3. **Explore the test results** in `logs/native_test.log`
4. **Modify test scenarios** in `scripts/test_native.py`
5. **Add your own test cases** in the `tests/` directory

The local setup provides the same functionality as the Docker version but runs entirely on your local machine using lightweight alternatives to external services.
