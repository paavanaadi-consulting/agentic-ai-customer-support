# Agentic AI Customer Support System

A sophisticated multi-agent AI system that evolves and adapts to provide better customer service through agentic workflows, genetic algorithms, and advanced database integration. The system features comprehensive **Model Context Protocol (MCP)** integration using external MCP servers for scalable, maintainable data and service access.

## 🚀 Features

- **External MCP Integration**: Uses official AWS Labs and community MCP servers instead of custom implementations
- **A2A (Agent-to-Agent) Protocol**: Modular agents communicate via a decoupled orchestration protocol for maximum scalability and flexibility.
- **Multi-Agent Architecture**: Modular agents (Claude, Gemini, GPT) with database context
- **Dynamic LLM Selection**: Agents can use OpenAI, Gemini, or Claude LLMs, with provider/model/API key set via config or per-request
- **Genetic Algorithm Evolution**: Agents evolve strategies for better performance
- **Multiple Data Sources**: RDBMS, PDF documents, Vector DB, Kafka streams
- **Full Database Integration**: Postgres schema for tickets, users, knowledge base, and analytics
- **Unified Environment Config**: All settings via `config/settings.py` and `.env`
- **Asynchronous Processing**: Built on `asyncio` for high-performance, real-time query handling.
- **Performance Monitoring**: Built-in metrics, fitness evaluation, and health checks
- **Enhanced Dashboard**: Customer and agent analytics, satisfaction trends, database health
- **Extensible Scripts**: For DB initialization, seeding, import/export, health checks, and more

---

## 🔧 Model Context Protocol (MCP) Architecture

The system uses external MCP servers through wrapper interfaces for modular service access:

### External MCP Packages
- **PostgreSQL**: `postgres-mcp` package from community (crystaldba/postgres-mcp)
- **Kafka**: `kafka-mcp` package from official Model Context Protocol organization (modelcontextprotocol/kafka-mcp)
- **AWS Services**: AWS Labs MCP packages (lambda-tool, core, documentation servers)

### MCP Wrappers
- **Postgres MCP Wrapper** (`mcp/postgres_mcp_wrapper.py`): External postgres-mcp package integration
- **Kafka MCP Wrapper** (`mcp/kafka_mcp_wrapper.py`): External kafka-mcp integration with fallback
- **AWS MCP Wrapper** (`mcp/aws_mcp_wrapper.py`): External AWS MCP packages integration

### MCP Client Manager
- **MCP Client** (`mcp/mcp_client.py`): Unified interface for MCP server communication
- **Base MCP Server** (`mcp/base_mcp_server.py`): Common base class for wrappers

### Quick MCP Example
```python
from mcp.postgres_mcp_wrapper import PostgresMCPWrapper
from mcp.kafka_mcp_wrapper import KafkaMCPWrapper, ExternalKafkaMCPConfig
from mcp.aws_mcp_wrapper import AWSMCPWrapper, ExternalMCPConfig

# Initialize MCP wrappers with external packages
db_wrapper = PostgresMCPWrapper("postgresql://user:pass@localhost:5432/db")
await db_wrapper.initialize()

kafka_config = ExternalKafkaMCPConfig(
    bootstrap_servers="localhost:9092",
    topic_name="customer-queries"
)
kafka_wrapper = KafkaMCPWrapper(kafka_config)
await kafka_wrapper.initialize()

aws_config = ExternalMCPConfig(
    aws_profile="default",
    aws_region="us-east-1"
)
aws_wrapper = AWSMCPWrapper(aws_config)
await aws_wrapper.initialize()

# Use MCP tools through wrappers
customer_data = await db_wrapper.call_tool("query", {
    "sql": "SELECT * FROM customers WHERE customer_id = %s",
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