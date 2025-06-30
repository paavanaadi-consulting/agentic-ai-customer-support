#!/bin/bash
# Start all Docker services for Agentic AI Customer Support

set -e

echo "🚀 Starting Agentic AI Customer Support Services..."

# Change to cicd directory (we're already in scripts subfolder)
cd "$(dirname "$0")/.."

# Create logs directory if it doesn't exist
mkdir -p ../logs

echo "🏁 Starting infrastructure services first..."

# Start infrastructure services first
docker-compose up -d postgres redis qdrant zookeeper kafka

echo "⏳ Waiting for infrastructure services to be ready..."
sleep 15

echo "🎯 Starting Kafka initialization..."
docker-compose up -d kafka-init

echo "⏳ Waiting for Kafka topics to be created..."
sleep 10

echo "🤖 Starting MCP services..."
docker-compose up -d mcp-database mcp-kafka mcp-kafka-wrapper mcp-aws

echo "⏳ Waiting for MCP services to be ready..."
sleep 10

echo "🧠 Starting Agents service..."
docker-compose up -d agents-service

echo "🌐 Starting API service..."
docker-compose up -d api-service

echo "🎪 Starting Main Application..."
docker-compose up -d main-app

echo "⏳ Waiting for all services to be ready..."
sleep 15

echo "✅ All services started!"

# Show status
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🌐 Service Endpoints:"
echo "  • Main App:      http://localhost:8000"
echo "  • API Service:   http://localhost:8080"
echo "  • Agents:        http://localhost:8005"
echo "  • Qdrant UI:     http://localhost:6333/dashboard"
echo "  • PostgreSQL:    localhost:5432"
echo ""
echo "🔍 Health Checks:"
echo "  • Main App:      curl http://localhost:8000/health"
echo "  • API Service:   curl http://localhost:8080/health"
echo "  • Agents:        curl http://localhost:8005/health"
echo ""
echo "📋 To view logs: docker-compose logs -f [service-name]"
echo "🛑 To stop all:  ./scripts/stop-all.sh"
