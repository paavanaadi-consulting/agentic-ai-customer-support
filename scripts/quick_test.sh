#!/bin/bash

# ===============================================
# Agentic AI Customer Support - Local Test Setup
# Quick start script for local development testing
# ===============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() { echo -e "${PURPLE}🚀 $1${NC}"; }
print_step() { echo -e "${BLUE}📌 $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/local-test-setup.log"

# Ensure logs directory exists
mkdir -p "$PROJECT_ROOT/logs"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Function to check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing_tools=()
    
    # Check Docker
    if command -v docker &> /dev/null; then
        print_success "Docker found: $(docker --version | cut -d' ' -f3)"
    else
        missing_tools+=("docker")
        print_error "Docker not found"
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose found: $(docker-compose --version | cut -d' ' -f3)"
    else
        missing_tools+=("docker-compose")
        print_error "Docker Compose not found"
    fi
    
    # Check Python
    if command -v python3 &> /dev/null; then
        print_success "Python found: $(python3 --version)"
    else
        missing_tools+=("python3")
        print_error "Python 3 not found"
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null; then
        print_success "pip found: $(pip3 --version | cut -d' ' -f2)"
    else
        missing_tools+=("pip3")
        print_error "pip3 not found"
    fi
    
    # Check Git
    if command -v git &> /dev/null; then
        print_success "Git found: $(git --version | cut -d' ' -f3)"
    else
        missing_tools+=("git")
        print_error "Git not found"
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        print_info "Please install the missing tools and run this script again."
        print_info "Installation guides:"
        print_info "  Docker: https://docs.docker.com/get-docker/"
        print_info "  Python: https://www.python.org/downloads/"
        print_info "  Git: https://git-scm.com/downloads"
        exit 1
    fi
    
    log "Prerequisites check completed successfully"
}

# Function to check API keys
check_api_keys() {
    print_header "Checking API Keys"
    
    local keys_found=0
    
    if [ -n "$CLAUDE_API_KEY" ]; then
        print_success "Claude API key found"
        keys_found=$((keys_found + 1))
    else
        print_warning "Claude API key not set (CLAUDE_API_KEY)"
    fi
    
    if [ -n "$OPENAI_API_KEY" ]; then
        print_success "OpenAI API key found"
        keys_found=$((keys_found + 1))
    else
        print_warning "OpenAI API key not set (OPENAI_API_KEY)"
    fi
    
    if [ -n "$GEMINI_API_KEY" ]; then
        print_success "Gemini API key found"
        keys_found=$((keys_found + 1))
    else
        print_warning "Gemini API key not set (GEMINI_API_KEY)"
    fi
    
    if [ $keys_found -eq 0 ]; then
        print_warning "No AI API keys found. The system will run in limited mode."
        print_info "To enable full AI functionality, set these environment variables:"
        print_info "  export CLAUDE_API_KEY='your-claude-api-key'"
        print_info "  export OPENAI_API_KEY='your-openai-api-key'"
        print_info "  export GEMINI_API_KEY='your-gemini-api-key'"
    else
        print_success "$keys_found AI API key(s) configured"
    fi
    
    log "API keys check completed ($keys_found keys found)"
}

