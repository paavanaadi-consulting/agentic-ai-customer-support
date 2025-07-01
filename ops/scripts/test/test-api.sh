#!/bin/bash
# Test script for API component

set -e

echo "🧪 Testing API Component..."

# Change to ops directory (we're in scripts/test subfolder)
cd "$(dirname "$0")/../.."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to check if API is responding
check_api_health() {
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for API to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost:8080/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ API is responding!${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ API failed to start within 60 seconds${NC}"
    return 1
}

# Function to test API endpoints
test_api_endpoints() {
    echo ""
    echo "🔍 Testing API endpoints..."
    
    # Test root endpoint
    echo -n "📍 Testing root endpoint: "
    if response=$(curl -s http://localhost:8080/); then
        if echo "$response" | grep -q "Agentic AI Customer Support API"; then
            echo -e "${GREEN}✅ Pass${NC}"
        else
            echo -e "${RED}❌ Fail - Unexpected response${NC}"
            echo "Response: $response"
        fi
    else
        echo -e "${RED}❌ Fail - No response${NC}"
    fi
    
    # Test health endpoint
    echo -n "🏥 Testing health endpoint: "
    if response=$(curl -s http://localhost:8080/health); then
        if echo "$response" | grep -q "healthy"; then
            echo -e "${GREEN}✅ Pass${NC}"
        else
            echo -e "${YELLOW}⚠️  Warning - Service reports unhealthy${NC}"
            echo "Response: $response"
        fi
    else
        echo -e "${RED}❌ Fail - No response${NC}"
    fi
    
    # Test docs endpoint
    echo -n "📚 Testing docs endpoint: "
    if curl -f -s http://localhost:8080/docs > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Pass${NC}"
    else
        echo -e "${RED}❌ Fail${NC}"
    fi
    
    # Test OpenAPI endpoint
    echo -n "📋 Testing OpenAPI endpoint: "
    if curl -f -s http://localhost:8080/openapi.json > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Pass${NC}"
    else
        echo -e "${RED}❌ Fail${NC}"
    fi
    
    # Test API v1 routes (if they exist)
    echo -n "🔌 Testing API v1 routes: "
    if curl -f -s http://localhost:8080/api/v1/status > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Pass${NC}"
    else
        echo -e "${YELLOW}⚠️  API v1 routes not available (may be expected)${NC}"
    fi
}

# Function to show API information
show_api_info() {
    echo ""
    echo -e "${BLUE}📊 API Service Information:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if response=$(curl -s http://localhost:8080/); then
        echo "Service: $(echo "$response" | jq -r '.message // "Unknown"' 2>/dev/null || echo "Agentic AI Customer Support API")"
        echo "Version: $(echo "$response" | jq -r '.version // "Unknown"' 2>/dev/null || echo "1.0.0")"
    fi
    
    echo "URL: http://localhost:8080"
    echo "Documentation: http://localhost:8080/docs"
    echo "Health Check: http://localhost:8080/health"
    echo "OpenAPI Spec: http://localhost:8080/openapi.json"
    
    # Show container status
    echo ""
    echo "🐳 Container Status:"
    docker-compose -f docker-compose.yml ps api-service
}

# Function to run load test
run_load_test() {
    echo ""
    echo -e "${YELLOW}🔄 Running basic load test...${NC}"
    
    if command -v ab > /dev/null 2>&1; then
        echo "Using Apache Bench (ab) for load testing..."
        ab -n 100 -c 10 http://localhost:8080/health
    elif command -v curl > /dev/null 2>&1; then
        echo "Running simple concurrent test with curl..."
        for i in {1..10}; do
            curl -s http://localhost:8080/health > /dev/null &
        done
        wait
        echo -e "${GREEN}✅ Concurrent requests completed${NC}"
    else
        echo -e "${YELLOW}⚠️  No load testing tools available${NC}"
    fi
}

# Main testing flow
main() {
    echo "🧪 Starting API Component Test Suite"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Check if PostgreSQL is running (required for API)
    echo "🗄️  Checking PostgreSQL dependency..."
    if ! docker-compose -f docker-compose.yml ps postgres | grep -q "Up"; then
        echo "📦 Starting PostgreSQL..."
        docker-compose -f docker-compose.yml up -d postgres
        
        echo "⏳ Waiting for PostgreSQL to be ready..."
        sleep 10
        
        # Wait for PostgreSQL to be healthy
        local attempts=0
        while [ $attempts -lt 30 ]; do
            if docker-compose -f docker-compose.yml exec -T postgres pg_isready -U admin -d customer_support > /dev/null 2>&1; then
                echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
                break
            fi
            echo -n "."
            sleep 2
            attempts=$((attempts + 1))
        done
    else
        echo -e "${GREEN}✅ PostgreSQL is already running${NC}"
    fi
    
    # Start API service
    echo ""
    echo "🚀 Starting API service..."
    docker-compose -f docker-compose.yml up -d api-service
    
    # Wait for API to be ready
    if check_api_health; then
        # Run tests
        test_api_endpoints
        show_api_info
        
        # Ask if user wants load test
        echo ""
        read -p "🔄 Run load test? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            run_load_test
        fi
        
        echo ""
        echo -e "${GREEN}✅ API testing completed successfully!${NC}"
        echo ""
        echo "🌐 You can now access:"
        echo "  • API: http://localhost:8080"
        echo "  • Docs: http://localhost:8080/docs"
        echo "  • Health: http://localhost:8080/health"
        echo ""
        echo "🛑 To stop: docker-compose -f docker-compose.yml stop api-service"
        echo "📋 To view logs: docker-compose -f docker-compose.yml logs -f api-service"
        
    else
        echo -e "${RED}❌ API testing failed - service not responding${NC}"
        echo ""
        echo "🔍 Debugging information:"
        echo "Container status:"
        docker-compose -f docker-compose.yml ps api-service
        echo ""
        echo "Recent logs:"
        docker-compose -f docker-compose.yml logs --tail=20 api-service
        exit 1
    fi
}

# Run main function
main
