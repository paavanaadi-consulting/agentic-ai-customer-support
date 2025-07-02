#!/bin/bash
# Start all external AWS MCP servers for the Agentic AI Customer Support System

# Ensure we're in the correct directory
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR/.."

# Function to show usage
show_usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  --lambda-port <port>     Port for Lambda Tool MCP Server (default: 8766)"
  echo "  --messaging-port <port>  Port for Messaging MCP Server (default: 8767)"
  echo "  --mq-port <port>         Port for MQ MCP Server (default: 8768)"
  echo "  --region <region>        AWS region (default: us-east-1)"
  echo "  --help                   Show this help message"
}

# Default values
LAMBDA_PORT=8766
MESSAGING_PORT=8767
MQ_PORT=8768
AWS_REGION=${AWS_REGION:-us-east-1}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --lambda-port)
      LAMBDA_PORT="$2"
      shift 2
      ;;
    --messaging-port)
      MESSAGING_PORT="$2"
      shift 2
      ;;
    --mq-port)
      MQ_PORT="$2"
      shift 2
      ;;
    --region)
      AWS_REGION="$2"
      shift 2
      ;;
    --help)
      show_usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      show_usage
      exit 1
      ;;
  esac
done

# Install packages if needed
echo "Checking if external AWS MCP server packages are installed..."
./scripts/install_aws_mcp_packages.sh --all

# Check if ports are already in use
function is_port_in_use() {
  local port=$1
  if nc -z localhost "$port" >/dev/null 2>&1; then
    echo "Port $port is already in use. Another server might be running."
    return 0
  else
    return 1
  fi
}

# Start Lambda Tool MCP Server
if ! is_port_in_use "$LAMBDA_PORT"; then
  echo "Starting AWS Lambda Tool MCP Server on port $LAMBDA_PORT..."
  python -m awslabs.lambda_tool_mcp_server --port "$LAMBDA_PORT" --aws-region "$AWS_REGION" &
  LAMBDA_PID=$!
  echo "Lambda Tool MCP Server started with PID $LAMBDA_PID"
fi

# Start Messaging MCP Server
if ! is_port_in_use "$MESSAGING_PORT"; then
  echo "Starting AWS Messaging MCP Server on port $MESSAGING_PORT..."
  python -m aws.messaging_mcp_server --port "$MESSAGING_PORT" --aws-region "$AWS_REGION" &
  MESSAGING_PID=$!
  echo "Messaging MCP Server started with PID $MESSAGING_PID"
fi

# Start MQ MCP Server
if ! is_port_in_use "$MQ_PORT"; then
  echo "Starting Amazon MQ MCP Server on port $MQ_PORT..."
  python -m amazon.mq_mcp_server --port "$MQ_PORT" --aws-region "$AWS_REGION" &
  MQ_PID=$!
  echo "MQ MCP Server started with PID $MQ_PID"
fi

# Save PIDs to a file for later cleanup
echo "$LAMBDA_PID $MESSAGING_PID $MQ_PID" > .aws_mcp_pids

echo "All external AWS MCP servers started."
echo "Use './scripts/stop_external_aws_mcp_servers.sh' to stop the servers."

# Keep running until user presses Ctrl+C
echo "Press Ctrl+C to stop all servers"
trap "kill $LAMBDA_PID $MESSAGING_PID $MQ_PID 2>/dev/null; rm .aws_mcp_pids 2>/dev/null; echo 'Servers stopped'; exit 0" INT
wait
