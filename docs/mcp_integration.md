# MCP Server Integrations

## Supported MCPs
- **Postgres MCP**: Uses PostgreSQL for message queueing and control.
- **AWS MCP**: Integrates with AWS SQS/SNS for messaging.
- **Kafka MCP**: Uses Apache Kafka for event streaming.

## Base Interface
All MCPs implement a common interface with methods:
- `connect()`
- `send(data)`
- `receive()`
- `close()`

## Adding a New MCP
1. Subclass `BaseMCP` in `mcp_servers/`.
2. Implement the required methods.
3. Register with the server manager if needed.
