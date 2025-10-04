#!/bin/bash

# AI Customer Support - Stack Management Script
# This script helps manage the complete monitoring and CI/CD stack

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE_SIMPLE="docker-compose-simple.yml"
COMPOSE_FILE_FULL="docker-compose-full.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
AI Customer Support Stack Management

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    start-simple    Start core services only (API, Database, MCP)
    start-full      Start all services including monitoring and CI/CD
    stop            Stop all services
    restart         Restart all services
    status          Show status of all services
    logs            Show logs for all services
    health          Check health of all services
    clean           Remove all containers and volumes
    build           Rebuild all containers
    backup          Backup database and configurations
    restore         Restore from backup
    update          Update all services to latest versions

Options:
    -f, --follow    Follow logs (for logs command)
    -d, --detach    Run in background (for start commands)
    -v, --verbose   Verbose output

Examples:
    $0 start-full           # Start complete stack
    $0 logs -f api-service  # Follow API service logs
    $0 health               # Check all service health
    $0 clean                # Clean everything

Services:
    Core:       postgres, mcp-postgres, api-service
    Monitoring: prometheus, grafana, alertmanager, node-exporter
    CI/CD:      jenkins
    Optional:   agents (consumer service)

Access URLs:
    API:         http://localhost:8000
    Grafana:     http://localhost:3000 (admin/admin123)
    Prometheus:  http://localhost:9090
    Jenkins:     http://localhost:8080 (admin/admin123)
    AlertManager: http://localhost:9093

EOF
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Check if Docker Compose is available
check_compose() {
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "Docker Compose is not installed."
        exit 1
    fi
}

# Start services
start_services() {
    local compose_file=$1
    local detach_flag=""
    
    if [[ "$2" == "-d" || "$2" == "--detach" ]]; then
        detach_flag="-d"
    fi
    
    log_info "Starting services using $compose_file..."
    
    cd "$SCRIPT_DIR"
    docker-compose -f "$compose_file" up $detach_flag
    
    if [[ -n "$detach_flag" ]]; then
        log_success "Services started in background"
        show_access_urls
    fi
}

# Stop services
stop_services() {
    log_info "Stopping all services..."
    
    cd "$SCRIPT_DIR"
    
    # Try to stop both compose files
    if [[ -f "$COMPOSE_FILE_FULL" ]]; then
        docker-compose -f "$COMPOSE_FILE_FULL" down || true
    fi
    
    if [[ -f "$COMPOSE_FILE_SIMPLE" ]]; then
        docker-compose -f "$COMPOSE_FILE_SIMPLE" down || true
    fi
    
    log_success "All services stopped"
}

# Show service status
show_status() {
    log_info "Service Status:"
    
    cd "$SCRIPT_DIR"
    
    if [[ -f "$COMPOSE_FILE_FULL" ]]; then
        docker-compose -f "$COMPOSE_FILE_FULL" ps
    else
        docker-compose -f "$COMPOSE_FILE_SIMPLE" ps
    fi
}

# Show logs
show_logs() {
    local follow_flag=""
    local service=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--follow)
                follow_flag="-f"
                shift
                ;;
            *)
                service="$1"
                shift
                ;;
        esac
    done
    
    cd "$SCRIPT_DIR"
    
    if [[ -n "$service" ]]; then
        log_info "Showing logs for $service..."
        docker-compose -f "$COMPOSE_FILE_FULL" logs $follow_flag "$service" 2>/dev/null || \
        docker-compose -f "$COMPOSE_FILE_SIMPLE" logs $follow_flag "$service"
    else
        log_info "Showing logs for all services..."
        docker-compose -f "$COMPOSE_FILE_FULL" logs $follow_flag 2>/dev/null || \
        docker-compose -f "$COMPOSE_FILE_SIMPLE" logs $follow_flag
    fi
}

