#!/bin/bash
# Start only infrastructure services for local development

set -e

echo "🔧 Starting Infrastructure Services for Development..."

# Change to cicd directory (we're already in scripts subfolder)
cd "$(dirname "$0")/.."

# Create logs directory if it doesn't exist
mkdir -p ../logs

echo "🏗️ Starting core infrastructure services..."

# Start only infrastructure services
docker-compose up -d postgres redis qdrant zookeeper kafka

echo "⏳ Waiting for infrastructure services to be ready..."
sleep 15

echo "🎯 Initializing Kafka topics..."
docker-compose up -d kafka-init

echo "⏳ Waiting for Kafka topics to be created..."
sleep 10

echo "✅ Infrastructure services are ready for development!"

# Show status
echo "📊 Infrastructure Status:"
docker-compose ps postgres redis qdrant kafka zookeeper kafka-init

echo ""
echo "🌐 Available Services:"
echo "  • PostgreSQL:    localhost:5432"
echo "  • Redis:         localhost:6379"
echo "  • Qdrant:        localhost:6333"
echo "  • Kafka:         localhost:9092"
echo "  • Qdrant UI:     http://localhost:6333/dashboard"
echo ""
echo "🔧 Development Environment Ready!"
echo "📝 You can now run your services locally and connect to these infrastructure services."
echo ""
echo "🗄️ Database Connection:"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   Database: customer_support"
echo "   User: admin"
echo "   Password: password"
echo ""
echo "🛑 To stop infrastructure: ./scripts/stop-infrastructure.sh"
echo "🚀 To start all services: ./scripts/start-all.sh"
