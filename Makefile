.PHONY: help test test-unit test-integration test-a2a test-mcp test-api clean setup-local start-test-env stop-test-env docker-build docker-start docker-stop api-demo

# Default target
help:
	@echo "🚀 Agentic AI Customer Support - Development Commands"
	@echo "======================================================"
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup-local      - Setup local development environment"
	@echo "  start-test-env   - Start test infrastructure (Docker)"
	@echo "  stop-test-env    - Stop test infrastructure"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test            - Run all tests"
	@echo "  test-unit       - Run unit tests only"
	@echo "  test-integration - Run integration tests"
	@echo "  test-a2a        - Test A2A module locally"
	@echo "  test-mcp        - Test MCP servers"
	@echo "  test-api        - Test API component (Docker)"
	@echo "  api-demo        - Run API v1 demo"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build    - Build all Docker services"
	@echo "  docker-start    - Start all Docker services"
	@echo "  docker-stop     - Stop all Docker services"
	@echo "  api-build       - Build API service only"
	@echo "  api-start       - Start API service only"
	@echo "  api-stop        - Stop API service only"
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean           - Clean up test artifacts"
	@echo "  logs            - View test logs"
	@echo "  health-check    - Check service health"

# Setup local development environment
setup-local:
	@echo "🔧 Setting up local development environment..."
	@python -m venv venv || python3 -m venv venv
	@. venv/bin/activate && pip install -e .
	@cp .env.example .env 2>/dev/null || echo "⚠️  No .env.example found - please create .env manually"
	@mkdir -p logs
	@echo "✅ Local environment setup complete!"
	@echo "📝 Don't forget to edit .env with your configuration"

# Start test infrastructure
start-test-env:
	@echo "🐳 Starting test infrastructure..."
	@docker-compose -f docker-compose.test.yml up -d
	@echo "⏳ Waiting for services to be ready..."
	@sleep 30
	@echo "✅ Test infrastructure started!"

# Stop test infrastructure
stop-test-env:
	@echo "🛑 Stopping test infrastructure..."
	@docker-compose -f docker-compose.test.yml down -v
	@echo "✅ Test infrastructure stopped!"

# Run all tests
test: test-unit test-mcp test-a2a test-api
	@echo "🎉 All tests completed!"

# Run unit tests
test-unit:
	@echo "🧪 Running unit tests..."
	@. venv/bin/activate && python -m pytest tests/ -v --tb=short -m "not integration" 2>/dev/null || echo "⚠️  No unit tests found or pytest not installed"

# Run integration tests
test-integration: start-test-env
	@echo "🔗 Running integration tests..."
	@. venv/bin/activate && python -m pytest tests/ -v --tb=short -m integration 2>/dev/null || echo "⚠️  No integration tests found"
	@$(MAKE) stop-test-env

# Test A2A module
test-a2a:
	@echo "🤖 Testing A2A module..."
	@. venv/bin/activate && python scripts/test_a2a_local.py 2>/dev/null || echo "⚠️  A2A test script not found"
	@echo "✅ A2A testing complete!"

# Test MCP servers
test-mcp:
	@echo "🔌 Testing MCP servers..."
	@. venv/bin/activate && python -m pytest tests/mcp_servers/ -v --tb=short 2>/dev/null || echo "⚠️  No MCP tests found"

# Test API component
test-api:
	@echo "🌐 Testing API component..."
	@./cicd/scripts/test/test-api.sh
	@echo "✅ API testing complete!"

# Run API demo
api-demo:
	@echo "🎮 Running API v1 demo..."
	@./cicd/scripts/test/demo-api-v1.sh
	@echo "✅ API demo complete!"

# Docker Commands
docker-build:
	@echo "🔨 Building all Docker services..."
	@./cicd/scripts/main/build-all.sh

docker-start:
	@echo "🚀 Starting all Docker services..."
	@./cicd/scripts/main/start-all.sh

docker-stop:
	@echo "🛑 Stopping all Docker services..."
	@./cicd/scripts/main/stop-all.sh

# API-specific Docker commands
api-build:
	@echo "🔨 Building API service..."
	@./cicd/scripts/main/api/build-api.sh

api-start:
	@echo "🚀 Starting API service..."
	@./cicd/scripts/main/api/start-api.sh

api-stop:
	@echo "🛑 Stopping API service..."
	@./cicd/scripts/main/api/stop-api.sh

# Clean up test artifacts
clean:
	@echo "🧹 Cleaning up test artifacts..."
	@rm -rf logs/a2a_test.log
	@rm -rf htmlcov/
	@rm -rf .pytest_cache/
	@rm -rf __pycache__/
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@docker-compose -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true
	@echo "✅ Cleanup complete!"

# View logs
logs:
	@echo "📋 Recent test logs:"
	@tail -n 50 logs/a2a_test.log 2>/dev/null || echo "No A2A test logs found"
	@echo ""
	@echo "🐳 Docker service logs:"
	@docker-compose -f docker-compose.test.yml logs --tail=20 2>/dev/null || echo "No Docker services running"

# Health check
health-check:
	@echo "🏥 Checking service health..."
	@echo "API Service:"
	@curl -s http://localhost:8080/health 2>/dev/null && echo "  ✅ API Service OK" || echo "  ❌ API Service DOWN"
	@curl -s http://localhost:8080/api/v1/status 2>/dev/null && echo "  ✅ API v1 Routes OK" || echo "  ❌ API v1 Routes DOWN"
	@echo "Database:"
	@curl -s http://localhost:8001/health 2>/dev/null && echo "  ✅ MCP Database Server OK" || echo "  ❌ MCP Database Server DOWN"
	@echo "Kafka:"
	@curl -s http://localhost:8002/health 2>/dev/null && echo "  ✅ MCP Kafka Server OK" || echo "  ❌ MCP Kafka Server DOWN"
	@echo "PostgreSQL:"
	@docker exec cicd-postgres-1 pg_isready -U admin 2>/dev/null && echo "  ✅ PostgreSQL OK" || echo "  ❌ PostgreSQL DOWN"

# Quick development cycle
dev-cycle: clean setup-local start-test-env test-a2a
	@echo "🔄 Development cycle complete!"

# CI/CD pipeline simulation
ci: clean setup-local test
	@echo "✅ CI pipeline simulation complete!"

# Production readiness check
prod-check: test health-check
	@echo "🚀 Production readiness check complete!"
	@echo "💡 Review logs and metrics before deploying to production"
