#!/bin/bash
set -e

# Function to check if a port is available
check_port_available() {
  local port=$1
  nc -z localhost "$port" > /dev/null 2>&1
  if [ $? -eq 0 ]; then
    echo "Port $port is already in use. Cannot start server."
    return 1
  fi
  return 0
}

# Function to start Lambda Tool MCP Server
start_lambda_mcp() {
  if check_port_available $AWS_MCP_LAMBDA_PORT; then
    echo "Starting AWS Lambda Tool MCP Server on port $AWS_MCP_LAMBDA_PORT..."
    python -m awslabs.lambda_tool_mcp_server --port $AWS_MCP_LAMBDA_PORT --aws-region $AWS_REGION &
    echo "Lambda Tool MCP Server started with PID $!"
  fi
}

# Function to start Messaging MCP Server
start_messaging_mcp() {
  if check_port_available $AWS_MCP_MESSAGING_PORT; then
    echo "Starting AWS Messaging MCP Server on port $AWS_MCP_MESSAGING_PORT..."
    python -m aws.messaging_mcp_server --port $AWS_MCP_MESSAGING_PORT --aws-region $AWS_REGION &
    echo "Messaging MCP Server started with PID $!"
  fi
}

# Function to start MQ MCP Server
start_mq_mcp() {
  if check_port_available $AWS_MCP_MQ_PORT; then
    echo "Starting Amazon MQ MCP Server on port $AWS_MCP_MQ_PORT..."
    python -m amazon.mq_mcp_server --port $AWS_MCP_MQ_PORT --aws-region $AWS_REGION &
    echo "MQ MCP Server started with PID $!"
  fi
}

# Setup AWS credentials if provided
setup_aws_credentials() {
  if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Setting up AWS credentials..."
    mkdir -p ~/.aws
    cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = $AWS_ACCESS_KEY_ID
aws_secret_access_key = $AWS_SECRET_ACCESS_KEY
EOF

    cat > ~/.aws/config << EOF
[default]
region = ${AWS_REGION:-us-east-1}
EOF
  fi
}

# Main execution
echo "Starting AWS MCP servers..."

# Setup AWS credentials
setup_aws_credentials

# Load configuration
CONFIG_FILE="/app/config/mcp_servers.json"
if [ -f "$CONFIG_FILE" ]; then
  echo "Loading configuration from $CONFIG_FILE"
  LAMBDA_ENABLED=$(grep -o '"lambda":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  MESSAGING_ENABLED=$(grep -o '"messaging":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  MQ_ENABLED=$(grep -o '"mq":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
else
  echo "Config file not found, using default settings"
  LAMBDA_ENABLED=1
  MESSAGING_ENABLED=1
  MQ_ENABLED=1
fi

# Determine which servers to start based on command line arguments
if [ "$1" = "all" ] || [ -z "$1" ]; then
  # Start all enabled servers
  if [ "$LAMBDA_ENABLED" -gt 0 ]; then
    start_lambda_mcp
  fi
  
  if [ "$MESSAGING_ENABLED" -gt 0 ]; then
    start_messaging_mcp
  fi
  
  if [ "$MQ_ENABLED" -gt 0 ]; then
    start_mq_mcp
  fi
elif [ "$1" = "lambda" ]; then
  start_lambda_mcp
elif [ "$1" = "messaging" ]; then
  start_messaging_mcp
elif [ "$1" = "mq" ]; then
  start_mq_mcp
else
  echo "Unknown argument: $1"
  echo "Usage: $0 [all|lambda|messaging|mq]"
  exit 1
fi

echo "All requested AWS MCP servers started."

# Keep container running
echo "Press CTRL+C to stop all servers"
tail -f /dev/null