# Function to setup environment
setup_environment() {
    print_header "Setting Up Environment"
    
    cd "$PROJECT_ROOT"
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        print_step "Creating .env file..."
        cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://agenticai:change-me@localhost:5432/customer_support
POSTGRES_DB=customer_support
POSTGRES_USER=agenticai
POSTGRES_PASSWORD=change-me

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=agentic-ai

# Qdrant Configuration
QDRANT_URL=http://localhost:6333

# Application Configuration
LOG_LEVEL=INFO
DEBUG=true
ENVIRONMENT=development

# AI API Keys
CLAUDE_API_KEY=${CLAUDE_API_KEY:-}
OPENAI_API_KEY=${OPENAI_API_KEY:-}
GEMINI_API_KEY=${GEMINI_API_KEY:-}

# MCP Server URLs
MCP_POSTGRES_URL=http://localhost:8001
MCP_KAFKA_URL=http://localhost:8002
EOF
        print_success ".env file created"
    else
        print_info ".env file already exists"
    fi
    
    # Make scripts executable
    print_step "Making scripts executable..."
    find "$PROJECT_ROOT/scripts" -name "*.py" -exec chmod +x {} \;
    find "$PROJECT_ROOT/scripts" -name "*.sh" -exec chmod +x {} \;
    find "$PROJECT_ROOT/ops/scripts" -name "*.sh" -exec chmod +x {} \;
    chmod +x "$PROJECT_ROOT/docker.sh"
    print_success "Scripts made executable"
    
    log "Environment setup completed"
}

# Function to start infrastructure services
start_infrastructure() {
    print_header "Starting Infrastructure Services"
    
    cd "$PROJECT_ROOT"
    
    print_step "Starting Docker containers..."
    if docker-compose -f ops/docker-compose.yml up -d postgres kafka qdrant; then
        print_success "Infrastructure services started"
    else
        print_error "Failed to start infrastructure services"
        return 1
    fi
    
    print_step "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    print_step "Checking service health..."
    
    # Check PostgreSQL
    if docker-compose -f ops/docker-compose.yml exec -T postgres pg_isready -U agenticai; then
        print_success "PostgreSQL is ready"
    else
        print_warning "PostgreSQL not ready yet, continuing anyway..."
    fi
    
    # Check Kafka (simple port check)
    if nc -z localhost 9092 2>/dev/null; then
        print_success "Kafka is ready"
    else
        print_warning "Kafka not ready yet, continuing anyway..."
    fi
    
    # Check Qdrant
    if curl -s http://localhost:6333/health >/dev/null 2>&1; then
        print_success "Qdrant is ready"
    else
        print_warning "Qdrant not ready yet, continuing anyway..."
    fi
    
    log "Infrastructure services started"
}

