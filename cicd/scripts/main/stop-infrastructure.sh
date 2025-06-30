#!/bin/bash
# Stop infrastructure services

set -e

echo "🛑 Stopping Infrastructure Services..."

# Change to cicd directory (we're already in scripts subfolder)
cd "$(dirname "$0")/.."

echo "📊 Current infrastructure status:"
docker-compose ps postgres redis qdrant kafka zookeeper kafka-init

echo ""
echo "🔄 Stopping infrastructure services..."

# Stop infrastructure services
docker-compose stop kafka-init kafka zookeeper qdrant redis postgres

echo "✅ Infrastructure services stopped!"

# Show final status
echo "📊 Final Status:"
docker-compose ps postgres redis qdrant kafka zookeeper kafka-init

echo ""
echo "🔄 To restart infrastructure: ./scripts/start-infrastructure.sh"
echo "🚀 To start all services: ./scripts/start-all.sh"
