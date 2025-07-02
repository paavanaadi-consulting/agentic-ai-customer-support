#!/bin/bash
# Stop all Docker services for Agentic AI Customer Support

set -e

echo "🛑 Stopping Agentic AI Customer Support Services..."

# Change to cicd directory (we're already in scripts subfolder)
cd "$(dirname "$0")/.."

echo "📊 Current service status:"
docker-compose ps

echo ""
echo "🔄 Stopping services gracefully..."

# Stop application services first
echo "🎪 Stopping Main Application..."
docker-compose stop main-app

echo "🌐 Stopping API Service..."
docker-compose stop api-service

echo "🧠 Stopping Agents Service..."
docker-compose stop agents-service

echo "🤖 Stopping MCP Services..."
# Stop Database and Kafka MCP services
docker-compose stop mcp-postgres mcp-kafka

# Stop AWS MCP services using dedicated script
echo "☁️ Stopping AWS MCP services..."
./main/aws-mcp.sh stop

echo "🏗️ Stopping Infrastructure Services..."
docker-compose stop kafka zookeeper qdrant redis postgres

echo "🧹 Stopping Kafka Init Container..."
docker-compose stop kafka-init

echo "✅ All services stopped!"

# Show final status
echo "📊 Final Status:"
docker-compose ps

echo ""
echo "🔄 To restart: ./scripts/start-all.sh"
echo "🗑️  To cleanup: ./scripts/cleanup-all.sh"