# Function to setup Python environment
setup_python_environment() {
    print_header "Setting Up Python Environment"
    
    cd "$PROJECT_ROOT"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_step "Creating Python virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    print_step "Activating virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    print_step "Upgrading pip..."
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        print_step "Installing Python dependencies..."
        pip install -r requirements.txt
        print_success "Dependencies installed"
    else
        print_warning "requirements.txt not found"
    fi
    
    # Install package in development mode
    if [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
        print_step "Installing package in development mode..."
        pip install -e .
        print_success "Package installed in development mode"
    fi
    
    log "Python environment setup completed"
}

# Function to initialize database
initialize_database() {
    print_header "Initializing Database"
    
    cd "$PROJECT_ROOT"
    
    print_step "Running database initialization..."
    if python3 scripts/init_db.py; then
        print_success "Database initialized"
    else
        print_warning "Database initialization failed, continuing anyway..."
    fi
    
    print_step "Seeding database with sample data..."
    if python3 scripts/seed_db.py; then
        print_success "Sample data loaded"
    else
        print_warning "Sample data loading failed, continuing anyway..."
    fi
    
    log "Database initialization completed"
}

# Function to run tests
run_tests() {
    print_header "Running Basic Tests"
    
    cd "$PROJECT_ROOT"
    
    # Test database connectivity
    print_step "Testing database connectivity..."
    if python3 scripts/test_postgresql.py; then
        print_success "Database connectivity test passed"
    else
        print_warning "Database connectivity test failed"
    fi
    
    # Test API health (if API server is running)
    print_step "Testing API health..."
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        print_success "API health check passed"
    else
        print_info "API server not running (this is expected for initial setup)"
    fi
    
    log "Basic tests completed"
}

# Function to run end-to-end tests
run_e2e_tests() {
    print_header "Running End-to-End Tests"
    
    cd "$PROJECT_ROOT"
    
    # Test customer support workflow
    print_step "Testing customer support workflow..."
    if curl -s -X POST http://localhost:8000/api/v1/support/query \
        -H "Content-Type: application/json" \
        -d '{"query": "I need help with my account", "user_id": "test_user"}' \
        | jq . >/dev/null 2>&1; then
        print_success "Customer support workflow test passed"
    else
        print_warning "Customer support workflow test failed or API not running"
    fi
    
    # Test genetic ML evolution
    print_step "Testing genetic ML evolution..."
    if curl -s -X POST http://localhost:8000/api/v1/evolution/trigger \
        -H "Content-Type: application/json" \
        -d '{"generations": 2, "population_size": 5}' \
        | jq . >/dev/null 2>&1; then
        print_success "Genetic ML evolution test passed"
    else
        print_warning "Genetic ML evolution test failed or API not running"
    fi
    
    # Test A2A protocol
    print_step "Testing A2A protocol..."
    if python3 scripts/test_a2a_local.py > /dev/null 2>&1; then
        print_success "A2A protocol test passed"
    else
        print_warning "A2A protocol test failed"
    fi
    
    log "End-to-end tests completed"
}

# Function to validate environment
validate_environment() {
    print_header "Validating Environment"
    
    local validation_passed=true
    
    # Check Python version
    print_step "Checking Python version..."
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    if python3 -c "import sys; assert sys.version_info >= (3, 8)" 2>/dev/null; then
        print_success "Python $python_version (compatible)"
    else
        print_error "Python $python_version (requires 3.8+)"
        validation_passed=false
    fi
    
    # Check Docker
    print_step "Checking Docker..."
    if command -v docker >/dev/null 2>&1; then
        docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        print_success "Docker $docker_version"
    else
        print_error "Docker not found"
        validation_passed=false
    fi
    
    # Check Docker Compose
    print_step "Checking Docker Compose..."
    if command -v docker-compose >/dev/null 2>&1; then
        compose_version=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        print_success "Docker Compose $compose_version"
    else
        print_error "Docker Compose not found"
        validation_passed=false
    fi
    
    # Check available disk space
    print_step "Checking disk space..."
    available_space=$(df -h . | awk 'NR==2 {print $4}')
    print_info "Available disk space: $available_space"
    
    # Check available memory
    print_step "Checking available memory..."
    if command -v free >/dev/null 2>&1; then
        available_memory=$(free -h | awk 'NR==2{print $7}')
        print_info "Available memory: $available_memory"
    elif command -v vm_stat >/dev/null 2>&1; then
        # macOS
        free_pages=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
        free_mb=$((free_pages * 4096 / 1024 / 1024))
        print_info "Available memory: ~${free_mb}MB"
    fi
    
    if [ "$validation_passed" = true ]; then
        print_success "Environment validation passed"
        return 0
    else
        print_error "Environment validation failed"
        return 1
    fi
}

# Function to show interactive menu
show_menu() {
    clear
    print_header "Agentic AI Customer Support - Local Testing Menu"
    
    echo "Choose an option:"
    echo "  1) Quick Start (Full Setup)"
    echo "  2) Start Infrastructure Only"
    echo "  3) Start Application Only"
    echo "  4) Run Tests"
    echo "  5) Run End-to-End Tests"
    echo "  6) Show Status"
    echo "  7) View Logs"
    echo "  8) Stop Services"
    echo "  9) Clean Reset"
    echo "  0) Exit"
    echo
    read -p "Enter your choice [0-9]: " choice
    
    case $choice in
        1)
            validate_environment && main start
            ;;
        2)
            start_infrastructure
            show_status
            ;;
        3)
            start_application
            show_status
            ;;
        4)
            run_tests
            ;;
        5)
            run_e2e_tests
            ;;
        6)
            show_status
            ;;
        7)
            if [ -f "$LOG_FILE" ]; then
                tail -f "$LOG_FILE"
            else
                print_warning "No log file found"
            fi
            ;;
        8)
            cleanup
            ;;
        9)
            cleanup
            print_step "Removing Docker volumes..."
            docker volume prune -f
            print_success "Clean reset completed"
            ;;
        0)
            print_info "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            sleep 2
            show_menu
            ;;
    esac
}

