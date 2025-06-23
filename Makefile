.PHONY: help test test-unit test-integration test-a2a test-mcp clean setup-local start-test-env stop-test-env

# Default target
help:
	@echo "🚀 Agentic AI Customer Support - Testing Commands"
	@echo "=================================================="
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
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean           - Clean up test artifacts"
	@echo "  logs            - View test logs"
	@echo "  health-check    - Check service health"

# Setup local development environment
setup-local:
	@echo "🔧 Setting up local development environment..."
	@python -m venv venv || python3 -m venv venv
	@. venv/bin/activate && pip install -r requirements.txt
	@cp .env.local.example .env.local
	@mkdir -p logs
	@echo "✅ Local environment setup complete!"
	@echo "📝 Don't forget to edit .env.local with your configuration"

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
test: test-unit test-mcp test-a2a
	@echo "🎉 All tests completed!"

# Run unit tests
test-unit:
	@echo "🧪 Running unit tests..."
	@. venv/bin/activate && python -m pytest tests/ -v --tb=short -m "not integration"

# Run integration tests
test-integration: start-test-env
	@echo "🔗 Running integration tests..."
	@. venv/bin/activate && python -m pytest tests/ -v --tb=short -m integration
	@$(MAKE) stop-test-env

# Test A2A module
test-a2a: start-test-env
	@echo "🤖 Testing A2A module..."
	@. venv/bin/activate && python scripts/test_a2a_local.py
	@echo "✅ A2A testing complete!"

# Test MCP servers
test-mcp:
	@echo "🔌 Testing MCP servers..."
	@. venv/bin/activate && python -m pytest tests/mcp_servers/ -v --tb=short

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
	@echo "Database:"
	@curl -s http://localhost:8001/health 2>/dev/null && echo "  ✅ MCP Database Server OK" || echo "  ❌ MCP Database Server DOWN"
	@echo "Kafka:"
	@curl -s http://localhost:8002/health 2>/dev/null && echo "  ✅ MCP Kafka Server OK" || echo "  ❌ MCP Kafka Server DOWN"
	@echo "PostgreSQL:"
	@docker exec $$(docker-compose -f docker-compose.test.yml ps -q postgres-test 2>/dev/null) pg_isready -U admin 2>/dev/null && echo "  ✅ PostgreSQL OK" || echo "  ❌ PostgreSQL DOWN"

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
