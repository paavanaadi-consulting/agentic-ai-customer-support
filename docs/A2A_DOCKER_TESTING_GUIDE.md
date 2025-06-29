# A2A Protocol Docker Testing Guide

This guide provides specific instructions for testing the `a2a_protocol` module within the fully containerized Docker environment. This ensures that the agent-to-agent communication works correctly with all its live dependencies, such as PostgreSQL and Kafka, running as separate services.

## Step 1: Set Up and Start the Docker Environment

First, ensure the entire application stack is running. If you haven't already, follow these steps from the main Docker Testing Guide:

1.  **Clone the repository** and navigate into the project directory.
2.  **Configure environment variables** by copying `.env.example` to `.env`.
    ```bash
    cp .env.example .env
    # (Optional) Edit .env to add real API keys for full functionality
    ```
3.  **Build and start all services** using Docker Compose.
    ```bash
    docker-compose up --build -d
    ```
4.  **Verify all services are running** and healthy.
    ```bash
    docker-compose ps
    ```
    Wait a minute or two for all services, especially `kafka` and `postgres`, to initialize. You can monitor their startup progress with `docker-compose logs -f`.

## Step 2: Run Automated Tests for the A2A Protocol

Once the environment is running, you can execute tests that specifically target the A2A protocol. These commands should be run from your host machine's terminal.

### Method 1: Using the Dedicated A2A Test Script (Recommended)

The repository includes a script designed for testing the A2A module. Running it inside the `api` container allows it to connect to the other running services (Postgres, Kafka) as if they were external MCPs.

```bash
docker-compose exec agentic-ai-customer-support python scripts/test_a2a_local.py --use-external-mcp
```

**What this command does:**
- `docker-compose exec agentic-ai-customer-support`: Executes a command inside the main application container (named `agentic-ai-customer-support` in `docker-compose.yml`).
- `python scripts/test_a2a_local.py`: Runs the A2A local testing script.
- `--use-external-mcp`: This crucial flag tells the script to connect to the MCP services (which are the other Docker containers) over the network, providing a true integration test.

The output will show the results of the test scenarios, confirming that the agents within the `a2a_protocol` can coordinate and function correctly with live backing services.

### Method 2: Using `pytest` with a Keyword Filter

You can also use `pytest` to run any unit or integration tests that are specifically tagged or named for the A2A protocol.

```bash
docker-compose exec agentic-ai-customer-support pytest -k "a2a" -v
```

This command will find and execute any test functions, classes, or files with "a2a" in their name. This is a great way to run a targeted subset of the full test suite.

## Step 3: Manual and Interactive Testing (for Debugging)

For more in-depth debugging, you can run the A2A agents manually inside the container and interact with them. This is an advanced technique that requires multiple terminal windows.

1.  **Open a shell inside the `api` container:**
    ```bash
    docker-compose exec agentic-ai-customer-support /bin/bash
    ```

2.  **From inside the container's shell, start the agents.** The `A2A_LOCAL_TESTING.md` guide provides one-liners for this. You would run each command in a separate terminal session attached to the container.

    *   **Terminal 1 (Start Query Agent):**
        ```bash
        # Inside the container shell
        python -c "import asyncio; from a2a_protocol.a2a_query_agent import A2AQueryAgent; asyncio.run(A2AQueryAgent('query-agent-1').start())"
        ```
    *   **Terminal 2 (Start Knowledge Agent):**
        ```bash
        # Get another shell: docker-compose exec agentic-ai-customer-support /bin/bash
        python -c "import asyncio; from a2a_protocol.a2a_knowledge_agent import A2AKnowledgeAgent; asyncio.run(A2AKnowledgeAgent('knowledge-agent-1').start())"
        ```
    *   **Terminal 3 (Start Response Agent):**
        ```bash
        # Get another shell: docker-compose exec agentic-ai-customer-support /bin/bash
        python -c "import asyncio; from a2a_protocol.a2a_response_agent import A2AResponseAgent; asyncio.run(A2AResponseAgent('response-agent-1').start())"
        ```

3.  **Terminal 4 (Send a Test Message):**
    Now, send a WebSocket message to the Query Agent to kick off the workflow.
    ```bash
    # Get another shell: docker-compose exec agentic-ai-customer-support /bin/bash
    python -c "import asyncio, websockets, json; \
    async def send_test(): \
        uri = 'ws://localhost:8101'; \
        async with websockets.connect(uri) as websocket: \
            message = {'message_id': 'test-1', 'sender_id': 'test-client', 'receiver_id': 'query-agent-1', 'message_type': 'customer_query', 'payload': {'query': 'How do I reset my password?', 'customer_id': 'test_customer_12345'}}; \
            await websocket.send(json.dumps(message)); \
            response = await websocket.recv(); \
            print(f'Response: {response}'); \
    asyncio.run(send_test())"
    ```

4.  **Monitor the logs** in another terminal to see the agents communicating with each other:
    ```bash
    docker-compose logs -f agentic-ai-customer-support
    ```

This comprehensive approach allows you to run both automated and manual tests on the `a2a_protocol` within a realistic, containerized environment, ensuring its robustness and integration with the rest of the system.