# Function to cleanup
cleanup() {
    print_header "Cleaning Up"
    
    cd "$PROJECT_ROOT"
    
    print_step "Stopping application processes..."
    if [ -f logs/api-server.pid ]; then
        API_PID=$(cat logs/api-server.pid)
        if kill -0 $API_PID 2>/dev/null; then
            kill $API_PID
            print_success "API server stopped"
        fi
        rm -f logs/api-server.pid
    fi
    
    if [ -f logs/mcp-servers.pid ]; then
        MCP_PID=$(cat logs/mcp-servers.pid)
        if kill -0 $MCP_PID 2>/dev/null; then
            kill $MCP_PID
            print_success "MCP servers stopped"
        fi
        rm -f logs/mcp-servers.pid
    fi
    
    print_step "Stopping Docker containers..."
    docker-compose -f ops/docker-compose.yml down
    print_success "Docker containers stopped"
    
    log "Cleanup completed"
}

# Function to show help
show_help() {
    cat << EOF
Agentic AI Customer Support - Local Test Setup

Usage: $0 [OPTION]

Options:
  start         Start the complete system (default)
  stop          Stop all services
  restart       Restart all services
  status        Show system status
  test          Run basic tests
  clean         Clean up and remove all data
  logs          Show logs
  help          Show this help message

Examples:
  $0 start      # Start the complete system
  $0 status     # Check system status
  $0 test       # Run basic tests
  $0 stop       # Stop all services

Environment Variables:
  CLAUDE_API_KEY    Anthropic Claude API key
  OPENAI_API_KEY    OpenAI API key
  GEMINI_API_KEY    Google Gemini API key

For more detailed testing instructions, see LOCAL_TESTING_GUIDE.md
EOF
}

# Main script logic
main() {
    local action="${1:-start}"
    
    case "$action" in
        "start")
            print_header "Agentic AI Customer Support - Local Setup"
            print_info "Log file: $LOG_FILE"
            
            check_prerequisites
            check_api_keys
            setup_environment
            start_infrastructure
            setup_python_environment
            initialize_database
            start_application
            run_tests
            show_status
            
            print_header "Setup Complete!"
            print_success "System is running and ready for testing"
            print_info "Run './scripts/quick_test.sh status' to check system status"
            print_info "Run './scripts/quick_test.sh test' to run additional tests"
            print_info "See LOCAL_TESTING_GUIDE.md for detailed testing instructions"
            ;;
        "stop")
            cleanup
            ;;
        "restart")
            cleanup
            sleep 5
            main start
            ;;
        "status")
            show_status
            ;;
        "test")
            run_tests
            ;;
        "e2e"|"e2e-test")
            run_e2e_tests
            ;;
        "validate"|"check")
            validate_environment
            ;;
        "menu"|"interactive")
            show_menu
            ;;
        "clean")
            cleanup
            print_step "Removing Docker volumes..."
            docker volume prune -f
            print_step "Removing Python virtual environment..."
            rm -rf venv
            print_success "Complete cleanup finished"
            ;;
        "logs")
            print_step "Showing logs..."
            if [ -f "$LOG_FILE" ]; then
                tail -f "$LOG_FILE"
            else
                print_warning "No log file found"
            fi
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown action: $action"
            show_help
            exit 1
            ;;
    esac
}

# Trap to cleanup on script exit
trap 'echo -e "\n${YELLOW}Script interrupted. Run '"'"'$0 stop'"'"' to cleanup.${NC}"' INT TERM

# Run main function
main "$@"
