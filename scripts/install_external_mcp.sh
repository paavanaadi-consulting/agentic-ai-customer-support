#!/bin/bash
# Enhanced installation script with external MCP packages

echo "🚀 Installing Agentic AI Customer Support with External MCP Packages"
echo "=================================================================="

# Step 1: Install base requirements
echo "📦 Installing base requirements..."
pip install -r requirements.txt

# Step 2: Install external MCP packages
echo "🔌 Installing external MCP packages..."

# Install postgres-mcp
echo "Installing postgres-mcp from GitHub..."
pip install git+https://github.com/crystaldba/postgres-mcp.git

# Note: Kafka MCP (Confluent) is handled via Docker
echo "Note: Kafka MCP (Confluent) will be installed via Docker - see docker-compose.yml"

# Verify installation
echo "🔍 Verifying installations..."

# Check postgres-mcp
python -c "
try:
    import postgres_mcp
    print('✅ postgres-mcp installed successfully')
except ImportError as e:
    print(f'❌ postgres-mcp installation failed: {e}')
"

# Note: kafka-mcp (Confluent) will be available via Docker
echo "✅ kafka-mcp (Confluent) will be available via Docker - no local installation needed"

# Check other dependencies
python -c "
import fastapi, uvicorn, psycopg2, boto3
print('✅ Core dependencies available')
"

echo ""
echo "📋 External MCP Package Information:"
echo "======================================"
echo "postgres-mcp: Advanced PostgreSQL MCP server"
echo "  - Source: https://github.com/crystaldba/postgres-mcp"
echo "  - Features: Schema introspection, query optimization, security"
echo "  - Integration: Wrapped in mcp/postgres_mcp_wrapper.py"
echo ""
echo "kafka-mcp (Confluent): Official Confluent Kafka MCP server (Node.js)"
echo "  - Source: https://github.com/confluentinc/mcp-confluent"
echo "  - Features: Publish, consume, topic management, cluster health (via Docker)"
echo "  - Integration: Wrapped in mcp/kafka_mcp_wrapper.py (HTTP communication)"
echo ""
echo "Our custom MCP servers:"
echo "  - Base MCP: mcp/base_mcp_server.py (base class for custom servers)"
echo ""
echo "External MCP integration:"
echo "  - AWS MCP Wrapper: mcp/aws_mcp_wrapper.py (external awslabs packages)"
echo "  - Postgres MCP Wrapper: mcp/postgres_mcp_wrapper.py (external postgres-mcp)"
echo "  - Kafka MCP Wrapper: mcp/kafka_mcp_wrapper.py (external Confluent MCP via Docker)"
echo ""
echo "✅ Installation complete!"
echo "Installing external AWS MCP packages..."

# Install AWS MCP packages via uvx
uvx install awslabs.lambda-tool-mcp-server@latest
if [ $? -eq 0 ]; then
    echo "✅ AWS Lambda Tool MCP server installed successfully"
else
    echo "❌ Failed to install AWS Lambda Tool MCP server"
fi

uvx install awslabs.core-mcp-server@latest
if [ $? -eq 0 ]; then
    echo "✅ AWS Core MCP server installed successfully"
else
    echo "❌ Failed to install AWS Core MCP server"
fi

uvx install awslabs.aws-documentation-mcp-server@latest
if [ $? -eq 0 ]; then
    echo "✅ AWS Documentation MCP server installed successfully"
else
    echo "❌ Failed to install AWS Documentation MCP server"
fi

echo ""
echo "Verifying AWS MCP installations..."
echo "AWS MCP packages available via uvx:"
uvx list | grep awslabs || echo "No AWS MCP packages found in uvx"

echo ""
echo "Note: External MCP servers are configured to use:"
echo "  - AWS MCP: mcp/aws_mcp_wrapper.py (external packages only)"
echo "  - AWS MCP: config/aws_mcp.env for configuration"

echo ""
echo "Next steps:"
echo "1. Configure database connection in config/postgres_mcp.env"
echo "2. Configure AWS connection in config/aws_mcp.env"
echo "3. Set up AWS credentials (aws configure or environment variables)"
echo "4. Run tests: python scripts/test_native.py"
echo "5. Start the application: uvicorn main:app --reload"
