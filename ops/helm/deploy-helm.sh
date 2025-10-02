#!/bin/bash

# Helm Chart Deployment Script for Agentic AI Customer Support
# Usage: ./deploy-helm.sh [ENVIRONMENT] [CLOUD_PROVIDER]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-development}
CLOUD_PROVIDER=${2:-local}
NAMESPACE="agentic-ai-${ENVIRONMENT}"
RELEASE_NAME="agentic-ai-${ENVIRONMENT}"
CHART_PATH="./ops/helm"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        print_error "Helm is not installed. Please install Helm first."
        exit 1
    fi
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check if chart directory exists
    if [ ! -d "$CHART_PATH" ]; then
        print_error "Helm chart directory not found: $CHART_PATH"
        exit 1
    fi
    
    print_status "Prerequisites check passed ✅"
}

# Function to create namespace
create_namespace() {
    print_status "Creating namespace: $NAMESPACE"
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
}

# Function to add Helm repositories
add_helm_repos() {
    print_status "Adding Helm repositories..."
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm repo update
    print_status "Helm repositories updated ✅"
}

# Function to validate Helm chart
validate_chart() {
    print_status "Validating Helm chart..."
    helm lint "$CHART_PATH"
    print_status "Chart validation passed ✅"
}

# Function to deploy with dry-run
dry_run_deploy() {
    print_status "Performing dry-run deployment..."
    
    local values_file=""
    case $CLOUD_PROVIDER in
        aws)
            values_file="$CHART_PATH/values-aws.yaml"
            ;;
        azure)
            values_file="$CHART_PATH/values-azure.yaml"
            ;;
        gcp)
            values_file="$CHART_PATH/values-gcp.yaml"
            ;;
        *)
            values_file="$CHART_PATH/values.yaml"
            ;;
    esac
    
    if [ ! -f "$values_file" ]; then
        print_error "Values file not found: $values_file"
        exit 1
    fi
    
    helm template "$RELEASE_NAME" "$CHART_PATH" \
        --namespace "$NAMESPACE" \
        --values "$values_file" \
        --dry-run > /tmp/helm-dry-run-output.yaml
    
    print_status "Dry-run completed successfully ✅"
    print_status "Generated manifests saved to: /tmp/helm-dry-run-output.yaml"
}

# Function to deploy the application
deploy_application() {
    print_status "Deploying Agentic AI Customer Support..."
    
    local values_file=""
    case $CLOUD_PROVIDER in
        aws)
            values_file="$CHART_PATH/values-aws.yaml"
            print_status "Using AWS-specific configuration"
            ;;
        azure)
            values_file="$CHART_PATH/values-azure.yaml"
            print_status "Using Azure-specific configuration"
            ;;
        gcp)
            values_file="$CHART_PATH/values-gcp.yaml"
            print_status "Using GCP-specific configuration"
            ;;
        *)
            values_file="$CHART_PATH/values.yaml"
            print_status "Using default configuration"
            ;;
    esac
    
    # Check if release already exists
    if helm list -n "$NAMESPACE" | grep -q "$RELEASE_NAME"; then
        print_status "Upgrading existing release..."
        helm upgrade "$RELEASE_NAME" "$CHART_PATH" \
            --namespace "$NAMESPACE" \
            --values "$values_file" \
            --wait \
            --timeout 10m
    else
        print_status "Installing new release..."
        helm install "$RELEASE_NAME" "$CHART_PATH" \
            --namespace "$NAMESPACE" \
            --values "$values_file" \
            --wait \
            --timeout 10m \
            --create-namespace
    fi
    
    print_status "Deployment completed successfully ✅"
}

# Function to show deployment status
show_status() {
    print_status "Checking deployment status..."
    
    echo ""
    print_status "Helm Release Status:"
    helm status "$RELEASE_NAME" -n "$NAMESPACE"
    
    echo ""
    print_status "Pod Status:"
    kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/instance="$RELEASE_NAME"
    
    echo ""
    print_status "Service Status:"
    kubectl get svc -n "$NAMESPACE" -l app.kubernetes.io/instance="$RELEASE_NAME"
    
    echo ""
    print_status "Ingress Status:"
    kubectl get ingress -n "$NAMESPACE" -l app.kubernetes.io/instance="$RELEASE_NAME"
}

# Function to get application URLs
get_application_urls() {
    print_status "Getting application URLs..."
    
    # Check if ingress is enabled
    local ingress_host=$(kubectl get ingress -n "$NAMESPACE" -l app.kubernetes.io/instance="$RELEASE_NAME" -o jsonpath='{.items[0].spec.rules[0].host}' 2>/dev/null || echo "")
    
    if [ -n "$ingress_host" ]; then
        echo ""
        print_status "Application URLs:"
        echo "🌐 API: https://$ingress_host"
        echo "🔍 Health Check: https://$ingress_host/health"
        echo "📚 API Docs: https://$ingress_host/docs"
    else
        print_warning "Ingress not configured. Use port-forward to access services:"
        echo "kubectl port-forward -n $NAMESPACE svc/$RELEASE_NAME-agentic-ai-customer-support-api 8000:8000"
        echo "Then access: http://localhost:8000"
    fi
}

# Function to show cleanup instructions
show_cleanup() {
    echo ""
    print_status "To clean up this deployment, run:"
    echo "helm uninstall $RELEASE_NAME -n $NAMESPACE"
    echo "kubectl delete namespace $NAMESPACE"
}

# Main execution
main() {
    echo "🚀 Agentic AI Customer Support - Helm Deployment"
    echo "================================================"
    echo "Environment: $ENVIRONMENT"
    echo "Cloud Provider: $CLOUD_PROVIDER"
    echo "Namespace: $NAMESPACE"
    echo "Release Name: $RELEASE_NAME"
    echo ""
    
    check_prerequisites
    add_helm_repos
    validate_chart
    create_namespace
    
    # Ask for confirmation unless --auto flag is provided
    if [[ ! " $* " =~ " --auto " ]]; then
        echo ""
        read -p "Proceed with deployment? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_warning "Deployment cancelled."
            exit 0
        fi
    fi
    
    dry_run_deploy
    deploy_application
    show_status
    get_application_urls
    show_cleanup
    
    print_status "🎉 Deployment completed successfully!"
}

# Help function
show_help() {
    cat << EOF
Agentic AI Customer Support - Helm Deployment Script

Usage: $0 [ENVIRONMENT] [CLOUD_PROVIDER] [OPTIONS]

ENVIRONMENT:
  development (default) - Deploy development environment
  staging              - Deploy staging environment
  production           - Deploy production environment

CLOUD_PROVIDER:
  local (default)      - Use default values
  aws                  - Use AWS-specific configuration
  azure               - Use Azure-specific configuration
  gcp                 - Use GCP-specific configuration

OPTIONS:
  --auto              - Skip confirmation prompts
  --help, -h          - Show this help message

Examples:
  $0                           # Deploy development environment locally
  $0 production aws            # Deploy production environment on AWS
  $0 staging azure --auto      # Deploy staging environment on Azure without prompts

Prerequisites:
  - Helm 3.x installed
  - kubectl configured with cluster access
  - Appropriate cloud provider credentials (for cloud deployments)
EOF
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
