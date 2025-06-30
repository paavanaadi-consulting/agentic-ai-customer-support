# Agentic AI Customer Support System

A sophisticated multi-agent AI system that provides intelligent customer support through evolutionary algorithms, genetic optimization, and comprehensive Docker-based deployment. The system features modular AI agents, comprehensive API endpoints, and scalable infrastructure for enterprise customer service operations.

## 🚀 Features

- **🤖 Multi-Agent Architecture**: Specialized AI agents (Query, Knowledge, Response) working collaboratively
- **🧬 Genetic Algorithm Evolution**: Agents evolve and optimize their strategies over time for better performance
- **🔗 Agent-to-Agent (A2A) Protocol**: Decoupled agent communication for maximum scalability
- **🗄️ Multi-Source Data Integration**: PostgreSQL, Vector DB, Kafka, PDF documents, and real-time streams
- **🐳 Complete Docker Infrastructure**: Production-ready containerized deployment with organized CI/CD scripts
- **🌐 Comprehensive REST API**: Full API v1 with endpoints for queries, tickets, customers, feedback, and analytics
- **📊 Real-time Analytics**: Performance monitoring, customer satisfaction tracking, and system metrics
- **⚙️ Flexible Configuration**: Environment-specific settings with unified configuration management
- **🏥 Health Monitoring**: Built-in health checks and system monitoring capabilities
- **🔧 MCP Integration**: Model Context Protocol support for external service integration

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Docker Deployment](#-docker-deployment)
- [Development](#-development)
- [Contributing](#-contributing)

## 🎯 Quick Start

### Option 1: Docker Deployment (Recommended)

**Full System:**
```bash
git clone https://github.com/yourusername/agentic-ai-customer-support.git
cd agentic-ai-customer-support

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings

# Build and start all services
./cicd/scripts/main/build.sh
./cicd/scripts/main/start.sh

# Check system status
./cicd/scripts/main/health-check.sh
```

**API Component Only (Lightweight):**
```bash
# For lightweight API-only deployment
./cicd/scripts/main/api/build-api.sh
./cicd/scripts/main/api/start-api.sh

# Test the API
./cicd/scripts/test/test-api.sh

# Demo API functionality
./cicd/scripts/test/demo-api-v1.sh
```

### Option 2: Local Development

```bash
# Clone and setup
git clone https://github.com/yourusername/agentic-ai-customer-support.git
cd agentic-ai-customer-support

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python scripts/init_db.py

# Run the system
python main.py
```

## 🏗 Architecture

### System Overview

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Data Sources      │    │   Agent Layer       │    │   Evolution         │
├─────────────────────┤    ├─────────────────────┤    ├─────────────────────┤
│ • PostgreSQL        │────▶│ • Enhanced Query    │────▶│ • Genetic Algorithm │
│ • Vector Database   │    │   Agent (Claude)    │    │ • Fitness Evaluation│
│ • PDF Documents     │    │ • Knowledge Agent   │    │ • Strategy Evolution│
│ • Kafka Streams     │    │   (Gemini)          │    │ • Performance Opt.  │
│ • Real-time Data    │    │ • Response Agent    │    │ • Adaptive Learning │
└─────────────────────┘    │   (GPT)             │    └─────────────────────┘
                          └─────────────────────┘
                                    │
                          ┌─────────────────────┐
                          │   API & Interface   │
                          ├─────────────────────┤
                          │ • REST API v1       │
                          │ • WebSocket Support │
                          │ • Health Monitoring │
                          │ • Analytics Dashboard│
                          └─────────────────────┘
```

### Agent Workflow

1. **Enhanced Query Agent**: Analyzes and classifies customer queries with database context
2. **Knowledge Agent**: Retrieves relevant information from multiple data sources
3. **Response Agent**: Crafts intelligent, contextual responses
4. **Evolution Engine**: Continuously optimizes agent strategies using genetic algorithms

### Project Structure

```
agentic-ai-customer-support/
├── 📄 main.py                     # Main application entry point
├── ⚙️ config/                     # Configuration management
│   ├── env_settings.py           # Environment-specific settings
│   └── settings.py               # Legacy settings (deprecated)
├── 🤖 agents/                     # AI Agent implementations
│   ├── base_agent.py
│   ├── enhanced_query_agent.py
│   ├── knowledge_agent.py
│   └── response_agent.py
├── 🔗 a2a_protocol/              # Agent-to-Agent communication
│   ├── base_a2a_agent.py
│   ├── a2a_coordinator.py
│   └── a2a_*.py
├── 🌐 api/                       # REST API implementation
│   ├── api_main.py               # API-only server
│   ├── routes.py                 # API v1 endpoints
│   └── schemas.py                # Request/Response models
├── 🧠 core/                      # Core system components
│   ├── evolution_engine.py      # Genetic algorithm engine
│   └── fitness_evaluator.py     # Performance evaluation
├── 🗄️ data_sources/              # Data integration layer
│   ├── pdf_processor.py
│   ├── rdbms_connector.py
│   ├── vector_db_client.py
│   └── kafka_consumer.py
├── 🐳 cicd/                      # Docker & CI/CD infrastructure
│   ├── docker-compose.yml       # Full system deployment
│   ├── docker-compose.api.yml   # API-only deployment
│   ├── scripts/                 # Management scripts
│   │   ├── main/               # Core infrastructure scripts
│   │   │   ├── api/           # API-specific scripts
│   │   │   ├── build*.sh      # Build scripts
│   │   │   ├── start*.sh      # Startup scripts
│   │   │   └── stop*.sh       # Shutdown scripts
│   │   └── test/              # Testing scripts
│   ├── api/                    # API Docker configuration
│   ├── postgres/              # Database Docker setup
│   └── main-app/              # Main app containerization
├── 🔧 scripts/                  # Utility scripts
│   ├── init_db.py
│   ├── seed_db.py
│   ├── health_check.py
│   └── test_api.py
├── 📊 data/                     # Data and schema files
│   ├── postgres_schema.sql
│   └── sample data generators
├── 🔌 integration/              # Service integration
│   └── database_service.py
├── 🛠️ utils/                    # Utility functions
└── 📚 docs/                     # Documentation
```

## 💾 Installation

### Prerequisites

- **Python 3.8+**
- **Docker & Docker Compose** (for containerized deployment)
- **PostgreSQL** (for local development)
- **API Keys**: Claude, Gemini, OpenAI
- **Optional**: Kafka, Vector Database (Qdrant)

### Installation Options

```bash
# Minimal installation (core only)
pip install -e .

# With web server capabilities
pip install -e .[server]

# With data visualization features
pip install -e .[visualization]

# Complete installation with all features
pip install -e .[all]

# Development installation
pip install -e .[dev]
```

### Database Setup

```bash
# Initialize database schema
python scripts/init_db.py

# Seed with sample data
python scripts/seed_db.py

# Generate additional test data
python data/generate_postgres_sample_data.py
```

## ⚙️ Configuration

### Environment Configuration (`.env`)

```env
# AI Model API Keys
CLAUDE_API_KEY=your_claude_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=admin
DB_PASSWORD=password
DB_NAME=customer_support

# Vector Database
VECTOR_DB_HOST=localhost
VECTOR_DB_PORT=6333
VECTOR_DB_COLLECTION=knowledge_base

# Kafka Configuration (Optional)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPICS=customer-queries,feedback-events

# Genetic Algorithm Settings
POPULATION_SIZE=20
MUTATION_RATE=0.1
CROSSOVER_RATE=0.8
MAX_GENERATIONS=100
FITNESS_THRESHOLD=0.95

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Environment
ENV=development  # development, staging, production
DEBUG=false
LOG_LEVEL=INFO
```

### Advanced Configuration

The system supports environment-specific configurations through `config/env_settings.py`:

```python
from config.env_settings import CONFIG

# Access configuration
api_key = CONFIG.CLAUDE_API_KEY
db_host = CONFIG.DB_HOST
population_size = CONFIG.POPULATION_SIZE
```

## 🚀 Usage

### Running the Complete System

```bash
# Start all services
python main.py

# With specific configuration
python main.py --mode server --port 8000

# Training mode for genetic algorithm
python main.py --mode train --generations 50
```

### API-Only Mode

```bash
# Start lightweight API server
python api/api_main.py

# Or using Docker
./cicd/scripts/main/api/start-api.sh
```

### Basic Python Usage

```python
from main import EnhancedGeneticAISupport
import asyncio

async def main():
    # Initialize the system
    ai_support = EnhancedGeneticAISupport()
    await ai_support.initialize()
    
    # Process a customer query
    result = await ai_support.process_query({
        'query': 'I need help with my billing issue',
        'customer_id': '12345',
        'context': {'priority': 'high'}
    })
    
    print(f"Response: {result['response']}")
    print(f"Confidence: {result['confidence']}")

# Run the example
asyncio.run(main())
```

### Agent-to-Agent (A2A) Protocol Usage

```python
from a2a_protocol.a2a_coordinator import A2ACoordinator
import asyncio

async def run_a2a_workflow():
    coordinator = A2ACoordinator()
    
    workflow_data = {
        "task_type": "customer_support_workflow",
        "query_data": {
            "query": "How do I upgrade my plan?",
            "customer_id": "12345",
            "priority": "medium"
        }
    }
    
    result = await coordinator.process_task(workflow_data)
    print(f"A2A Result: {result}")

asyncio.run(run_a2a_workflow())
```

## 🌐 API Documentation

### REST API Endpoints (v1)

#### **Query Processing**
```http
POST /api/v1/queries
Content-Type: application/json

{
  "query": "How do I reset my password?",
  "customer_id": "cust-123",
  "query_type": "technical",
  "priority": "medium",
  "context": {}
}
```

#### **Ticket Management**
```http
POST /api/v1/tickets
Content-Type: application/json

{
  "title": "Cannot access account",
  "description": "Customer unable to log in",
  "customer_id": "cust-123",
  "category": "account",
  "priority": "high"
}
```

#### **Customer Management**
```http
POST /api/v1/customers
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1-555-0123",
  "company": "Acme Corp"
}
```

#### **Analytics & Monitoring**
```http
GET /api/v1/analytics          # System metrics
GET /api/v1/status            # API status
GET /api/v1/queries           # List queries
GET /api/v1/tickets           # List tickets
GET /api/v1/customers         # List customers
GET /api/v1/feedback          # List feedback
```

### Interactive API Documentation

- **Swagger UI**: `http://localhost:8080/docs`
- **ReDoc**: `http://localhost:8080/redoc`
- **OpenAPI Spec**: `http://localhost:8080/openapi.json`

### Example API Usage

```bash
# Process a query
curl -X POST http://localhost:8080/api/v1/queries \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I forgot my password",
    "customer_id": "cust-001",
    "query_type": "technical",
    "priority": "medium"
  }'

# Get system analytics
curl http://localhost:8080/api/v1/analytics

# Check API health
curl http://localhost:8080/api/v1/status
```

## 🐳 Docker Deployment

### Full System Deployment

```bash
# Build all services
./cicd/scripts/main/build-all.sh

# Start complete system (API, Database, Kafka, Vector DB, etc.)
./cicd/scripts/main/start-all.sh

# Monitor services
./cicd/scripts/main/logs.sh

# Health check
./cicd/scripts/main/health-check.sh

# Stop all services
./cicd/scripts/main/stop-all.sh
```

### API-Only Deployment (Lightweight)

```bash
# Build API service
./cicd/scripts/main/api/build-api.sh

# Start API with PostgreSQL
./cicd/scripts/main/api/start-api.sh

# Test API functionality
./cicd/scripts/test/test-api.sh

# Demo API endpoints
./cicd/scripts/test/demo-api-v1.sh

# Stop API services
./cicd/scripts/main/api/stop-api.sh
```

### Infrastructure Management

```bash
# Start only infrastructure (PostgreSQL, Redis, etc.)
./cicd/scripts/main/start-infrastructure.sh

# Stop infrastructure
./cicd/scripts/main/stop-infrastructure.sh

# Clean up resources
./cicd/scripts/main/cleanup-all.sh
```

### Available Docker Services

- **API Service**: FastAPI web server (`localhost:8080`)
- **Main Application**: Complete AI system (`localhost:8000`)
- **PostgreSQL**: Database service (`localhost:5432`)
- **Redis**: Caching layer (`localhost:6379`)
- **Qdrant**: Vector database (`localhost:6333`)
- **Kafka**: Message streaming (`localhost:9092`)
- **Agents Service**: AI agents (`localhost:8005`)
- **MCP Services**: Model Context Protocol servers

## 🧬 Genetic Algorithm & Evolution

### Evolution Process

The system uses genetic algorithms to evolve agent strategies:

1. **Initialize Population**: Random agent strategies
2. **Evaluate Fitness**: Performance metrics (response time, accuracy, satisfaction)
3. **Selection**: Choose best-performing strategies
4. **Crossover**: Combine successful strategies
5. **Mutation**: Introduce variations
6. **Evolution**: Iterate to improve performance

### Fitness Metrics

```python
fitness_score = (
    0.40 * success_rate +
    0.30 * response_time_score +
    0.30 * customer_satisfaction
)
```

### Agent Strategy Parameters

**Query Agent (Claude)**:
- Confidence thresholds
- Context window size
- Classification detail level
- Sentiment analysis enablement

**Knowledge Agent (Gemini)**:
- Search depth
- Relevance thresholds
- Source synthesis level
- Fact-checking parameters

**Response Agent (GPT)**:
- Response tone and style
- Personalization level
- Empathy considerations
- Length preferences

## 🏥 Monitoring & Analytics

### Health Checks

```bash
# System health check
./cicd/scripts/main/health-check.sh

# API-specific health check
curl http://localhost:8080/health

# Database health check
python scripts/health_check.py
```

### Performance Metrics

- **Agent Performance**: Success rates, response times, evolution progress
- **System Metrics**: Throughput, latency, error rates, resource usage
- **Business Metrics**: Customer satisfaction, resolution rates, agent effectiveness
- **Database Metrics**: Query performance, connection health, data integrity

### Monitoring Dashboard

Access monitoring capabilities:
- **API Status**: `http://localhost:8080/api/v1/status`
- **Analytics**: `http://localhost:8080/api/v1/analytics`
- **Health Check**: `http://localhost:8080/health`

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Test specific components
pytest tests/test_agents.py
pytest tests/test_api.py
pytest tests/test_evolution.py

# Integration tests
pytest tests/test_integration.py -v

# Performance tests
pytest tests/test_performance.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### API Testing

```bash
# Automated API test suite
./cicd/scripts/test/test-api.sh

# API v1 demonstration
./cicd/scripts/test/demo-api-v1.sh

# Manual API testing
python scripts/test_api.py
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Service interaction testing
- **API Tests**: Endpoint functionality testing
- **Performance Tests**: Load and stress testing
- **Evolution Tests**: Genetic algorithm testing

## 🛠 Development

### Development Setup

```bash
# Install development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Run code formatting
black .
isort .

# Run linting
flake8 .

# Type checking
mypy .
```

### Adding New Agents

1. Create agent class inheriting from `BaseAgent`
2. Implement required methods
3. Define chromosome structure
4. Add to evolution engine
5. Write comprehensive tests

### Adding New Data Sources

1. Create connector in `data_sources/`
2. Implement data retrieval methods
3. Add to configuration
4. Update knowledge agents
5. Test integration

### Development Scripts

```bash
# Database operations
python scripts/init_db.py       # Initialize database
python scripts/seed_db.py       # Seed test data
python scripts/cleanup.py       # Clean test data

# Development utilities
python scripts/health_check.py  # System health
python scripts/export_data.py   # Export data
python scripts/import_data.py   # Import data
```

## 🔒 Security & Production

### Security Features

- **API Authentication**: Token-based authentication
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: API request throttling
- **CORS Configuration**: Cross-origin request handling
- **Environment Isolation**: Secure configuration management

### Production Considerations

- **Environment Variables**: Secure configuration via environment
- **Database Security**: Connection pooling, query optimization
- **Monitoring**: Comprehensive logging and alerting
- **Scaling**: Horizontal scaling support
- **Backup & Recovery**: Database backup strategies

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Add tests**: Ensure your changes are tested
5. **Run the test suite**: `pytest`
6. **Commit your changes**: `git commit -m 'Add amazing feature'`
7. **Push to the branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Code Style Guidelines

- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Write comprehensive docstrings
- Add unit tests for new functionality
- Update documentation as needed

### Development Workflow

- Use feature branches for development
- Write descriptive commit messages
- Ensure all tests pass before submitting PR
- Update README for new features
- Follow semantic versioning

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Anthropic** for Claude API
- **Google** for Gemini API  
- **OpenAI** for GPT API
- **FastAPI** for the web framework
- **Docker** for containerization
- **PostgreSQL** for database support
- **Open Source Community** for various libraries and tools

## 📞 Support & Resources

### Documentation
- **Complete Documentation**: [docs/](docs/) directory
- **API Reference**: [docs/api_reference.md](docs/api_reference.md)
- **Architecture Guide**: [docs/architecture.md](docs/architecture.md)
- **Setup Guide**: [docs/setup_guide.md](docs/setup_guide.md)

### Quick Links
- **🚀 Live API Demo**: `http://localhost:8080/docs`
- **📊 System Status**: `http://localhost:8080/api/v1/status`
- **🔍 Health Check**: `http://localhost:8080/health`
- **📈 Analytics**: `http://localhost:8080/api/v1/analytics`

### Getting Help
- **📋 GitHub Issues**: [Create an issue](https://github.com/yourusername/agentic-ai-customer-support/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/yourusername/agentic-ai-customer-support/discussions)
- **📧 Email Support**: support@yourcompany.com

### Example Commands
```bash
# Quick health check
curl http://localhost:8080/health

# Process a query
curl -X POST http://localhost:8080/api/v1/queries \
  -H "Content-Type: application/json" \
  -d '{"query": "Help me", "customer_id": "test"}'

# View system metrics
curl http://localhost:8080/api/v1/analytics
```

---

**Made with ❤️ by the Agentic AI Team** | **[View on GitHub](https://github.com/yourusername/agentic-ai-customer-support)**
    "params": ["12345"]
})

# Publish to Kafka
await kafka_wrapper.call_tool("kafka-publish", {
    "topic": "customer-queries",
    "message": {"query": "How to reset password?", "customer_id": "12345"}
})

# Call AWS Lambda function
result = await aws_wrapper.call_tool("invoke_lambda", {
    "function_name": "process-customer-query",
    "payload": {"customer_id": "12345"}
})
```

---

    agent_id="query-agent-1", 
    agent_type="query",
    mcp_clients={"main": mcp_client}
)

knowledge_agent = A2AKnowledgeAgent(
    agent_id="knowledge-agent-1",
    agent_type="knowledge", 
    mcp_clients={"main": mcp_client}
)

response_agent = A2AResponseAgent(
    agent_id="response-agent-1",
    agent_type="response",
    mcp_clients={"main": mcp_client}
)

coordinator = A2ACoordinator()
```

---

# 🆕 Orchestrator Workflow with MCP Integration

The coordinator can orchestrate a workflow where each agent uses a different LLM provider/model, as configured globally or per-request:

```python
import asyncio
from a2a_protocol.a2a_coordinator import A2ACoordinator

async def run_workflow():
    coordinator = A2ACoordinator()
    workflow_data = {
        "task_type": "customer_support_workflow",
        "query_data": {
            "query": "How do I upgrade?",
            "customer_id": "12345",
            # Optionally specify LLM config per agent/task:
            "llm_provider": "openai",
            "llm_model": "gpt-3.5-turbo",
            "api_key": "<OPENAI_API_KEY>"
        }
    }
    result = await coordinator.process_task(workflow_data)
    print(result)

asyncio.run(run_workflow())
```

---

# 🆕 A2A Agent Usage Example

See `examples/a2a_usage_example.py` for a full example. Basic usage:

```python
from a2a_protocol.a2a_query_agent import A2AQueryAgent
from a2a_protocol.a2a_knowledge_agent import A2AKnowledgeAgent
from a2a_protocol.a2a_response_agent import A2AResponseAgent
from a2a_protocol.a2a_coordinator import A2ACoordinator

# Initialize agents (default: OpenAI, override as needed)
query_agent = A2AQueryAgent()
knowledge_agent = A2AKnowledgeAgent()
response_agent = A2AResponseAgent()
coordinator = A2ACoordinator()

# Example: process a query via the coordinator
import asyncio
async def run_workflow():
    workflow_data = {"task_type": "customer_support_workflow", "query_data": {"query": "How do I upgrade?", "customer_id": "12345"}}
    result = await coordinator.process_task(workflow_data)
    print(result)

asyncio.run(run_workflow())
```

---

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Database Schema](#database-schema)
- [Scripts](#scripts)
- [Docker Compose](#docker-compose)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

---

## 🛠 Installation

### Prerequisites

- Python 3.8+
- PostgreSQL
- Apache Kafka (optional - external MCP package available)
- Vector Database (Qdrant/Weaviate)
- API Keys for Claude, Gemini, and OpenAI
- uvx (recommended for external MCP package management)

### Quick Start

#### 🐳 Docker Deployment (Recommended)

**Full System:**
```bash
git clone https://github.com/yourusername/agentic-ai-customer-support.git
cd agentic-ai-customer-support

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Build and start all services
./docker.sh build
./docker.sh start

# Check status
./docker.sh status
```

**API Component Only (Lightweight):**
```bash
# For lightweight API-only deployment
./docker.sh api-build
./docker.sh api-start

# Check API status
./docker.sh api-status

# View API documentation
open http://localhost:8080/docs
```

#### 🔧 Local Development

```bash
git clone https://github.com/yourusername/agentic-ai-customer-support.git
cd agentic-ai-customer-support

# Install core dependencies
pip install -e .

# Install external MCP packages
./scripts/install_external_mcp.sh

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python scripts/init_db.py

# Run the system
python main.py
```

### Detailed Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/agentic-ai-customer-support.git
   cd agentic-ai-customer-support
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # Core installation
   pip install -e .
   
   # Optional: Install with specific features
   pip install -e .[mcp]           # MCP communication
   pip install -e .[server]        # Web server
   pip install -e .[visualization] # Data visualization
   pip install -e .[all]           # All optional features
   
   # Development installation
   pip install -e .[dev]
   ```

4. **Install external MCP packages**
   ```bash
   # Automated installation
   ./scripts/install_external_mcp.sh
   
   # Manual installation
   uvx install postgres-mcp@git+https://github.com/crystaldba/postgres-mcp.git
   uvx install git+https://github.com/modelcontextprotocol/kafka-mcp.git
   uvx install awslabs.lambda-tool-mcp-server
   uvx install awslabs.core-mcp-server
   uvx install awslabs.aws-documentation-mcp-server
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your API keys and database configurations.

5. **Configure external MCP packages**
   ```bash
   # Copy MCP configuration template
   cp config/aws_mcp.env.example config/aws_mcp.env
   # Edit with your AWS credentials and preferences
   ```

6. **Initialize database**
   ```bash
   python scripts/init_db.py
   # Or use the provided SQL schema:
   psql -U <user> -d <db> -f data/postgres_schema.sql
   ```

7. **Seed database and generate sample data**
   ```bash
   python scripts/seed_db.py
   python data/generate_postgres_sample_data.py
   ```

8. **(Optional) Import/Export Data**
   ```bash
   python scripts/import_data.py
   python scripts/export_data.py
   ```

## ⚙️ Configuration

- All environment-specific settings are managed in `config/env_settings.py` and `.env`.
- External MCP packages configured in `config/aws_mcp.env` and similar files.
- Supports development, staging, and production environments.

### Main Configuration (`.env`)

```env
# AI Model API Keys
CLAUDE_API_KEY=your_claude_api_key
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=admin
DB_PASSWORD=password
DB_NAME=customer_support

# Kafka Configuration (optional - external MCP available)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPICS=customer-queries,feedback-events

# Vector Database
VECTOR_DB_HOST=localhost
VECTOR_DB_PORT=6333
VECTOR_DB_COLLECTION=knowledge_base

# Genetic Algorithm Settings
POPULATION_SIZE=20
MUTATION_RATE=0.1
CROSSOVER_RATE=0.8
MAX_GENERATIONS=100

# Environment
ENV=development  # or production, staging, etc.
```

### External MCP Configuration (`config/aws_mcp.env`)

```env
# AWS Credentials and Region
AWS_PROFILE=default
AWS_REGION=us-east-1

# AWS MCP Server Settings
AWS_MCP_USE_EXTERNAL=true
AWS_MCP_USE_UVX=true

# MCP Server Enablement
LAMBDA_TOOL_MCP_ENABLED=true
CORE_MCP_ENABLED=true
DOCUMENTATION_MCP_ENABLED=true

# Logging
FASTMCP_LOG_LEVEL=ERROR
```

### Installation Options

The system supports flexible installation options:

```bash
# Minimal installation (core only)
pip install -e .

# With MCP support
pip install -e .[mcp]

# With web server
pip install -e .[server]

# With data visualization
pip install -e .[visualization]

# With fallback implementations (if needed - deprecated)
pip install -e .[kafka-fallback,aws-fallback]

# Everything
pip install -e .[all]

# Development
pip install -e .[dev]
```

## 🚀 Usage

### Basic Usage

```python
from main import EnhancedGeneticAISupport

# Initialize the system
ai_support = EnhancedGeneticAISupport()

# Process a customer query
result = await ai_support.process_query({
    'query': 'I need help with my billing issue',
    'customer_id': '12345',
    'context': {'previous_queries': []}
})

print(result)
```

### Running the Server

```bash
python main.py --mode server --port 8000
```

### Training Mode

```bash
python main.py --mode train --generations 50
```

### API Usage

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I reset my password?",
    "customer_id": "12345"
  }'
```

## 🏗 Architecture

### System Overview

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   Data Sources  │    │  Agent Layer         │    │   Evolution     │
├─────────────────┤    ├──────────────────────┤    ├─────────────────┤
│ • RDBMS        │────▶│ • Enhanced Query     │────▶│ • Genetic       │
│ • PDF Docs     │    │   Agent (Claude+DB)  │    │   Algorithm     │
│ • Vector DB    │    │ • Knowledge Agent    │    │ • Fitness       │
│ • Kafka Topics │    │   (Gemini+DB)        │    │   Evaluation    │
│ • Postgres     │    │ • Response Agent     │    │ • Evolution     │
└─────────────────┘    │   (GPT)              │    │   Engine        │
                      └──────────────────────┘    └─────────────────┘
```

### Agent Workflow

1. **Enhanced Query Agent** (Claude+DB): Analyzes and classifies queries with database context
2. **Knowledge Agent** (Gemini+DB): Retrieves and synthesizes information from knowledge base and documents
3. **Response Agent** (GPT): Crafts customer responses
4. **Evolution Engine**: Improves agent strategies

### Project Structure

```
agentic-ai-customer-support/
├── main.py
├── config/
│   ├── env_settings.py  # Unified, environment-specific config
│   ├── aws_mcp.env     # External AWS MCP configuration
│   └── ...
├── core/
│   ├── evolution_engine.py
│   └── ...
├── agents/
│   ├── enhanced_query_agent.py
│   ├── knowledge_agent.py
│   ├── response_agent.py
│   └── ...
├── a2a_protocol/
│   ├── base_a2a_agent.py
│   ├── a2a_query_agent.py
│   ├── a2a_knowledge_agent.py
│   ├── a2a_response_agent.py
│   └── a2a_coordinator.py
├── data_sources/
│   ├── pdf_processor.py
│   ├── rdbms_connector.py
│   ├── vector_db_client.py
│   ├── kafka_consumer.py
│   └── ...
├── mcp/
│   ├── base_mcp_server.py      # Base class for wrappers
│   ├── postgres_mcp_wrapper.py # External Postgres MCP wrapper
│   ├── kafka_mcp_wrapper.py   # External Kafka MCP wrapper
│   ├── aws_mcp_wrapper.py     # External AWS MCP wrapper
│   ├── mcp_client.py          # MCP client manager
│   └── database_mcp_server.py # Internal database MCP server
├── scripts/
│   ├── init_db.py
│   ├── seed_db.py
│   ├── import_data.py
│   ├── export_data.py
│   ├── cleanup.py
│   ├── health_check.py
│   ├── install_external_mcp.sh
│   └── test_api.py
├── data/
│   ├── postgres_schema.sql  # Full Postgres schema
│   ├── generate_postgres_sample_data.py
│   └── ...
├── api/
│   ├── routes.py
│   ├── schemas.py
│   └── ...
├── examples/
│   ├── mcp_integration_example.py
│   ├── a2a_usage_example.py
│   └── ...
├── utils/
│   └── logger.py
└── ...
```

## 🛠 Scripts

- `scripts/init_db.py`: Initialize the database
- `scripts/seed_db.py`: Seed the database with sample data
- `scripts/import_data.py` / `scripts/export_data.py`: Import/export data
- `scripts/cleanup.py`: Clean up test or old data
- `scripts/health_check.py`: System and DB health checks
- `scripts/test_api.py`: Test API endpoints
- `scripts/install_external_mcp.sh`: Install external MCP packages
- `data/generate_postgres_sample_data.py`: Generate sample data for Postgres

## 🐳 Docker Compose

- Use `docker-compose.yml` to spin up the full stack (API, Postgres, Kafka, Vector DB, etc.)
- Example:
  ```bash
  docker-compose up -d
  docker-compose logs -f
  docker-compose down
  ```
- Edit `.env` and `docker-compose.yml` for your environment.

## 🗄 Database Schema

A full Postgres schema is provided in `data/postgres_schema.sql` for customer support, tickets, users, knowledge base, messages, and analytics. See the file for details and customization.

## 🏥 Health & Monitoring

- System and database health checks via `scripts/health_check.py` and dashboard
- Enhanced dashboard at `http://localhost:8000/dashboard` shows agent, system, and DB metrics

## 📚 Documentation

The system includes comprehensive documentation:

### Core Documentation
- `docs/README.md`: Overview and getting started
- `docs/architecture.md`: System architecture details
- `docs/setup_guide.md`: Detailed setup instructions
- `docs/api_reference.md`: API documentation

### MCP Integration Documentation
- `docs/mcp_integration.md`: Complete MCP integration guide
- `docs/EXTERNAL_POSTGRES_MCP.md`: PostgreSQL MCP server details
- `docs/EXTERNAL_KAFKA_MCP.md`: Kafka MCP server details  
- `docs/EXTERNAL_AWS_MCP.md`: AWS MCP server details

### Examples and Testing
- `examples/mcp_integration_example.py`: MCP usage examples
- `examples/a2a_usage_example.py`: A2A protocol examples
- Various test files demonstrating functionality

---

---

## 📚 API Documentation

### REST API Endpoints
#### Process Query
Content-Type: application/json

{
  "query": "string",
  "customer_id": "string",
  "context": object,
  "priority": "low|medium|high"
}
```

#### Get Agent Performance
```http
GET /api/agents/{agent_id}/performance
```

#### Trigger Evolution
```http
POST /api/evolution/trigger
Content-Type: application/json

{
  "generations": 10,
  "target_fitness": 0.95
}
```

#### Get System Status
```http
GET /api/status
```

### WebSocket API

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.send(JSON.stringify({
  'type': 'query',
  'data': {
    'query': 'How do I cancel my subscription?',
    'customer_id': '12345'
  }
}));
```

## ⚡️ Agent Prompt Templates

Each agent uses a prompt template tailored to its capability. Example for Query Agent:

- **analyze_query**: "You are an AI assistant. Analyze the following customer query and provide a structured analysis including intent, entities, sentiment, urgency, and language: ..."
- **classify_intent**: "Classify the intent of this customer query: ..."
- **extract_entities**: "Extract all relevant entities from this query: ..."
- ...and so on for all agent capabilities.

Knowledge and Response agents have similar templates for their respective tasks.

## 🧬 Genetic Algorithm Details

### Chromosome Structure

Each agent's strategy is encoded as a chromosome with the following genes:

**Query Agent (Claude)**:
- `confidence_threshold`: Minimum confidence for classifications
- `context_window_size`: Amount of context to consider
- `classification_detail_level`: Depth of analysis
- `include_sentiment`: Whether to analyze sentiment
- `extract_entities`: Whether to extract named entities
- `urgency_detection`: Whether to detect urgency levels

**Knowledge Agent (Gemini)**:
- `search_depth`: How deep to search for information
- `relevance_threshold`: Minimum relevance score
- `max_sources`: Maximum number of sources to use
- `synthesis_level`: Detail level of synthesis
- `fact_checking_enabled`: Whether to verify facts

**Response Agent (GPT)**:
- `tone`: Response tone (formal, friendly, casual)
- `length_preference`: Preferred response length
- `personalization_level`: How much to personalize
- `empathy_level`: Level of empathy in responses

### Fitness Function

```python
def calculate_fitness(agent):
    metrics = agent.performance_metrics
    
    success_rate = metrics['successful_responses'] / metrics['total_queries']
    response_time_score = 1.0 / (1.0 + metrics['average_response_time'])
    satisfaction_score = metrics['customer_satisfaction']
    
    fitness = (0.4 * success_rate + 
               0.3 * response_time_score + 
               0.3 * satisfaction_score)
    
    return fitness
```

### Evolution Process

1. **Initialize Population**: Create random strategies for each agent
2. **Evaluate Fitness**: Process queries and measure performance
3. **Selection**: Choose best performing strategies
4. **Crossover**: Combine successful strategies
5. **Mutation**: Introduce random variations
6. **Replace Population**: New generation replaces old
7. **Repeat**: Continue until convergence or max generations

## 🔧 Development

### Setting up Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
flake8 .
black .

# Type checking
mypy .
```

### Adding New Agents

1. Create new agent class inheriting from `BaseAgent`
2. Implement required methods: `update_strategy()`, `process_input()`
3. Define chromosome structure for the agent
4. Add agent to the evolution engine
5. Write tests for the new agent

Example:
```python
from agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "custom-model")
        self.strategy = {
            'param1': 0.5,
            'param2': True
        }
    
    def update_strategy(self, genes: Dict[str, Any]) -> None:
        self.strategy.update(genes)
    
    def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Your processing logic here
        return {'result': 'processed'}
```

### Adding New Data Sources

1. Create connector class in `data_sources/`
2. Implement connection and query methods
3. Add source to configuration
4. Update knowledge agent to use new source

## 📊 Monitoring and Metrics

### Built-in Metrics

- **Agent Performance**: Success rate, response time, customer satisfaction
- **System Metrics**: Throughput, latency, error rates
- **Evolution Metrics**: Fitness scores, generation progress
- **Business Metrics**: Customer satisfaction, resolution rates

### Monitoring Dashboard

Access the monitoring dashboard at `http://localhost:8000/dashboard`

Features:
- Real-time agent performance
- Evolution progress visualization
- System health monitoring
- Customer satisfaction trends

### Logging

```python
import logging
from utils.logger import setup_logger

logger = setup_logger('my_component')
logger.info('Processing started')
logger.error('Error occurred', extra={'customer_id': '12345'})
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agents.py

# Run with coverage
pytest --cov=.

# Run integration tests
pytest tests/test_integration.py -v
```

### Test Categories

- **Unit Tests**: Test individual components
- **Integration Tests**: Test component interactions
- **Performance Tests**: Test system performance
- **Genetic Algorithm Tests**: Test evolution logic

## 🚀 Deployment

### Docker Deployment

```bash
# Build image
docker build -t genetic-ai-support .

# Run container
docker run -p 8000:8000 --env-file .env genetic-ai-support
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Considerations

- Use environment-specific configurations
- Set up proper logging and monitoring
- Configure load balancing for high availability
- Implement proper security measures
- Set up backup and recovery procedures

## 🔒 Security

### API Security

- API key authentication
- Rate limiting
- Input validation and sanitization
- CORS configuration
- HTTPS enforcement

### Data Security

- Encryption at rest and in transit
- PII data handling
- Audit logging
- Access controls
- Data retention policies

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Contribution Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings
- Add unit tests
- Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Anthropic for Claude API
- Google for Gemini API
- OpenAI for GPT API
- Open source community for various libraries

## 📞 Support

- **Documentation**: Complete documentation in [docs/](docs/) directory
- **MCP Integration**: See [docs/mcp_integration.md](docs/mcp_integration.md) for detailed MCP usage
- **External MCP Guides**: Individual guides for each external MCP package in docs/
- **Examples**: Working examples in [examples/](examples/) directory  
- **Issues**: [GitHub Issues](https://github.com/yourusername/agentic-ai-customer-support/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/agentic-ai-customer-support/discussions)
- **Email**: support@yourcompany.com

### Quick Links
- [Migration Guide](docs/mcp_integration.md#migration-from-custom-mcp-servers)
- [External MCP Setup](scripts/install_external_mcp.sh)
- [MCP Integration Examples](examples/mcp_integration_example.py)
- [A2A Protocol Examples](examples/a2a_usage_example.py)

---

**Made with ❤️ by the Agentic AI Team**