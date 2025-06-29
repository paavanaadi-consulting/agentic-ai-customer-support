# Guide: Testing the API Component in Docker

This guide provides step-by-step instructions for testing the API component within the fully containerized Docker environment. This approach ensures the API functions correctly with all its live backing services, such as the database, Kafka, and various MCP servers.

## Step 1: Start the Docker Environment

First, ensure the entire application stack is running. If you haven't already, navigate to the project root and use Docker Compose to build and start all services in detached mode.

```bash
# From your project's root directory
docker-compose up --build -d
```

Verify that all containers, especially `agentic-ai-customer-support`, `postgres`, and `kafka`, are running and healthy.

```bash
docker-compose ps
```

## Step 2: Run Automated API Tests with `pytest`

The most comprehensive way to test the API is by running its integration tests. These tests are designed to validate the API endpoints and their interaction with the rest of the system.

Execute the `pytest` command inside the running `agentic-ai-customer-support` container. You can target specific API test files if they are organized in a dedicated directory (e.g., `tests/api/`).

```bash
# Execute pytest inside the 'agentic-ai-customer-support' container
docker-compose exec agentic-ai-customer-support pytest tests/api/ -v
```

If the API tests are not in a separate folder, you can run all tests or filter them by a keyword:

```bash
# Run all tests
docker-compose exec agentic-ai-customer-support pytest -v

# Run only tests with "api" in their name
docker-compose exec agentic-ai-customer-support pytest -k "api" -v
```

This approach tests the API in a live, containerized environment, providing the highest level of confidence.

## Step 3: Manual Testing with `curl`

You can manually send requests to the API from your host machine's terminal using a tool like `curl`. Since the `agentic-ai-customer-support` service exposes port `8000`, the API is accessible at `http://localhost:8000`.

Here are some example commands from the `API_TESTING_GUIDE.md`:

**Check the Health Status:**

```bash
curl -X GET http://localhost:8000/api/status
```

**Submit a Customer Query:**

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

This method is excellent for quick, ad-hoc testing and debugging of specific endpoints.

## Step 4: Using the Dedicated API Test Script

The repository includes a simple script, `scripts/test_api.py`, for a quick check of the primary `/api/query` endpoint. You can run this script inside the container.

```bash
docker-compose exec agentic-ai-customer-support python scripts/test_api.py
```

This will send a predefined query to the API and print the status code and response, serving as a quick sanity check that the main workflow is operational.