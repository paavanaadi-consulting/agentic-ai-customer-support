#!/bin/bash

# Helm Chart Testing Script for Agentic AI Customer Support
# This script validates the Helm chart templates and configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CHART_PATH="./ops/helm"
TEST_NAMESPACE="agentic-ai-test"

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

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

# Test 1: Chart structure validation
test_chart_structure() {
    print_test "Testing chart structure..."
    
    # Check required files
    local required_files=(
        "Chart.yaml"
        "values.yaml"
        "values-aws.yaml"
        "values-azure.yaml"
        "values-gcp.yaml"
        "templates/_helpers.tpl"
        "templates/NOTES.txt"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$CHART_PATH/$file" ]; then
            print_status "✅ $file exists"
        else
            print_error "❌ $file missing"
            return 1
        fi
    done
    
    # Check template files
    local template_files=(
        "api-deployment.yaml"
        "api-service.yaml" 
        "api-hpa.yaml"
        "mcp-postgres-deployment.yaml"
        "mcp-postgres-service.yaml"
        "mcp-kafka-deployment.yaml"
        "mcp-kafka-service.yaml"
        "consumer-deployment.yaml"
        "consumer-service.yaml"
        "consumer-hpa.yaml"
        "qdrant-deployment.yaml"
        "qdrant-service.yaml"
        "qdrant-pvc.yaml"
        "ingress.yaml"
        "configmap.yaml"
        "secrets.yaml"
        "serviceaccount.yaml"
        "pdb.yaml"
        "networkpolicy.yaml"
    )
    
    for template in "${template_files[@]}"; do
        if [ -f "$CHART_PATH/templates/$template" ]; then
            print_status "✅ templates/$template exists"
        else
            print_error "❌ templates/$template missing"
            return 1
        fi
    done
    
    print_status "Chart structure validation passed ✅"
}

# Test 2: Helm lint
test_helm_lint() {
    print_test "Running Helm lint..."
    
    if helm lint "$CHART_PATH"; then
        print_status "Helm lint passed ✅"
    else
        print_error "Helm lint failed ❌"
        return 1
    fi
}

# Test 3: Template rendering with default values
test_template_rendering_default() {
    print_test "Testing template rendering with default values..."
    
    if helm template test "$CHART_PATH" --dry-run > /tmp/helm-test-default.yaml 2>&1; then
        print_status "Default template rendering passed ✅"
    else
        print_error "Default template rendering failed ❌"
        cat /tmp/helm-test-default.yaml
        return 1
    fi
}

# Test 4: Template rendering with AWS values
test_template_rendering_aws() {
    print_test "Testing template rendering with AWS values..."
    
    if helm template test "$CHART_PATH" -f "$CHART_PATH/values-aws.yaml" --dry-run > /tmp/helm-test-aws.yaml 2>&1; then
        print_status "AWS template rendering passed ✅"
    else
        print_error "AWS template rendering failed ❌"
        cat /tmp/helm-test-aws.yaml
        return 1
    fi
}

# Test 5: Template rendering with Azure values
test_template_rendering_azure() {
    print_test "Testing template rendering with Azure values..."
    
    if helm template test "$CHART_PATH" -f "$CHART_PATH/values-azure.yaml" --dry-run > /tmp/helm-test-azure.yaml 2>&1; then
        print_status "Azure template rendering passed ✅"
    else
        print_error "Azure template rendering failed ❌"
        cat /tmp/helm-test-azure.yaml
        return 1
    fi
}

# Test 6: Template rendering with GCP values
test_template_rendering_gcp() {
    print_test "Testing template rendering with GCP values..."
    
    if helm template test "$CHART_PATH" -f "$CHART_PATH/values-gcp.yaml" --dry-run > /tmp/helm-test-gcp.yaml 2>&1; then
        print_status "GCP template rendering passed ✅"
    else
        print_error "GCP template rendering failed ❌"
        cat /tmp/helm-test-gcp.yaml
        return 1
    fi
}

# Test 7: YAML validation
test_yaml_validation() {
    print_test "Validating generated YAML syntax..."
    
    # Test default values
    helm template test "$CHART_PATH" --dry-run > /tmp/helm-test-yaml.yaml
    
    # Use kubectl to validate YAML syntax
    if kubectl apply --dry-run=client -f /tmp/helm-test-yaml.yaml > /dev/null 2>&1; then
        print_status "YAML validation passed ✅"
    else
        print_error "YAML validation failed ❌"
        return 1
    fi
}

# Test 8: Resource validation
test_resource_validation() {
    print_test "Validating Kubernetes resources..."
    
    helm template test "$CHART_PATH" --dry-run > /tmp/helm-test-resources.yaml
    
    # Check for required Kubernetes resources
    local required_resources=(
        "Deployment"
        "Service"
        "ConfigMap"
        "Secret"
        "HorizontalPodAutoscaler"
        "PersistentVolumeClaim"
        "Ingress"
        "ServiceAccount"
        "PodDisruptionBudget"
        "NetworkPolicy"
    )
    
    for resource in "${required_resources[@]}"; do
        if grep -q "kind: $resource" /tmp/helm-test-resources.yaml; then
            print_status "✅ $resource found in templates"
        else
            print_warning "⚠️  $resource not found in templates"
        fi
    done
    
    print_status "Resource validation completed ✅"
}

# Test 9: Dependencies check
test_dependencies() {
    print_test "Testing Helm dependencies..."
    
    # Check if dependencies are defined in Chart.yaml
    if grep -q "dependencies:" "$CHART_PATH/Chart.yaml"; then
        print_status "Dependencies found in Chart.yaml"
        
        # Update dependencies
        if helm dependency update "$CHART_PATH"; then
            print_status "Dependencies updated successfully ✅"
        else
            print_error "Failed to update dependencies ❌"
            return 1
        fi
    else
        print_warning "No dependencies defined in Chart.yaml"
    fi
}

# Test 10: Values validation
test_values_validation() {
    print_test "Validating values files..."
    
    local values_files=(
        "values.yaml"
        "values-aws.yaml"
        "values-azure.yaml"
        "values-gcp.yaml"
    )
    
    for values_file in "${values_files[@]}"; do
        if [ -f "$CHART_PATH/$values_file" ]; then
            # Test YAML syntax
            if python3 -c "import yaml; yaml.safe_load(open('$CHART_PATH/$values_file'))" 2>/dev/null; then
                print_status "✅ $values_file has valid YAML syntax"
            else
                print_error "❌ $values_file has invalid YAML syntax"
                return 1
            fi
        fi
    done
    
    print_status "Values validation passed ✅"
}

# Function to run all tests
run_all_tests() {
    echo "🧪 Agentic AI Customer Support - Helm Chart Testing"
    echo "=================================================="
    echo ""
    
    local tests=(
        "test_chart_structure"
        "test_helm_lint"
        "test_template_rendering_default"
        "test_template_rendering_aws"
        "test_template_rendering_azure"
        "test_template_rendering_gcp"
        "test_yaml_validation"
        "test_resource_validation"
        "test_dependencies"
        "test_values_validation"
    )
    
    local passed=0
    local failed=0
    
    for test in "${tests[@]}"; do
        echo ""
        if $test; then
            ((passed++))
        else
            ((failed++))
        fi
    done
    
    echo ""
    echo "📊 Test Results:"
    echo "==============="
    echo "✅ Passed: $passed"
    echo "❌ Failed: $failed"
    echo "📁 Total:  $((passed + failed))"
    
    if [ $failed -eq 0 ]; then
        print_status "🎉 All tests passed! Helm chart is ready for deployment."
        return 0
    else
        print_error "❌ $failed test(s) failed. Please fix the issues before deployment."
        return 1
    fi
}

# Function to clean up test files
cleanup() {
    print_status "Cleaning up test files..."
    rm -f /tmp/helm-test-*.yaml
}

# Help function
show_help() {
    cat << EOF
Agentic AI Customer Support - Helm Chart Testing Script

Usage: $0 [TEST_NAME]

Available Tests:
  structure     - Test chart structure and required files
  lint          - Run Helm lint
  render        - Test template rendering
  yaml          - Validate YAML syntax
  resources     - Validate Kubernetes resources
  dependencies  - Test Helm dependencies
  values        - Validate values files
  all           - Run all tests (default)

Options:
  --help, -h    - Show this help message

Examples:
  $0            # Run all tests
  $0 all        # Run all tests
  $0 lint       # Run only Helm lint
  $0 structure  # Test only chart structure
EOF
}

# Trap to cleanup on exit
trap cleanup EXIT

# Parse command line arguments
case "${1:-all}" in
    structure)
        test_chart_structure
        ;;
    lint)
        test_helm_lint
        ;;
    render)
        test_template_rendering_default
        test_template_rendering_aws
        test_template_rendering_azure
        test_template_rendering_gcp
        ;;
    yaml)
        test_yaml_validation
        ;;
    resources)
        test_resource_validation
        ;;
    dependencies)
        test_dependencies
        ;;
    values)
        test_values_validation
        ;;
    all)
        run_all_tests
        ;;
    --help|-h)
        show_help
        exit 0
        ;;
    *)
        print_error "Unknown test: $1"
        show_help
        exit 1
        ;;
esac
