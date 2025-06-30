#!/bin/bash
# Start script for API component only

set -e  # Exit on any error

echo "🚀 Starting API Component..."

# Change to cicd directory (we're in scripts/main/api subfolder)
cd "$(dirname "$0")/../../.."

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

# API Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development

# Security (add your actual keys)
JWT_SECRET_KEY=your_jwt_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here
EOF
    echo "✅ Sample .env file created. Please update it with your actual configuration."
fi

# Start API services
echo "🔄 Starting API services with Docker Compose..."
docker-compose -f docker-compose.api.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 20

# Check service health
echo "🔍 Checking API service health..."
if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ API service is healthy"
else
    echo "⚠️  API service may not be ready yet (this is normal during first startup)"
fi

echo ""
echo "🎉 API service started successfully!"
echo ""
echo "📋 Service URLs:"
echo "   API Service: http://localhost:8080"
echo "   API Docs: http://localhost:8080/docs"
echo "   API Health: http://localhost:8080/health"
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo ""
echo "📖 View logs: docker-compose -f docker-compose.api.yml logs -f"
echo "🛑 Stop API: ./scripts/main/api/stop-api.sh"
