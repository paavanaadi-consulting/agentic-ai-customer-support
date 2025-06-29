# API Testing Guide

This guide provides detailed instructions for testing the REST and WebSocket APIs of the Agentic AI Customer Support system.

## 1. Prerequisites

- The application must be running, either locally (`python main.py --mode server`) or via Docker (`docker-compose up`).
- **`curl`**: A command-line tool for making HTTP requests.
- **`websocat`** or a similar WebSocket client for testing the WebSocket API.
- A REST client like Postman or Insomnia can also be used for easier testing.

## 2. Running the API Server

### Local Development

Start the FastAPI server from the project root:

```bash
python main.py --mode server --port 8000
```

The API will be available at `http://localhost:8000`.

### Docker Environment

If you are using Docker, the API is exposed as part of the `agentic-ai-customer-support` service.

```bash
docker-compose up -d
```

The API will be available at `http://localhost:8000`.

## 3. REST API Endpoint Testing

The following sections detail how to test each REST endpoint using `curl`.

### Health Check

This endpoint is used to verify that the API server is running and healthy.

**Endpoint**: `GET /api/status`

**Command**:
```bash
curl -X GET http://localhost:8000/api/status
```

**Expected Response**:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "..."
}
```

### Process a Customer Query

This is the primary endpoint for submitting a customer query to the A2A workflow.

**Endpoint**: `POST /api/query`

**Command**:
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I reset my password?",
    "customer_id": "cust_12345",
    "context": {
      "channel": "live_chat"
    }
  }'
```

**Expected Response**:
A successful response will contain the result from the `A2ACoordinator`, including the generated response and analysis from each agent.

```json
{
  "workflow_id": "...",
  "success": true,
  "query_analysis": { ... },
  "knowledge_result": { ... },
  "response_result": {
    "response_text": "To reset your password, please visit our login page and click 'Forgot Password'...",
    ...
  },
  "total_agents_used": 3,
  "coordination_overhead": "minimal"
}
```

### Get Agent Performance

This endpoint retrieves performance metrics for a specific agent.

**Endpoint**: `GET /api/agents/{agent_id}/performance`

**Command**:
```bash
# Replace 'query-agent-1' with a valid agent ID
curl -X GET http://localhost:8000/api/agents/query-agent-1/performance
```

### Trigger Evolution Engine

This endpoint manually triggers the genetic algorithm to evolve agent strategies.

**Endpoint**: `POST /api/evolution/trigger`

**Command**:
```bash
curl -X POST http://localhost:8000/api/evolution/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "generations": 5,
    "target_fitness": 0.9
  }'
```

## 4. WebSocket API Testing

The WebSocket API provides a real-time, bi-directional communication channel.

**Endpoint**: `ws://localhost:8000/ws`

You can use a command-line tool like `websocat` to test it.

**Command**:
```bash
# Install websocat: brew install websocat
websocat ws://localhost:8000/ws
```

Once connected, you can send a JSON message to initiate a query:
```json
{
  "type": "query",
  "data": {
    "query": "How do I cancel my subscription?",
    "customer_id": "cust_67890"
  }
}
```
The server will push back status updates and the final response over the same connection.

## 5. Automated API Testing

The repository includes a script to run automated tests against the API endpoints.

**Script**: `scripts/test_api.py`

**Command**:
Ensure the server is running, then execute:
```bash
python scripts/test_api.py
```
This script will make requests to the various endpoints and validate the responses, providing a quick way to check for regressions.