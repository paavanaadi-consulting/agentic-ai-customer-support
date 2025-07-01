#!/bin/bash
# Start script for the agentic AI customer support system

set -e  # Exit on any error

echo "🚀 Starting Agentic AI Customer Support System..."

# Change to cicd directory (we're in scripts/main subfolder)
cd "$(dirname "$0")/../.."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Check if .env file exists
if [[ ! -f .env ]]; then
    echo "⚠️  .env file not found. Creating a sample .env file..."
    cat > .env << EOF
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=customer_support
DB_USER=admin
DB_PASSWORD=password

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Vector Database Configuration
VECTOR_DB_HOST=qdrant
VECTOR_DB_PORT=6333

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# MCP Services Configuration
MCP_DATABASE_HOST=mcp-database
MCP_DATABASE_PORT=8001
MCP_KAFKA_HOST=mcp-kafka-wrapper
MCP_KAFKA_PORT=8003
MCP_AWS_HOST=mcp-aws
MCP_AWS_PORT=8004

# API Keys (add your actual keys here)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here

# AWS Configuration (if using AWS MCP)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1
EOF
    echo "✅ Sample .env file created. Please update it with your actual API keys."
fi

# Start all services
echo "🔄 Starting all services with Docker Compose..."
docker-compose -f docker-compose.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
services=("agentic-ai-customer-support:8000" "mcp-database:8001" "mcp-kafka-wrapper:8003" "mcp-aws:8004")

for service in "${services[@]}"; do
    name=${service%:*}
    port=${service#*:}
    if curl -sf http://localhost:$port/health > /dev/null 2>&1; then
        echo "✅ $name is healthy"
    else
        echo "⚠️  $name may not be ready yet (this is normal during first startup)"
    fi
done

echo ""
echo "🎉 System started successfully!"
echo ""
echo "📋 Service URLs:"
echo "   Main API: http://localhost:8000"
echo "   MCP Database: http://localhost:8001"
echo "   MCP Kafka Wrapper: http://localhost:8003"
echo "   MCP AWS: http://localhost:8004"
echo "   PostgreSQL: localhost:5432"
echo "   Kafka: localhost:9092"
echo "   Qdrant: http://localhost:6333"
echo "   Redis: localhost:6379"
echo ""
echo "📖 View logs: docker-compose -f docker-compose.yml logs -f"
echo "🛑 Stop services: ./scripts/main/stop.sh"
