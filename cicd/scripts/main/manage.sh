#!/bin/bash
# Master script for managing Agentic AI Customer Support Docker infrastructure

set -e

# Change to cicd directory (we're already in scripts subfolder)
cd "$(dirname "$0")/.."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}🤖 Agentic AI Customer Support - Docker Manager${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to show menu
show_menu() {
    echo ""
    echo -e "${YELLOW}📋 Available Commands:${NC}"
    echo ""
    echo -e "${GREEN}🚀 Deployment & Management:${NC}"
    echo "  1) Build all services"
    echo "  2) Start all services"
    echo "  3) Stop all services"
    echo "  4) Restart all services"
    echo "  5) Cleanup all (⚠️  removes data)"
    echo ""
    echo -e "${GREEN}🔧 Development:${NC}"
    echo "  6) Start infrastructure only"
    echo "  7) Stop infrastructure"
    echo ""
    echo -e "${GREEN}📊 Monitoring & Debug:${NC}"
    echo "  8) Health check"
    echo "  9) View logs"
    echo " 10) Service status"
    echo ""
    echo -e "${GREEN}🎯 Individual Services:${NC}"
    echo " 11) Start API service only"
    echo " 12) Start Agents service only"
    echo " 13) Start Main app only"
    echo ""
    echo -e "${PURPLE}💡 Information:${NC}"
    echo " 14) Show service endpoints"
    echo " 15) Show documentation"
    echo ""
    echo "  0) Exit"
    echo ""
}

# Function to show service endpoints
show_endpoints() {
    echo ""
    echo -e "${CYAN}🌐 Service Endpoints:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "• Main Application:    http://localhost:8000"
    echo "• API Documentation:   http://localhost:8000/docs"
    echo "• API Service:         http://localhost:8080"
    echo "• API Docs:           http://localhost:8080/docs"
    echo "• Agents Service:      http://localhost:8005"
    echo "• Agents Docs:        http://localhost:8005/docs"
    echo "• Qdrant Vector DB:    http://localhost:6333/dashboard"
    echo "• PostgreSQL:          localhost:5432"
    echo "• Redis:              localhost:6379"
    echo "• Kafka:              localhost:9092"
    echo ""
    echo -e "${YELLOW}🔍 Health Checks:${NC}"
    echo "• Main App Health:     curl http://localhost:8000/health"
    echo "• API Health:         curl http://localhost:8080/health"
    echo "• Agents Health:      curl http://localhost:8005/health"
}

# Function to show documentation
show_documentation() {
    echo ""
    echo -e "${CYAN}📖 Documentation:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "• Infrastructure Guide: cicd/README-Infrastructure.md"
    echo "• API Documentation:    docs/api_reference.md"
    echo "• Architecture:         docs/architecture.md"
    echo "• Setup Guide:          docs/setup_guide.md"
    echo ""
    echo -e "${YELLOW}📁 Project Structure:${NC}"
    echo "• API Service:          cicd/api/"
    echo "• Agents Service:       cicd/agents/"
    echo "• Main Application:     cicd/main-app/"
    echo "• MCP Services:         cicd/mcp-kafka/"
    echo "• PostgreSQL:           cicd/postgres/"
    echo "• Scripts:              cicd/scripts/"
}

# Main loop
main() {
    print_header
    
    while true; do
        show_menu
        read -p "Select an option [0-15]: " choice
        
        case $choice in
            1)
                echo -e "${GREEN}🔨 Building all services...${NC}"
                ./scripts/build-all.sh
                ;;
            2)
                echo -e "${GREEN}🚀 Starting all services...${NC}"
                ./scripts/start-all.sh
                ;;
            3)
                echo -e "${YELLOW}🛑 Stopping all services...${NC}"
                ./scripts/stop-all.sh
                ;;
            4)
                echo -e "${YELLOW}🔄 Restarting all services...${NC}"
                ./scripts/stop-all.sh
                sleep 2
                ./scripts/start-all.sh
                ;;
            5)
                echo -e "${RED}🗑️  WARNING: This will remove all data!${NC}"
                ./scripts/cleanup-all.sh
                ;;
            6)
                echo -e "${GREEN}🔧 Starting infrastructure services...${NC}"
                ./scripts/start-infrastructure.sh
                ;;
            7)
                echo -e "${YELLOW}🛑 Stopping infrastructure services...${NC}"
                ./scripts/stop-infrastructure.sh
                ;;
            8)
                echo -e "${CYAN}🏥 Running health check...${NC}"
                ./scripts/health-check.sh
                ;;
            9)
                echo -e "${CYAN}📄 Viewing logs...${NC}"
                ./scripts/logs.sh
                ;;
            10)
                echo -e "${CYAN}📊 Service status:${NC}"
                docker-compose ps
                ;;
            11)
                echo -e "${GREEN}🌐 Starting API service only...${NC}"
                docker-compose up -d postgres
                sleep 5
                docker-compose up -d api-service
                ;;
            12)
                echo -e "${GREEN}🧠 Starting Agents service only...${NC}"
                docker-compose up -d postgres qdrant redis kafka zookeeper
                sleep 10
                docker-compose up -d agents-service
                ;;
            13)
                echo -e "${GREEN}🎪 Starting Main app only...${NC}"
                docker-compose up -d postgres qdrant redis kafka zookeeper
                sleep 10
                docker-compose up -d main-app
                ;;
            14)
                show_endpoints
                ;;
            15)
                show_documentation
                ;;
            0)
                echo -e "${GREEN}👋 Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Invalid option. Please try again.${NC}"
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Run main function
main
