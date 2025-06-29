# Comprehensive Docker Testing Guide

This guide provides step-by-step instructions for setting up, testing, and interacting with the complete Agentic AI Customer Support system using Docker and Docker Compose. This is the recommended method for a full-stack testing experience that mirrors a production-like environment.

## 1. Prerequisites

Before you begin, ensure you have the following installed on your system:
- **Docker**: [Get Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: Usually included with Docker Desktop.
- **Git**: For cloning the repository.
- **API Keys**: (Optional but recommended for full functionality) API keys for OpenAI, Gemini, and/or Claude.

## 2. Quick Start (10-15 minutes)

Follow these steps to get the entire system running quickly.

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/agentic-ai-customer-support.git
cd agentic-ai-customer-support
```

### Step 2: Configure Environment Variables

Copy the example environment file. This file contains all the necessary configurations for the Docker services.

```bash
cp .env.example .env
```

Next, open the `.env` file and edit the settings. At a minimum, you should review the `PostgreSQL` credentials. For full agent functionality, add your LLM API keys.

```bash
# Open .env in your favorite editor
nano .env
```

### Step 3: Build and Start All Services

Use Docker Compose to build the images and start all the containers in detached mode.

```bash
# This command will build the 'api' image and pull images for Postgres, Kafka, etc.
docker-compose up --build -d
```

### Step 4: Verify Services are Running

Check the status of all running containers. You should see services like `api`, `postgres`, `kafka`, `zookeeper`, and `qdrant` with a `running` or `up` status.

```bash
docker-compose ps
```

It might take a minute or two for all services, especially Kafka, to become fully healthy. You can monitor the logs to see their progress:

```bash
docker-compose logs -f
```
Press `Ctrl+C` to exit the logs.

### Step 5: Run the Test Suite

Once all services are running, you can execute the entire test suite inside the `api` container.

```bash
docker-compose exec api pytest -v
```

You should see the test results printed to your console.

## 3. Docker Architecture Overview

The `docker-compose.yml` file defines the following services:

- **`api`**: The main application container running the FastAPI server, all agents (Query, Knowledge, Response), the A2A Coordinator, and the MCP server wrappers.
- **`postgres`**: The PostgreSQL database for storing all application data (customers, tickets, knowledge base, etc.).
- **`zookeeper`**: A required dependency for Kafka.
- **`kafka`**: The message broker for asynchronous communication and event streaming.
- **`qdrant`**: The vector database used for similarity searches in the knowledge base.
- **`redis`**: (If configured) Used for caching and session management.

The containers are connected via a custom Docker network, allowing them to communicate with each other using their service names (e.g., the `api` service can reach the database at `postgres:5432`).

## 4. Detailed Testing Procedures

You can run various tests by executing commands inside the `api` container.

### Running the Full Test Suite

This is the most common command to validate the entire application.

```bash
docker-compose exec api pytest -v --tb=short
```

### Running Specific Test Files or Folders

To run tests for a specific part of the application, provide the path.

```bash
# Run only the agent tests
docker-compose exec api pytest tests/test_agents.py

# Run only the MCP server tests
docker-compose exec api pytest tests/mcp_servers/
```

### Running Tests Matching a Keyword

Use the `-k` flag to run tests whose names match a specific string.

```bash
# Run all tests related to "kafka"
docker-compose exec api pytest -k "kafka" -v

# Run tests related to the A2A protocol
docker-compose exec api pytest -k "a2a" -v
```

### Running the A2A Local Test Script

The `test_a2a_local.py` script can be run inside the Docker environment to test the full pipeline with external MCPs (which are the other Docker containers).

```bash
docker-compose exec api python scripts/test_a2a_local.py --use-external-mcp
```

## 5. Interacting with Services Manually

You can directly interact with each service for debugging or manual verification.

### Accessing the API Container Shell

To get an interactive shell inside the `api` container:

```bash
docker-compose exec api /bin/bash
```
From here, you can run any Python script or command.

### Connecting to the PostgreSQL Database

You can connect to the running PostgreSQL instance using `psql`. The credentials are from your `.env` file.

```bash
# The default user is 'admin' and database is 'customer_support'
docker-compose exec postgres psql -U admin -d customer_support
```

Once connected, you can run SQL queries:

```sql
-- List all tables
\dt;

-- See the first 5 customers
SELECT * FROM customers LIMIT 5;

-- Exit psql
\q
```

### Interacting with Kafka

You can use the Kafka command-line tools available in the `kafka` container.

```bash
# List all topics in the Kafka cluster
docker-compose exec kafka /opt/bitnami/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# Watch messages on a specific topic (e.g., customer-queries)
docker-compose exec kafka /opt/bitnami/kafka/bin/kafka-console-consumer.sh \
    --topic customer-queries \
    --from-beginning \
    --bootstrap-server localhost:9092
```

## 6. Monitoring and Logging

### View Logs for All Services

To see a continuous stream of logs from all running containers:

```bash
docker-compose logs -f
```

### View Logs for a Single Service

To isolate logs for a specific service, like the `api`:

```bash
docker-compose logs -f api
```

## 7. Troubleshooting

### Port Conflicts
If a service fails to start, it might be because a port is already in use on your host machine. Check the `ports` section in `docker-compose.yml` and ensure they are free.

### Build Issues
If you encounter issues during the build process, try building without the cache.
```bash
docker-compose build --no-cache
```

### Data Issues
If you want to start with a completely fresh database, you need to remove the Docker volume associated with PostgreSQL.
```bash
docker-compose down -v
```
**Warning**: This will permanently delete all data in your database.

## 8. Cleaning Up

### Stop All Services

To stop all running containers without deleting any data:

```bash
docker-compose down
```

### Stop and Remove Everything

To stop containers AND remove all associated volumes (deleting all data) and networks:

```bash
docker-compose down -v
```