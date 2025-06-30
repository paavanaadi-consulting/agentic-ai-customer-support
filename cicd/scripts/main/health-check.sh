#!/bin/bash
# Health check script for all services

set -e

# Change to cicd directory (we're already in scripts subfolder)
cd "$(dirname "$0")/.."

echo "🏥 Agentic AI Customer Support - Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Function to check HTTP endpoint
check_http_endpoint() {
    local service_name=$1
    local url=$2
    local timeout=${3:-5}
    
    echo -n "🔍 $service_name: "
    
    if curl -f -s --max-time $timeout "$url" > /dev/null 2>&1; then
        echo "✅ Healthy"
        return 0
    else
        echo "❌ Unhealthy"
        return 1
    fi
}

# Function to check database connection
check_database() {
    echo -n "🗄️  PostgreSQL: "
    
    if docker-compose exec -T postgres pg_isready -U admin -d customer_support > /dev/null 2>&1; then
        echo "✅ Healthy"
        return 0
    else
        echo "❌ Unhealthy"
        return 1
    fi
}

# Function to check if service is running
check_service_running() {
    local service_name=$1
    echo -n "🔧 $service_name: "
    
    if docker-compose ps "$service_name" | grep -q "Up"; then
        echo "✅ Running"
        return 0
    else
        echo "❌ Not Running"
        return 1
    fi
}

echo "📊 Service Status Check:"
echo ""

# Check if services are running
check_service_running "postgres"
check_service_running "redis"
check_service_running "kafka"
check_service_running "qdrant"
check_service_running "api-service"
check_service_running "agents-service"
check_service_running "main-app"

echo ""
echo "🌐 Health Endpoint Checks:"
echo ""

# Check health endpoints
check_database
check_http_endpoint "API Service" "http://localhost:8080/health"
check_http_endpoint "Agents Service" "http://localhost:8005/health"
check_http_endpoint "Main Application" "http://localhost:8000/health"
check_http_endpoint "Qdrant" "http://localhost:6333/"

echo ""
echo "🔌 Infrastructure Service Checks:"
echo ""

# Check Redis
echo -n "📦 Redis: "
if docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

# Check Kafka
echo -n "📡 Kafka: "
if docker-compose exec -T kafka /opt/bitnami/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092 > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

echo ""
echo "📋 Docker Compose Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker-compose ps

echo ""
echo "💡 Tips:"
echo "  • If services are unhealthy, check logs: ./scripts/logs.sh [service-name]"
echo "  • To restart a service: docker-compose restart [service-name]"
echo "  • To restart all services: ./scripts/stop-all.sh && ./scripts/start-all.sh"
