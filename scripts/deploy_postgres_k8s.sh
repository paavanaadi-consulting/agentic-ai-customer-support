#!/bin/bash

# =========================================
# Agentic AI Customer Support - Kubernetes PostgreSQL Deployment
# Deploy PostgreSQL with our custom schema to Kubernetes
# =========================================

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
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
NAMESPACE="agentic-ai-support"

print_header "Deploying PostgreSQL to Kubernetes"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl could not be found. Please install kubectl first."
    exit 1
fi

# Check if Docker image exists
print_step "Checking for Docker image..."
if docker images | grep -q "agentic-ai-postgres"; then
    print_success "Docker image 'agentic-ai-postgres' found"
else
    print_warning "Docker image 'agentic-ai-postgres' not found. Building it now..."
    cd "$PROJECT_ROOT/ops/postgres"
    docker build -t agentic-ai-postgres .
    if [ $? -eq 0 ]; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
fi

# Check if we're using minikube and load the image
if kubectl config current-context | grep -q "minikube"; then
    print_step "Detected minikube, loading Docker image..."
    minikube image load agentic-ai-postgres:latest
    print_success "Image loaded to minikube"
fi

# Create namespace if it doesn't exist
print_step "Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
print_success "Namespace '$NAMESPACE' ready"

# Apply PostgreSQL deployment
print_step "Deploying PostgreSQL..."
kubectl apply -f "$PROJECT_ROOT/ops/kubernetes/base/postgres.yaml"
print_success "PostgreSQL deployment applied"

# Wait for PostgreSQL to be ready
print_step "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgres -n $NAMESPACE --timeout=300s

if [ $? -eq 0 ]; then
    print_success "PostgreSQL is ready!"
else
    print_warning "PostgreSQL deployment may still be starting. Checking status..."
fi

# Check deployment status
print_step "Checking deployment status..."
kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=postgres

# Get service information
print_step "Service information:"
kubectl get svc -n $NAMESPACE postgres

# Test database connection
print_step "Testing database connection..."
POD_NAME=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=postgres -o jsonpath='{.items[0].metadata.name}')

if [ -n "$POD_NAME" ]; then
    print_info "Testing connection to pod: $POD_NAME"
    
    # Test database connection
    if kubectl exec -n $NAMESPACE $POD_NAME -- psql -U admin -d agentic_ai_support -c "SELECT version();" > /dev/null 2>&1; then
        print_success "Database connection successful"
        
        # Show table count
        TABLE_COUNT=$(kubectl exec -n $NAMESPACE $POD_NAME -- psql -U admin -d agentic_ai_support -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)
        print_info "Database contains $TABLE_COUNT tables"
        
        # Show sample data
        CUSTOMER_COUNT=$(kubectl exec -n $NAMESPACE $POD_NAME -- psql -U admin -d agentic_ai_support -t -c "SELECT count(*) FROM customers;" | xargs)
        print_info "Database contains $CUSTOMER_COUNT customers"
        
    else
        print_warning "Database connection test failed, but this might be expected during initialization"
    fi
else
    print_warning "Could not find PostgreSQL pod"
fi

print_header "Deployment Summary"
print_info "Namespace: $NAMESPACE"
print_info "Service: postgres.$NAMESPACE.svc.cluster.local:5432"
print_info "Database: agentic_ai_support"
print_info "Username: admin"
print_info "Password: admin123"

print_step "Useful commands:"
echo "  kubectl get pods -n $NAMESPACE"
echo "  kubectl logs -n $NAMESPACE deployment/postgres"
echo "  kubectl exec -n $NAMESPACE deployment/postgres -- psql -U admin -d agentic_ai_support"
echo "  kubectl port-forward -n $NAMESPACE service/postgres 5432:5432"

print_success "PostgreSQL deployment completed!"
