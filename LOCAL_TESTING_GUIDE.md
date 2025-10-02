# 🧪 **Local Testing Guide for Agentic AI Customer Support**

This comprehensive guide will help you set up, configure, and test the Agentic AI Customer Support application on your local development environment.

## 📋 **Prerequisites**

### **System Requirements**
- **OS**: macOS, Linux, or Windows (with WSL2)
- **RAM**: Minimum 8GB, Recommended 16GB+
- **Storage**: 10GB+ free space
- **CPU**: Multi-core processor (4+ cores recommended)

### **Required Software**
```bash
# Core tools
- Docker Desktop 4.0+
- Docker Compose 2.0+
- Python 3.9+
- Node.js 16+ (for frontend, if applicable)
- Git

# Optional but recommended
- kubectl (for Kubernetes testing)
- helm (for Helm chart testing)
- make (for Makefile commands)
```

### **API Keys Required**
```bash
# AI Service API Keys (required for full functionality)
export CLAUDE_API_KEY="your-anthropic-claude-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export GEMINI_API_KEY="your-google-gemini-api-key"

# Optional AWS Keys (for cloud testing)
export AWS_ACCESS_KEY_ID="your-aws-access-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

## 🚀 **Quick Start (5 Minutes)**

### **1. Clone and Setup**
```bash
# Clone repository
git clone https://github.com/paavanaadi-consulting/agentic-ai-customer-support.git
cd agentic-ai-customer-support