# Health check
health_check() {
    log_info "Checking service health..."
    
    # API Health
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        log_success "API Service: Healthy"
    else
        log_error "API Service: Unhealthy"
    fi
    
    # Prometheus Health
    if curl -f http://localhost:9090/-/healthy >/dev/null 2>&1; then
        log_success "Prometheus: Healthy"
    else
        log_warning "Prometheus: Not running or unhealthy"
    fi
    
    # Grafana Health
    if curl -f http://localhost:3000/api/health >/dev/null 2>&1; then
        log_success "Grafana: Healthy"
    else
        log_warning "Grafana: Not running or unhealthy"
    fi
    
    # Jenkins Health
    if curl -f http://localhost:8080/login >/dev/null 2>&1; then
        log_success "Jenkins: Healthy"
    else
        log_warning "Jenkins: Not running or unhealthy"
    fi
    
    # Database Health
    if docker exec -it $(docker ps -q -f name=postgres) pg_isready -U admin >/dev/null 2>&1; then
        log_success "PostgreSQL: Healthy"
    else
        log_error "PostgreSQL: Unhealthy"
    fi
}

# Clean everything
clean_all() {
    log_warning "This will remove all containers, networks, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cleaning all resources..."
        
        cd "$SCRIPT_DIR"
        
        # Stop and remove everything
        docker-compose -f "$COMPOSE_FILE_FULL" down -v --remove-orphans 2>/dev/null || true
        docker-compose -f "$COMPOSE_FILE_SIMPLE" down -v --remove-orphans 2>/dev/null || true
        
        # Remove images related to this project
        docker images --format "table {{.Repository}}:{{.Tag}}" | grep -E "(ai-customer-support|agentic)" | xargs -r docker rmi || true
        
        log_success "Cleanup completed"
    else
        log_info "Cleanup cancelled"
    fi
}

# Build all containers
build_all() {
    log_info "Building all containers..."
    
    cd "$SCRIPT_DIR"
    docker-compose -f "$COMPOSE_FILE_FULL" build --no-cache
    
    log_success "All containers built"
}

# Backup database and configs
backup_data() {
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    
    log_info "Creating backup in $backup_dir..."
    
    mkdir -p "$backup_dir"
    
    # Backup database
    if docker ps --format "{{.Names}}" | grep -q postgres; then
        log_info "Backing up database..."
        docker exec $(docker ps -q -f name=postgres) pg_dump -U admin customer_support > "$backup_dir/database.sql"
        log_success "Database backup completed"
    fi
    
    # Backup configurations
    log_info "Backing up configurations..."
    cp -r monitoring "$backup_dir/"
    cp -r jenkins "$backup_dir/"
    cp *.yml "$backup_dir/"
    
    log_success "Backup completed in $backup_dir"
}

# Show access URLs
show_access_urls() {
    cat << EOF

${GREEN}=== Service Access URLs ===${NC}
${BLUE}API Service:${NC}      http://localhost:8000
${BLUE}API Health:${NC}       http://localhost:8000/health
${BLUE}API Docs:${NC}         http://localhost:8000/docs

${BLUE}Grafana:${NC}          http://localhost:3000 (admin/admin123)
${BLUE}Prometheus:${NC}       http://localhost:9090
${BLUE}AlertManager:${NC}     http://localhost:9093
${BLUE}Jenkins:${NC}          http://localhost:8080 (admin/admin123)

${YELLOW}Note: It may take a few minutes for all services to be fully ready${NC}

EOF
}

# Main script logic
main() {
    check_docker
    check_compose
    
    case "${1:-}" in
        start-simple)
            start_services "$COMPOSE_FILE_SIMPLE" "$2"
            ;;
        start-full)
            start_services "$COMPOSE_FILE_FULL" "$2"
            ;;
        stop)
            stop_services
            ;;
        restart)
            stop_services
            sleep 5
            start_services "$COMPOSE_FILE_FULL" "-d"
            ;;
        status)
            show_status
            ;;
        logs)
            shift
            show_logs "$@"
            ;;
        health)
            health_check
            ;;
        clean)
            clean_all
            ;;
        build)
            build_all
            ;;
        backup)
            backup_data
            ;;
        update)
            log_info "Pulling latest images..."
            cd "$SCRIPT_DIR"
            docker-compose -f "$COMPOSE_FILE_FULL" pull
            log_success "Images updated"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: ${1:-}"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
