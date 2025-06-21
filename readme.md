# Genetic AI Customer Support System

A sophisticated multi-agent AI system that evolves and adapts to provide better customer service through genetic algorithms.

## 🚀 Features

- **Multi-Agent Architecture**: Three specialized AI agents (Claude, Gemini, GPT)
- **Genetic Algorithm Evolution**: Agents evolve strategies for better performance
- **Multiple Data Sources**: RDBMS, PDF documents, Vector DB, Kafka streams
- **MCP Server Integration**: Extensible server communication protocol
- **Real-time Processing**: Asynchronous processing of customer queries
- **Performance Monitoring**: Built-in metrics and fitness evaluation

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
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
git clone https://github.com/yourusername/genetic-ai-customer-support.git
cd genetic-ai-customer-support
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python main.py
```

### Detailed Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/genetic-ai-customer-support.git
   cd genetic-ai-customer-support
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
   python scripts/init_database.py
   ```

## ⚙️ Configuration

### Environment Variables

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
```

## 🚀 Usage

### Basic Usage

```python
from main import GeneticAISupport

# Initialize the system
ai_support = GeneticAISupport()

# Process a customer query
result = ai_support.process_query({
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
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │  Agent Layer    │    │   Evolution     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • RDBMS        │────▶│ • Query Agent   │────▶│ • Genetic       │
│ • PDF Docs     │    │   (Claude)      │    │   Algorithm     │
│ • Vector DB    │    │ • Knowledge     │    │ • Fitness       │
│ • Kafka Topics │    │   Agent (Gemini)│    │   Evaluation    │
└─────────────────┘    │ • Response      │    │ • Evolution     │
                       │   Agent (GPT)   │    │   Engine        │
                       └─────────────────┘    └─────────────────┘
```

### Agent Workflow

1. **Query Agent** (Claude): Analyzes and classifies incoming queries
2. **Knowledge Agent** (Gemini): Retrieves and synthesizes relevant information
3. **Response Agent** (GPT): Crafts appropriate customer responses
4. **Evolution Engine**: Continuously improves agent strategies

### Project Structure

```
genetic-ai-customer-support/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
├── setup.py
├── main.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── mcp_config.py
├── core/
│   ├── __init__.py
│   ├── genetic_algorithm.py
│   ├── fitness_evaluator.py
│   └── evolution_engine.py
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── query_agent.py
│   ├── knowledge_agent.py
│   └── response_agent.py
├── data_sources/
│   ├── __init__.py
│   ├── rdbms_connector.py
│   ├── pdf_processor.py
│   ├── vector_db_client.py
│   └── kafka_consumer.py
├── mcp_servers/
│   ├── __init__.py
│   ├── mcp_client.py
│   └── server_manager.py
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   ├── metrics.py
│   └── helpers.py
├── api/
│   ├── __init__.py
│   ├── routes.py
│   └── middleware.py
├── scripts/
│   ├── init_database.py
│   ├── migrate.py
│   └── benchmark.py
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_genetic_algorithm.py
│   ├── test_data_sources.py
│   └── test_integration.py
├── docs/
│   ├── api.md
│   ├── configuration.md
│   └── development.md
└── examples/
    ├── basic_usage.py
    ├── custom_agent.py
    └── training_example.py
```

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
- **Issues**: [GitHub Issues](https://github.com/yourusername/genetic-ai-customer-support/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/genetic-ai-customer-support/discussions)
- **Email**: support@yourcompany.com

## 🗺 Roadmap

### Version 1.1
- [ ] Advanced fitness functions
- [ ] Multi-objective optimization
- [ ] Custom agent plugins
- [ ] Enhanced monitoring dashboard

### Version 1.2
- [ ] Distributed processing
- [ ] Advanced ML integration
- [ ] Real-time adaptation
- [ ] Customer feedback loops

### Version 2.0
- [ ] Neural architecture search
- [ ] AutoML integration
- [ ] Advanced NLP capabilities
- [ ] Predictive analytics

---

**Made with ❤️ by the Genetic AI Team**