# ⚡️ A2A Protocol Migration Notice

**This project now uses an Agent-to-Agent (A2A) protocol for all agent communication.**

- All new development must use the agents in `a2a_protocol/`.
- Legacy agents in `agents/` are deprecated and remain as stubs for backward compatibility.
- See `examples/a2a_usage_example.py` for usage of the new A2A system.

---

# Agentic AI Customer Support System

A sophisticated multi-agent AI system that evolves and adapts to provide better customer service through agentic workflows, genetic algorithms, and advanced database integration.

## 🚀 Features

- **A2A Protocol**: Modular agents communicate directly via WebSockets for scalable, decoupled orchestration
- **Multi-Agent Architecture**: Modular agents (Claude, Gemini, GPT) with database context
- **Dynamic LLM Selection**: Agents can use OpenAI, Gemini, or Claude LLMs, with provider/model/API key set via config or per-request
- **Genetic Algorithm Evolution**: Agents evolve strategies for better performance
- **Multiple Data Sources**: RDBMS, PDF documents, Vector DB, Kafka streams
- **MCP Server Integration**: Extensible server communication protocol
- **Full Database Integration**: Postgres schema for tickets, users, knowledge base, and analytics
- **Unified Environment Config**: All settings via `config/settings.py` and `.env`
- **Real-time Processing**: Asynchronous processing of customer queries
- **Performance Monitoring**: Built-in metrics, fitness evaluation, and health checks
- **Enhanced Dashboard**: Customer and agent analytics, satisfaction trends, database health
- **Extensible Scripts**: For DB initialization, seeding, import/export, health checks, and more

---

## 🆕 Key Updates (2025)

- **All agents now support dynamic LLM selection (OpenAI, Gemini, Claude) for all LLM operations.**
- **Prompt templates are used for each agent capability (intent, knowledge, response, etc).**
- **All A2A agents accept `mcp_clients` for context-aware LLM prompting (Postgres, Kafka, AWS, etc).**
- **Legacy agents are fully deprecated; only use `a2a_protocol/` agents.**
- **See `examples/a2a_usage_example.py` for modern usage.**

---

# 🆕 A2A Agent Initialization Example (Multi-LLM)

```python
from a2a_protocol.a2a_query_agent import A2AQueryAgent
from a2a_protocol.a2a_knowledge_agent import A2AKnowledgeAgent
from a2a_protocol.a2a_response_agent import A2AResponseAgent
from a2a_protocol.a2a_coordinator import A2ACoordinator

# Pass API key, LLM provider/model, and MCP clients for context
query_agent = A2AQueryAgent(api_key="<OPENAI_API_KEY>", llm_provider="openai", llm_model="gpt-3.5-turbo", mcp_clients=mcp_clients)
knowledge_agent = A2AKnowledgeAgent(api_key="<GEMINI_API_KEY>", llm_provider="gemini", llm_model="gemini-pro", mcp_clients=mcp_clients)
response_agent = A2AResponseAgent(api_key="<CLAUDE_API_KEY>", llm_provider="claude", llm_model="claude-3-opus-20240229", mcp_clients=mcp_clients)
coordinator = A2ACoordinator()
```

---

# 🆕 Orchestrator Workflow Example (Dynamic LLM)

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

## 🛠 Installation

### Prerequisites

- Python 3.8+
- PostgreSQL
- Apache Kafka
- Vector Database (Qdrant/Weaviate)
- API Keys for Claude, Gemini, and OpenAI

### Quick Start

```bash
git clone https://github.com/yourusername/agentic-ai-customer-support.git
cd agentic-ai-customer-support
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
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
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your API keys and database configurations.

5. **Initialize database**
   ```bash
   python scripts/init_db.py
   # Or use the provided SQL schema:
   psql -U <user> -d <db> -f data/postgres_schema.sql
   ```

6. **Seed database and generate sample data**
   ```bash
   python scripts/seed_db.py
   python data/generate_postgres_sample_data.py
   ```

7. **(Optional) Import/Export Data**
   ```bash
   python scripts/import_data.py
   python scripts/export_data.py
   ```

## ⚙️ Configuration

- All environment-specific settings are managed in `config/env_settings.py` and `.env`.
- Supports development, staging, and production environments.

Create a `.env` file with the following variables:

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

# Kafka Configuration
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
│   └── ...
├── core/
│   ├── evolution_engine.py
│   └── ...
├── agents/
│   ├── enhanced_query_agent.py
│   ├── knowledge_agent.py
│   ├── response_agent.py
│   └── ...
├── data_sources/
│   ├── pdf_processor.py
│   ├── rdbms_connector.py
│   ├── vector_db_client.py
│   ├── kafka_consumer.py
│   └── ...
├── mcp_servers/
│   ├── postgres_mcp.py
│   ├── aws_mcp.py
│   ├── kafka_mcp.py
│   └── ...
├── scripts/
│   ├── init_db.py
│   ├── seed_db.py
│   ├── import_data.py
│   ├── export_data.py
│   ├── cleanup.py
│   ├── health_check.py
│   └── test_api.py
├── data/
│   ├── postgres_schema.sql  # Full Postgres schema
│   ├── generate_postgres_sample_data.py
│   └── ...
├── api/
│   ├── routes.py
│   ├── schemas.py
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

## 📚 API Documentation

### REST API Endpoints

#### Process Query
```http
POST /api/query
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

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/agentic-ai-customer-support/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/agentic-ai-customer-support/discussions)
- **Email**: support@yourcompany.com

---

**Made with ❤️ by the Agentic AI Team**