# System Architecture

The Agentic AI Customer Support System is a modular, multi-agent platform designed for scalable, intelligent customer support.

## Main Components
- **API Layer**: Exposes endpoints for client interaction.
- **Agents**: Specialized AI agents for query analysis, knowledge retrieval, and response generation.
- **Evolution Engine**: Manages genetic optimization of agent strategies.
- **Data Sources**: Connectors for RDBMS, vector DB, PDF, and Kafka.
- **MCP Servers**: Integrations for Postgres, AWS, Kafka, etc.

## Data Flow
1. API receives a customer query.
2. Query is processed by agents in sequence.
3. Data sources are used for retrieval and storage.
4. MCP servers handle messaging and integration.
5. Evolution engine optimizes agent strategies over time.