# Make scripts executable
chmod +x docker.sh
chmod +x ops/scripts/**/*.sh
chmod +x scripts/*.py

# Set up environment
cp config/env_settings.py.example config/env_settings.py
```

### **2. Docker-based Quick Start**
```bash
# Build and start all services
./docker.sh build
./docker.sh start

# Check service status
./docker.sh status

# View logs
./docker.sh logs
```

### **3. Verify Installation**
```bash
# Health check
curl http://localhost:8000/health

# API endpoints
curl http://localhost:8000/api/v1/customers
curl http://localhost:8000/docs  # Swagger UI
```

## 🔧 **Detailed Setup Options**

### **Option 1: Full Docker Stack (Recommended)**

#### **Step 1: Environment Configuration**
```bash
# Create environment file
cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://agenticai:change-me@localhost:5432/customer_support
POSTGRES_DB=customer_support
POSTGRES_USER=agenticai
POSTGRES_PASSWORD=change-me

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=agentic-ai

# Qdrant Configuration
QDRANT_URL=http://localhost:6333

# Application Configuration
LOG_LEVEL=INFO
DEBUG=true
ENVIRONMENT=development

# AI API Keys
CLAUDE_API_KEY=${CLAUDE_API_KEY}
OPENAI_API_KEY=${OPENAI_API_KEY}
GEMINI_API_KEY=${GEMINI_API_KEY}

# MCP Server URLs
MCP_POSTGRES_URL=http://localhost:8001
MCP_KAFKA_URL=http://localhost:8002
EOF
```

#### **Step 2: Start Infrastructure Services**
```bash
# Start core infrastructure
docker-compose -f ops/docker-compose.yml up -d postgres kafka qdrant

# Wait for services to be ready
sleep 30

# Verify infrastructure
docker-compose -f ops/docker-compose.yml ps
```

#### **Step 3: Initialize Database**
```bash
# Run database initialization
python scripts/init_db.py

# Seed with sample data
python scripts/seed_db.py

# Verify database setup
python scripts/test_postgresql.py
```

#### **Step 4: Start Application Services**
```bash
# Start MCP servers
python scripts/start_mcp_servers.py

# Start main application (in separate terminal)
python main.py --mode development

# Start API server (in another terminal)
python scripts/start_integrated_api.py
```

### **Option 2: Native Python Setup**

#### **Step 1: Python Environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

#### **Step 2: Setup External Services**
```bash
# Install and start PostgreSQL (macOS)
brew install postgresql
brew services start postgresql
createdb customer_support

# Install and start Kafka (macOS)
brew install kafka
brew services start kafka

# Install and start Qdrant
docker run -d -p 6333:6333 qdrant/qdrant
```

#### **Step 3: Native Application Setup**
```bash
# Configure environment
python scripts/setup_native.py

# Initialize database schema
python scripts/init_db.py

# Start MCP servers
python scripts/start_mcp_servers.py &

# Start main application
python main.py
```

### **Option 3: Kubernetes Local Testing**

#### **Step 1: Local Kubernetes Setup**
```bash
# Using kind (Kubernetes in Docker)
kind create cluster --config ops/kubernetes/kind-config.yaml

# Or using minikube
minikube start --memory=8192 --cpus=4

# Verify cluster
kubectl cluster-info
```

#### **Step 2: Deploy with Helm**
```bash
# Add Bitnami repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Build dependencies
cd ops/helm
helm dependency build

# Deploy to local cluster
helm install agentic-ai . -f values-local.yaml

# Check deployment
kubectl get pods
kubectl get services
```

## 🧪 **Testing Scenarios**

### **1. API Testing**

#### **Basic API Tests**
```bash
# Test health endpoint
curl -X GET http://localhost:8000/health

# Test customer creation
curl -X POST http://localhost:8000/api/v1/customers \\
  -H "Content-Type: application/json" \\
  -d '{
    "customer_id": "test_001",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "company": "Test Corp"
  }'

# Test query processing
curl -X POST http://localhost:8000/api/v1/queries \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "How do I reset my password?",
    "customer_id": "test_001"
  }'
```

#### **Automated API Testing**
```bash
# Run API test suite
python scripts/test_api.py

# Run integration tests
python scripts/test_api_integration.py

# Run specific test categories
python -m pytest tests/api/ -v
python -m pytest tests/services/ -v
```

### **2. AI Agent Testing**

#### **A2A Protocol Testing**
```bash
# Test agent-to-agent communication
python scripts/test_a2a_local.py

# Test individual agents
python -c "
from src.a2a_protocol.a2a_query_agent import A2AQueryAgent
agent = A2AQueryAgent()
result = await agent.process_input({'query': 'Test query'})
print(result)
"
```

#### **Genetic Algorithm Testing**
```bash
# Test evolution engine
python scripts/geneticml/test_evolution.py

# Run genetic optimization
python scripts/geneticml/run_evolution.py --generations 5
```

### **3. Database Testing**

#### **PostgreSQL Tests**
```bash
# Test database connectivity
python scripts/test_postgresql.py

# Test MCP PostgreSQL client
python scripts/test_mcp_postgres.py

# Test database operations
python -c "
from src.integration.database_service import DatabaseService
db = DatabaseService()
result = await db.get_customer('test_001')
print(result)
"
```

### **4. Event Streaming Testing**

#### **Kafka Tests**
```bash
# Test Kafka connectivity
python scripts/test_kafka.py

# Test MCP Kafka client
python scripts/test_mcp_kafka.py

# Test event processing
python -c "
from src.data_sources.kafka_consumer import KafkaConsumer
consumer = KafkaConsumer()
await consumer.start()
"
```

### **5. MCP Integration Testing**

#### **MCP Server Tests**
```bash
# Test MCP servers
python scripts/test_aws_mcp.py
python scripts/test_external_aws_mcp.py

# Test MCP client manager
python -c "
from src.mcp.mcp_client_manager import MCPClientManager
manager = MCPClientManager()
await manager.initialize()
"
```

### **6. End-to-End Testing**

#### **Full Workflow Test**
```bash
# Complete customer support workflow
python scripts/test_native.py

# Test with sample data
python -c "
import asyncio
from main import EnhancedGeneticAISupport

async def test_workflow():
    app = EnhancedGeneticAISupport()
    await app.initialize()
    
    # Test query processing
    result = await app.process_query({
        'query': 'I need help with my account',
        'customer_id': 'test_001'
    })
    print(f'Result: {result}')

asyncio.run(test_workflow())
"
```

## 🔍 **Testing Tools and Scripts**

### **Available Test Scripts**
```bash
# Health check
python scripts/health_check.py

# Database tests
python scripts/test_postgresql.py
python scripts/test_mcp_postgres.py

# API tests
python scripts/test_api.py
python scripts/test_api_integration.py

# MCP tests
python scripts/test_aws_mcp.py
python scripts/test_external_aws_mcp.py

# Event streaming tests
python scripts/test_kafka.py

# A2A protocol tests
python scripts/test_a2a_local.py

# Native setup tests
python scripts/test_native.py
```

### **pytest Test Suites**
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/api/ -v --tb=short
python -m pytest tests/services/ -v --tb=short
python -m pytest tests/a2a_protocol/ -v --tb=short
python -m pytest tests/geneticml/ -v --tb=short

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### **Load Testing**
```bash
# Install load testing tools
pip install locust artillery

# Run load tests
locust -f tests/load/locustfile.py --host=http://localhost:8000

# API load testing
artillery run tests/load/api-load-test.yml
```

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Database Connection Issues**
```bash
# Check PostgreSQL status
docker-compose -f ops/docker-compose.yml ps postgres

# Test database connection
psql postgresql://agenticai:change-me@localhost:5432/customer_support -c "\\dt"

# Reset database
docker-compose -f ops/docker-compose.yml down postgres
docker volume rm $(docker volume ls -q | grep postgres)
docker-compose -f ops/docker-compose.yml up -d postgres
```

#### **API Server Issues**
```bash
# Check API server logs
docker-compose -f ops/docker-compose.yml logs api

# Test API directly
python -c "
from src.api.api_main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000)
"
```

#### **MCP Server Issues**
```bash
# Check MCP server status
curl http://localhost:8001/health  # Postgres MCP
curl http://localhost:8002/health  # Kafka MCP

# Restart MCP servers
python scripts/stop_external_aws_mcp_servers.sh
python scripts/start_external_aws_mcp_servers.sh
```

#### **Agent Communication Issues**
```bash
# Test A2A protocol
python scripts/test_a2a_local.py

# Check agent logs
tail -f logs/agents.log
tail -f logs/a2a_protocol.log
```

### **Performance Testing**

#### **Resource Monitoring**
```bash
# Monitor Docker resources
docker stats

# Monitor system resources
htop  # or top on macOS
iostat -x 1
free -h  # Linux only
```

#### **Application Metrics**
```bash
# Check application health
curl http://localhost:8000/health

# Monitor API performance
curl http://localhost:8000/metrics  # If metrics endpoint is enabled

# Database performance
python -c "
from src.integration.database_service import DatabaseService
db = DatabaseService()
print(await db.get_performance_stats())
"
```

## 📊 **Expected Results**

### **Successful Setup Indicators**
- ✅ All Docker containers running (`docker-compose ps`)
- ✅ API health check returns 200 (`curl localhost:8000/health`)
- ✅ Database tables created (`psql -c "\\dt"`)
- ✅ MCP servers responding (`curl localhost:8001/health`)
- ✅ Kafka topics created (`kafka-topics.sh --list`)
- ✅ AI agents initialized (check logs)

### **Test Success Metrics**
- ✅ API tests pass (≥95% success rate)
- ✅ Database operations complete successfully
- ✅ MCP integration tests pass
- ✅ A2A protocol communication works
- ✅ Query processing returns valid responses
- ✅ Genetic algorithm evolution runs

### **Performance Benchmarks**
- 🎯 API response time: <500ms for simple queries
- 🎯 Database query time: <100ms for standard operations
- 🎯 AI agent response time: <2s for complex queries
- 🎯 Memory usage: <2GB for full stack
- 🎯 CPU usage: <70% under normal load

## 🔄 **Continuous Testing**

### **Development Workflow**
```bash
# 1. Start development environment
./docker.sh start

# 2. Run tests before changes
python -m pytest tests/ -v

# 3. Make code changes

# 4. Run specific tests
python scripts/test_api.py

# 5. Run full test suite
python -m pytest tests/ --cov=src

# 6. Check integration
python scripts/test_native.py
```

### **CI/CD Pipeline (Local)**
```bash
# Simulate CI/CD pipeline locally
bash -c "
set -e
echo '1. Linting...'
flake8 src/ tests/

echo '2. Type checking...'
mypy src/

echo '3. Security checks...'
bandit -r src/

echo '4. Tests...'
python -m pytest tests/ -v

echo '5. Integration tests...'
python scripts/test_api_integration.py

echo '6. Load tests...'
locust -f tests/load/locustfile.py --headless -u 10 -r 2 -t 30s --host=http://localhost:8000

echo '✅ All checks passed!'
"
```

This comprehensive testing guide provides multiple pathways to test the application locally, from quick Docker-based setup to detailed native installation and Kubernetes deployment testing.
