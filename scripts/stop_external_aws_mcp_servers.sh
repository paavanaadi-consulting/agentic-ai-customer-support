#!/bin/bash
# Stop all external AWS MCP servers for the Agentic AI Customer Support System

# Ensure we're in the correct directory
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR/.."

# Check if PID file exists
if [ -f .aws_mcp_pids ]; then
  echo "Stopping external AWS MCP servers..."
  
  # Read PIDs from file
  read -r LAMBDA_PID MESSAGING_PID MQ_PID < .aws_mcp_pids
  
  # Kill processes
  if [ -n "$LAMBDA_PID" ]; then
    echo "Stopping Lambda Tool MCP Server (PID $LAMBDA_PID)..."
    kill "$LAMBDA_PID" 2>/dev/null || echo "Lambda server already stopped"
  fi
  
  if [ -n "$MESSAGING_PID" ]; then
    echo "Stopping Messaging MCP Server (PID $MESSAGING_PID)..."
    kill "$MESSAGING_PID" 2>/dev/null || echo "Messaging server already stopped"
  fi
  
  if [ -n "$MQ_PID" ]; then
    echo "Stopping MQ MCP Server (PID $MQ_PID)..."
    kill "$MQ_PID" 2>/dev/null || echo "MQ server already stopped"
  fi
  
  # Remove PID file
  rm .aws_mcp_pids
  echo "All external AWS MCP servers stopped"
else
  echo "No external AWS MCP servers found running"
  
  # Try to find and kill any running servers based on process name
  echo "Checking for any running servers by name..."
  pkill -f "lambda_tool_mcp_server" || echo "No Lambda server found"
  pkill -f "messaging_mcp_server" || echo "No Messaging server found"
  pkill -f "mq_mcp_server" || echo "No MQ server found"
fi
