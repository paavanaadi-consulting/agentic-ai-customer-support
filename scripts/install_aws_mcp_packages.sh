#!/bin/bash
# Script to install official external AWS MCP server packages

# Function to show usage
show_usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  --all                    Install all AWS MCP server packages"
  echo "  --lambda                 Install AWS Lambda Tool MCP Server"
  echo "  --messaging              Install Amazon SNS/SQS MCP Server"
  echo "  --mq                     Install Amazon MQ MCP Server"
  echo "  --help                   Show this help message"
}

# Function to install a specific package
install_package() {
  PACKAGE=$1
  PACKAGE_NAME=$2
  
  echo "Installing $PACKAGE_NAME..."
  if pip install $PACKAGE; then
    echo "✅ Successfully installed $PACKAGE_NAME"
  else
    echo "❌ Failed to install $PACKAGE_NAME"
    return 1
  fi
}

# Parse command line arguments
if [ $# -eq 0 ]; then
  show_usage
  exit 1
fi

INSTALL_ALL=false
INSTALL_LAMBDA=false
INSTALL_MESSAGING=false
INSTALL_MQ=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --all)
      INSTALL_ALL=true
      shift
      ;;
    --lambda)
      INSTALL_LAMBDA=true
      shift
      ;;
    --messaging)
      INSTALL_MESSAGING=true
      shift
      ;;
    --mq)
      INSTALL_MQ=true
      shift
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

# Install packages based on arguments
if [ "$INSTALL_ALL" = true ] || [ "$INSTALL_LAMBDA" = true ]; then
  install_package "awslabs-lambda-tool-mcp-server" "AWS Lambda Tool MCP Server"
fi

if [ "$INSTALL_ALL" = true ] || [ "$INSTALL_MESSAGING" = true ]; then
  install_package "aws-messaging-mcp-server" "Amazon SNS/SQS MCP Server"
fi

if [ "$INSTALL_ALL" = true ] || [ "$INSTALL_MQ" = true ]; then
  install_package "amazon-mq-mcp-server" "Amazon MQ MCP Server"
fi

echo "Installation completed!"
