# Local Testing Guide for Agentic AI Customer Support

This guide provides step-by-step instructions for setting up and testing the Agentic AI Customer Support application locally.

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8+ (recommended: 3.11+)
- **Docker**: Latest version with Docker Compose
- **Git**: For cloning and version control
- **System RAM**: Minimum 8GB (recommended: 16GB+)
- **Storage**: At least 5GB free space

### macOS Specific Setup
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install python@3.11 docker docker-compose git
brew install --cask docker  # Docker Desktop

# Start Docker Desktop
open /Applications/Docker.app
```

## 🚀 Quick Start (5 Minutes)

### Option 1: Automated Setup
```bash
# Navigate to project root
cd /Users/ashokasangapallar/Desktop/studyrepos/agentic-ai-customer-support

# Run the quick setup script
chmod +x scripts/quick_test.sh
./scripts/quick_test.sh --mode=full
```

### Option 2: Manual Setup

#### Step 1: Environment Setup
```bash
# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -e .
```

#### Step 2: Configuration
```bash
# Copy environment templates
cp config/env_settings.py.example config/env_settings.py
cp config/postgres_mcp.env.example config/postgres_mcp.env
cp config/kafka.env.example config/kafka.env
cp config/aws_mcp.env.example config/aws_mcp.env

# Edit configuration files with your settings
nano config/env_settings.py
```

#### Step 3: Start Infrastructure Services
```bash
# Start core services (PostgreSQL, Kafka, Qdrant)
docker-compose -f ops/docker-compose.yml up -d postgres kafka qdrant

# Wait for services to be ready (30-60 seconds)
docker-compose -f ops/docker-compose.yml logs -f
```

#### Step 4: Initialize Database
```bash
# Run database initialization
python scripts/init_db.py
python scripts/seed_db.py
```

#### Step 5: Start Application Services
```bash
# Terminal 1: Start MCP servers
python scripts/start_mcp_servers.py

# Terminal 2: Start main API
python scripts/start_integrated_api.py

# Terminal 3: Start main application
python main.py --mode=local
```

## 🧪 Testing Scenarios

### 1. Health Check Tests
```bash
# Test API health
python scripts/health_check.py

# Test database connectivity
python scripts/test_postgresql.py

# Test Kafka connectivity
python scripts/test_kafka.py

# Test MCP servers
python scripts/test_mcp_postgres.py
python scripts/test_aws_mcp.py
```

### 2. API Integration Tests
```bash
# Run comprehensive API tests
python scripts/test_api.py

# Run integration tests
python scripts/test_api_integration.py

# Test A2A protocol locally
python scripts/test_a2a_local.py
```

### 3. End-to-End Tests
```bash
# Test customer support flow
curl -X POST http://localhost:8000/api/v1/support/query \
  -H "Content-Type: application/json" \
  -d '{"query": "I need help with my account", "user_id": "test_user"}'

# Test genetic algorithm evolution
curl -X POST http://localhost:8000/api/v1/evolution/trigger \
  -H "Content-Type: application/json" \
  -d '{"generations": 5, "population_size": 10}'
```

## 🔧 Development Workflow

### Daily Development Setup
```bash
# 1. Start development environment
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 2. Start infrastructure
docker-compose -f ops/docker-compose.yml up -d postgres kafka qdrant

# 3. Start development servers
python scripts/start_mcp_servers.py &
python scripts/start_integrated_api.py &
```

### Code Testing
```bash
# Run unit tests
python -m pytest tests/ -v

# Run specific test modules
python -m pytest tests/api/ -v
python -m pytest tests/a2a_protocol/ -v
python -m pytest tests/services/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Database Operations
```bash
# Reset database
python scripts/cleanup.py --database
python scripts/init_db.py
python scripts/seed_db.py

# Export/Import data
python scripts/export_data.py --format=json
python scripts/import_data.py --file=data_export.json
```

## 🐳 Docker-Based Testing

### Full Stack with Docker
```bash
# Start all services
docker-compose -f ops/docker-compose.yml up -d

# View logs
docker-compose -f ops/docker-compose.yml logs -f api-service

# Scale services
docker-compose -f ops/docker-compose.yml up -d --scale consumer-service=3

# Stop all services
docker-compose -f ops/docker-compose.yml down
```

