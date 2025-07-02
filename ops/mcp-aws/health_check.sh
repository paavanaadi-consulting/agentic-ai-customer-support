#!/bin/bash
set -e

# Function to check if a port is open
check_port() {
  local port=$1
  local service=$2
  nc -z localhost "$port" > /dev/null 2>&1
  if [ $? -eq 0 ]; then
    echo "✅ $service MCP Server is running on port $port"
    return 0
  else
    echo "❌ $service MCP Server is NOT running on port $port"
    return 1
  fi
}

# Check all services
echo "Checking AWS MCP Servers health..."

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

# Check services based on configuration
HEALTHY=true

if [ "$LAMBDA_ENABLED" -gt 0 ]; then
  check_port "$AWS_MCP_LAMBDA_PORT" "Lambda Tool" || HEALTHY=false
fi

if [ "$MESSAGING_ENABLED" -gt 0 ]; then
  check_port "$AWS_MCP_MESSAGING_PORT" "Messaging" || HEALTHY=false
fi

if [ "$MQ_ENABLED" -gt 0 ]; then
  check_port "$AWS_MCP_MQ_PORT" "MQ" || HEALTHY=false
fi

# Check memory usage
echo "Checking memory usage..."
FREE_MEM=$(free -m | awk '/^Mem:/{print $4}')
echo "Free memory: ${FREE_MEM}MB"
if [ "$FREE_MEM" -lt 100 ]; then
  echo "❌ Low memory: ${FREE_MEM}MB"
  HEALTHY=false
else
  echo "✅ Memory OK: ${FREE_MEM}MB"
fi

# Check CPU usage
echo "Checking CPU usage..."
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}' | cut -d. -f1)
echo "CPU usage: ${CPU_USAGE}%"
if [ "$CPU_USAGE" -gt 90 ]; then
  echo "❌ High CPU usage: ${CPU_USAGE}%"
  HEALTHY=false
else
  echo "✅ CPU usage OK: ${CPU_USAGE}%"
fi

# Return overall health status
if [ "$HEALTHY" = true ]; then
  echo "All checked services are healthy!"
  exit 0
else
  echo "One or more services are unhealthy!"
  exit 1
fi
