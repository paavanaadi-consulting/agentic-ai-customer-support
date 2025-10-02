# Troubleshooting Guide for Local Testing

This guide helps you diagnose and fix common issues when setting up and testing the Agentic AI Customer Support application locally.

## 🚨 Common Issues and Solutions

### 1. Python Environment Issues

#### Issue: Import Errors
```bash
ModuleNotFoundError: No module named 'src'
```

**Solution:**
```bash
# Ensure PYTHONPATH is set correctly
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install in development mode
pip install -e .

# Verify Python path
python3 -c "import sys; print('\n'.join(sys.path))"
```

#### Issue: Package Installation Failures
```bash
ERROR: Could not find a version that satisfies the requirement...
```

**Solution:**
```bash
# Update pip
pip install --upgrade pip

# Install specific versions
pip install -r requirements.txt

# For macOS ARM64 issues
pip install --no-deps package_name
```

### 2. Database Connection Issues

#### Issue: PostgreSQL Connection Refused
```bash
psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed
```

**Solutions:**
```bash
# Check if PostgreSQL is running
docker-compose -f ops/docker-compose.yml ps postgres

# Start PostgreSQL
docker-compose -f ops/docker-compose.yml up -d postgres

# Check logs
docker-compose -f ops/docker-compose.yml logs postgres

# Test connection manually
psql -h localhost -U admin -d customer_support

# Reset database
docker-compose -f ops/docker-compose.yml restart postgres
```

#### Issue: Database Schema Missing
```bash
relation "customers" does not exist
```

**Solutions:**
```bash
# Reinitialize database
python scripts/init_db.py

# Check if tables exist
psql -h localhost -U admin -d customer_support -c "\dt"

# Force recreate tables
python scripts/init_db.py --force-recreate

# Seed with test data
python scripts/seed_db.py
```

### 3. Docker Issues

#### Issue: Port Already in Use
```bash
ERROR: for postgres  Cannot start service postgres: driver failed programming external connectivity
```

**Solutions:**
```bash
# Find what's using the port
lsof -i :5432
lsof -i :9092
lsof -i :6333

# Kill the process
kill -9 PID_NUMBER

# Use different ports in docker-compose.yml
ports:
  - "5433:5432"  # Changed from 5432
```

#### Issue: Docker Daemon Not Running
```bash
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solutions:**
```bash
# Start Docker Desktop on macOS
open /Applications/Docker.app

# Verify Docker is running
docker version
docker ps

# Restart Docker service (Linux)
sudo systemctl restart docker
```

### 4. Kafka Issues

#### Issue: Kafka Broker Not Available
```bash
NoBrokersAvailable: NoBrokersAvailable
```

**Solutions:**
```bash
# Check Kafka status
docker-compose -f ops/docker-compose.yml ps kafka

# Start Kafka
docker-compose -f ops/docker-compose.yml up -d kafka

# Check Kafka logs
docker-compose -f ops/docker-compose.yml logs kafka

# Test Kafka connectivity
python scripts/test_kafka.py

# Reset Kafka
docker-compose -f ops/docker-compose.yml restart kafka
```

#### Issue: Topic Creation Failed
```bash
UnknownTopicOrPartitionError
```

**Solutions:**
```bash
# Create topics manually
docker exec -it kafka_container kafka-topics.sh \
  --create --topic customer-support \
  --bootstrap-server localhost:9092

# List existing topics
docker exec -it kafka_container kafka-topics.sh \
  --list --bootstrap-server localhost:9092
```

### 5. API Server Issues

#### Issue: API Server Won't Start
```bash
Address already in use: Port 8000
```

**Solutions:**
```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
kill -9 $(lsof -ti:8000)

# Use different port
export PORT=8001
python scripts/start_integrated_api.py

# Check API logs
tail -f logs/api-server.log
```

#### Issue: FastAPI Import Errors
```bash
ImportError: cannot import name 'app' from 'src.api.api_main'
```

**Solutions:**
```bash
# Check if API module exists
ls -la src/api/

# Test API imports
python3 -c "from src.api.api_main import app; print('OK')"

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 6. MCP Server Issues

#### Issue: MCP Servers Not Responding
```bash
ConnectionError: HTTPConnectionPool(host='localhost', port=8001): Max retries exceeded
```

**Solutions:**
```bash
# Check MCP server status
ps aux | grep mcp

# Start MCP servers
python scripts/start_mcp_servers.py

# Check individual MCP health
curl http://localhost:8001/health  # PostgreSQL MCP
curl http://localhost:8002/health  # Kafka MCP

# Kill and restart MCP servers
pkill -f mcp_server
python scripts/start_mcp_servers.py
```

#### Issue: MCP Installation Problems
```bash
ModuleNotFoundError: No module named 'mcp'
```

**Solutions:**
```bash
# Install MCP packages
pip install mcp

# Check if MCP is installed
python3 -c "import mcp; print('MCP installed')"

# Reinstall if needed
pip uninstall mcp
pip install mcp
```

### 7. Qdrant Vector Database Issues

#### Issue: Qdrant Connection Failed
```bash
ConnectError: [Errno 61] Connection refused
```