### Individual Service Testing
```bash
# Test specific services
docker-compose -f ops/docker-compose.yml up postgres
docker-compose -f ops/docker-compose.yml up mcp-postgres
docker-compose -f ops/docker-compose.yml up api-service
```

## 📊 Monitoring and Debugging

### Application Logs
```bash
# View application logs
tail -f logs/application.log

# View specific service logs
tail -f logs/api-service.log
tail -f logs/mcp-postgres.log
tail -f logs/geneticml.log
```

### Performance Monitoring
```bash
# Monitor system resources
docker stats

# Monitor application metrics
curl http://localhost:8000/metrics

# Database query performance
psql -h localhost -U admin -d customer_support -c "SELECT * FROM pg_stat_activity;"
```

### Common Issues and Solutions

#### Issue: Port Already in Use
```bash
# Check what's using the port
lsof -i :8000
lsof -i :5432

# Kill process using port
kill -9 $(lsof -ti:8000)
```

#### Issue: Database Connection Failed
```bash
# Check PostgreSQL status
docker-compose -f ops/docker-compose.yml ps postgres

# Reset database
docker-compose -f ops/docker-compose.yml restart postgres
```

#### Issue: MCP Server Not Responding
```bash
# Check MCP server status
ps aux | grep mcp
curl http://localhost:8001/health  # PostgreSQL MCP
curl http://localhost:8002/health  # Kafka MCP
```

## 🧩 Component Testing

### A2A Protocol Testing
```bash
# Test agent communication
python examples/a2a_usage_example.py

# Test knowledge sharing
python -c "
from src.a2a_protocol.a2a_coordinator import A2ACoordinator
import asyncio

async def test():
    coordinator = A2ACoordinator()
    await coordinator.initialize()
    result = await coordinator.process_query('Test query')
    print(result)

asyncio.run(test())
"
```

### Genetic ML Testing
```bash
# Test evolution engine
python -c "
from src.geneticML.engines.evolution_engine import EvolutionEngine
import asyncio

async def test():
    engine = EvolutionEngine()
    await engine.initialize()
    result = await engine.evolve_solutions(generations=3)
    print(result)

asyncio.run(test())
"
```

### MCP Integration Testing
```bash
# Test PostgreSQL MCP
python examples/mcp_integration_example.py

# Test optimized MCP usage
python examples/optimized_mcp_usage.py

# Test external AWS MCP
python examples/external_aws_mcp_example.py
```

## 📈 Performance Testing

### Load Testing
```bash
# Install load testing tools
pip install locust

# Run load tests
locust -f tests/load_tests.py --host=http://localhost:8000
```

### Stress Testing
```bash
# Test with high concurrency
ab -n 1000 -c 50 http://localhost:8000/api/v1/health

# Test database performance
pgbench -h localhost -U admin -d customer_support -c 10 -t 100
```

## 🔐 Security Testing

### API Security
```bash
# Test authentication
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'

# Test authorization
curl -X GET http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🚢 Production Readiness

### Environment Validation
```bash
# Check configuration
python -c "from config.settings import CONFIG; print(CONFIG)"

# Validate dependencies
pip check

# Security scan
pip install safety
safety check
```

### Deployment Testing
```bash
# Test with production-like settings
export ENV=production
python main.py --mode=production

# Test Helm chart
helm template agentic-ai-customer-support ops/helm/
helm install --dry-run agentic-ai-customer-support ops/helm/
```

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs (when running)
- **Architecture Guide**: [docs/ops/README.md](docs/ops/README.md)
- **Helm Documentation**: [ops/helm/README.md](ops/helm/README.md)
- **Troubleshooting**: [docs/ops/TROUBLESHOOTING.md](docs/ops/TROUBLESHOOTING.md)

## 🆘 Getting Help

### Debug Mode
```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
python main.py --mode=local --debug

# Enable SQL query logging
export DB_ECHO=true
```

### Health Checks
```bash
# Comprehensive health check
python scripts/health_check.py --verbose

# Service-specific checks
python scripts/health_check.py --service=database
python scripts/health_check.py --service=kafka
python scripts/health_check.py --service=qdrant
```

### Support Commands
```bash
# Generate support bundle
python scripts/generate_support_bundle.py

# Run diagnostics
python scripts/diagnostics.py
```

---

**Next Steps**: After completing local testing, proceed to [Kubernetes deployment](docs/ops/KUBERNETES_DOCUMENTATION.md) or [Helm chart setup](ops/helm/README.md).