**Solutions:**
```bash
# Start Qdrant
docker-compose -f ops/docker-compose.yml up -d qdrant

# Check Qdrant logs
docker-compose -f ops/docker-compose.yml logs qdrant

# Test Qdrant connectivity
curl http://localhost:6333/health

# Reset Qdrant data
docker volume rm qdrant_data
docker-compose -f ops/docker-compose.yml up -d qdrant
```

### 8. Genetic ML Engine Issues

#### Issue: Evolution Engine Failures
```bash
AttributeError: 'NoneType' object has no attribute 'evolve'
```

**Solutions:**
```bash
# Check genetic ML dependencies
pip install numpy scikit-learn

# Test evolution engine
python3 -c "
from src.geneticML.engines.evolution_engine import EvolutionEngine
print('Evolution engine import successful')
"

# Check configuration
python3 -c "from config.settings import CONFIG; print(CONFIG.get('genetic_ml', {}))"
```

### 9. AI API Key Issues

#### Issue: API Key Authentication Failed
```bash
AuthenticationError: Invalid API key provided
```

**Solutions:**
```bash
# Check environment variables
echo $CLAUDE_API_KEY
echo $OPENAI_API_KEY
echo $GEMINI_API_KEY

# Set API keys
export CLAUDE_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"
export GEMINI_API_KEY="your-key-here"

# Add to .env file
echo "CLAUDE_API_KEY=your-key-here" >> .env
echo "OPENAI_API_KEY=your-key-here" >> .env
echo "GEMINI_API_KEY=your-key-here" >> .env

# Test API connectivity
python3 scripts/test_ai_apis.py
```

### 10. Memory and Performance Issues

#### Issue: Out of Memory Errors
```bash
MemoryError: Unable to allocate array
```

**Solutions:**
```bash
# Check available memory
free -h  # Linux
vm_stat  # macOS

# Reduce batch sizes in configuration
# Edit config/settings.py
BATCH_SIZE = 10  # Reduce from default

# Increase Docker memory limits
# Docker Desktop -> Preferences -> Resources -> Memory
```

#### Issue: Slow Performance
```bash
# System feels sluggish during testing
```

**Solutions:**
```bash
# Check CPU usage
top
htop

# Reduce concurrent processes
# Modify docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 512M

# Use lighter AI models for testing
export AI_MODEL="gpt-3.5-turbo"  # Instead of gpt-4
```

## 🔍 Debugging Commands

### System Diagnostics
```bash
# Comprehensive health check
python scripts/health_check.py --verbose

# Run specific tests
python scripts/run_local_tests.py --category=database

# Check all services
./scripts/quick_test.sh status

# View all logs
tail -f logs/*.log
```

### Service-Specific Debugging
```bash
# Database debugging
psql -h localhost -U admin -d customer_support -c "SELECT COUNT(*) FROM customers;"

# Kafka debugging
docker exec -it kafka_container kafka-console-consumer.sh \
  --topic customer-support --bootstrap-server localhost:9092

# API debugging
curl -v http://localhost:8000/health
curl -v http://localhost:8000/api/v1/info

# MCP debugging
curl -v http://localhost:8001/list_tools
curl -v http://localhost:8002/list_tools
```

### Log Analysis
```bash
# View recent logs
tail -50 logs/application.log

# Search for errors
grep -i error logs/*.log

# Follow logs in real-time
tail -f logs/api-server.log | grep ERROR

# Docker logs
docker-compose -f ops/docker-compose.yml logs --tail=50 postgres
```

## 🆘 Emergency Reset

### Complete System Reset
```bash
# Stop everything
./scripts/quick_test.sh stop

# Clean Docker
docker-compose -f ops/docker-compose.yml down -v
docker system prune -f

# Clean Python environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Restart from scratch
./scripts/quick_test.sh start
```

### Selective Reset
```bash
# Reset database only
docker-compose -f ops/docker-compose.yml restart postgres
python scripts/init_db.py
python scripts/seed_db.py

# Reset Kafka only
docker-compose -f ops/docker-compose.yml restart kafka

# Reset application only
pkill -f "python.*start_"
python scripts/start_mcp_servers.py &
python scripts/start_integrated_api.py &
```

## 📞 Getting Help

### Log Collection for Support
```bash
# Generate support bundle
mkdir support_bundle
cp logs/*.log support_bundle/
docker-compose -f ops/docker-compose.yml logs > support_bundle/docker_logs.txt
python scripts/health_check.py --json > support_bundle/health_check.json
python scripts/run_local_tests.py --json > support_bundle/test_results.json
tar -czf support_bundle.tar.gz support_bundle/
```

### Environment Information
```bash
# System info
uname -a
python3 --version
docker --version
docker-compose --version

# Package versions
pip list > support_bundle/pip_list.txt

# Configuration dump
python3 -c "
from config.settings import CONFIG
import json
print(json.dumps(CONFIG, indent=2, default=str))
" > support_bundle/config.json
```

### Contact Information
- **Documentation**: Check `docs/` directory for additional guides
- **Issues**: Create GitHub issues with logs and system information
- **Community**: Join the project Discord/Slack for real-time help

---

**Remember**: Always check the logs first! Most issues can be diagnosed by examining the log files in the `logs/` directory.
