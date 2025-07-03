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
    python -m lambda_tool_mcp_server.main --port $AWS_MCP_LAMBDA_PORT --aws-region $AWS_REGION &
    echo "Lambda Tool MCP Server started with PID $!"
  fi
}

# Function to start Messaging MCP Server
start_messaging_mcp() {
  if check_port_available $AWS_MCP_MESSAGING_PORT; then
    echo "Starting AWS Messaging MCP Server on port $AWS_MCP_MESSAGING_PORT..."
    python -m amazon_sns_sqs_mcp_server.main --port $AWS_MCP_MESSAGING_PORT --aws-region $AWS_REGION &
    echo "Messaging MCP Server started with PID $!"
  fi
}

# Function to start MQ MCP Server
start_mq_mcp() {
  if check_port_available $AWS_MCP_MQ_PORT; then
    echo "Starting Amazon MQ MCP Server on port $AWS_MCP_MQ_PORT..."
    python -m amazon_mq_mcp_server.main --port $AWS_MCP_MQ_PORT --aws-region $AWS_REGION &
    echo "MQ MCP Server started with PID $!"
  fi
}

# Function to start Kendra MCP Server
start_kendra_mcp() {
  if check_port_available $AWS_MCP_KENDRA_PORT; then
    echo "Starting Amazon Kendra MCP Server on port $AWS_MCP_KENDRA_PORT..."
    python -m amazon_kendra_index_mcp_server.main --port $AWS_MCP_KENDRA_PORT --aws-region $AWS_REGION &
    echo "Kendra MCP Server started with PID $!"
  fi
}

# Function to start Keyspaces MCP Server
start_keyspaces_mcp() {
  if check_port_available $AWS_MCP_KEYSPACES_PORT; then
    echo "Starting Amazon Keyspaces MCP Server on port $AWS_MCP_KEYSPACES_PORT..."
    python -m amazon_keyspaces_mcp_server.main --port $AWS_MCP_KEYSPACES_PORT --aws-region $AWS_REGION &
    echo "Keyspaces MCP Server started with PID $!"
  fi
}

# Function to start Neptune MCP Server
start_neptune_mcp() {
  if check_port_available $AWS_MCP_NEPTUNE_PORT; then
    echo "Starting Amazon Neptune MCP Server on port $AWS_MCP_NEPTUNE_PORT..."
    python -m amazon_neptune_mcp_server.main --port $AWS_MCP_NEPTUNE_PORT --aws-region $AWS_REGION &
    echo "Neptune MCP Server started with PID $!"
  fi
}

# Function to start QIndex MCP Server
start_qindex_mcp() {
  if check_port_available $AWS_MCP_QINDEX_PORT; then
    echo "Starting Amazon QIndex MCP Server on port $AWS_MCP_QINDEX_PORT..."
    python -m amazon_qindex_mcp_server.main --port $AWS_MCP_QINDEX_PORT --aws-region $AWS_REGION &
    echo "QIndex MCP Server started with PID $!"
  fi
}

# Function to start Rekognition MCP Server
start_rekognition_mcp() {
  if check_port_available $AWS_MCP_REKOGNITION_PORT; then
    echo "Starting Amazon Rekognition MCP Server on port $AWS_MCP_REKOGNITION_PORT..."
    python -m amazon_rekognition_mcp_server.main --port $AWS_MCP_REKOGNITION_PORT --aws-region $AWS_REGION &
    echo "Rekognition MCP Server started with PID $!"
  fi
}

# Function to start Bedrock Data Automation MCP Server
start_bedrock_data_mcp() {
  if check_port_available $AWS_MCP_BEDROCK_DATA_PORT; then
    echo "Starting AWS Bedrock Data Automation MCP Server on port $AWS_MCP_BEDROCK_DATA_PORT..."
    python -m aws_bedrock_data_automation_mcp_server.main --port $AWS_MCP_BEDROCK_DATA_PORT --aws-region $AWS_REGION &
    echo "Bedrock Data Automation MCP Server started with PID $!"
  fi
}

# Function to start AWS Diagram MCP Server
start_diagram_mcp() {
  if check_port_available $AWS_MCP_DIAGRAM_PORT; then
    echo "Starting AWS Diagram MCP Server on port $AWS_MCP_DIAGRAM_PORT..."
    python -m aws_diagram_mcp_server.main --port $AWS_MCP_DIAGRAM_PORT --aws-region $AWS_REGION &
    echo "AWS Diagram MCP Server started with PID $!"
  fi
}

# Function to start AWS Documentation MCP Server
start_documentation_mcp() {
  if check_port_available $AWS_MCP_DOCUMENTATION_PORT; then
    echo "Starting AWS Documentation MCP Server on port $AWS_MCP_DOCUMENTATION_PORT..."
    python -m aws_documentation_mcp_server.main --port $AWS_MCP_DOCUMENTATION_PORT --aws-region $AWS_REGION &
    echo "AWS Documentation MCP Server started with PID $!"
  fi
}

# Function to start AWS HealthOmics MCP Server
start_healthomics_mcp() {
  if check_port_available $AWS_MCP_HEALTHOMICS_PORT; then
    echo "Starting AWS HealthOmics MCP Server on port $AWS_MCP_HEALTHOMICS_PORT..."
    python -m aws_healthomics_mcp_server.main --port $AWS_MCP_HEALTHOMICS_PORT --aws-region $AWS_REGION &
    echo "AWS HealthOmics MCP Server started with PID $!"
  fi
}

# Function to start AWS Location MCP Server
start_location_mcp() {
  if check_port_available $AWS_MCP_LOCATION_PORT; then
    echo "Starting AWS Location MCP Server on port $AWS_MCP_LOCATION_PORT..."
    python -m aws_location_mcp_server.main --port $AWS_MCP_LOCATION_PORT --aws-region $AWS_REGION &
    echo "AWS Location MCP Server started with PID $!"
  fi
}

# Function to start AWS Serverless MCP Server
start_serverless_mcp() {
  if check_port_available $AWS_MCP_SERVERLESS_PORT; then
    echo "Starting AWS Serverless MCP Server on port $AWS_MCP_SERVERLESS_PORT..."
    python -m aws_serverless_mcp_server.main --port $AWS_MCP_SERVERLESS_PORT --aws-region $AWS_REGION &
    echo "AWS Serverless MCP Server started with PID $!"
  fi
}

# Function to start AWS Support MCP Server
start_support_mcp() {
  if check_port_available $AWS_MCP_SUPPORT_PORT; then
    echo "Starting AWS Support MCP Server on port $AWS_MCP_SUPPORT_PORT..."
    python -m aws_support_mcp_server.main --port $AWS_MCP_SUPPORT_PORT --aws-region $AWS_REGION &
    echo "AWS Support MCP Server started with PID $!"
  fi
}

# Function to start Bedrock KB Retrieval MCP Server
start_bedrock_kb_mcp() {
  if check_port_available $AWS_MCP_BEDROCK_KB_PORT; then
    echo "Starting Bedrock KB Retrieval MCP Server on port $AWS_MCP_BEDROCK_KB_PORT..."
    python -m bedrock_kb_retrieval_mcp_server.main --port $AWS_MCP_BEDROCK_KB_PORT --aws-region $AWS_REGION &
    echo "Bedrock KB Retrieval MCP Server started with PID $!"
  fi
}

# Function to start CDK MCP Server
start_cdk_mcp() {
  if check_port_available $AWS_MCP_CDK_PORT; then
    echo "Starting CDK MCP Server on port $AWS_MCP_CDK_PORT..."
    python -m cdk_mcp_server.main --port $AWS_MCP_CDK_PORT --aws-region $AWS_REGION &
    echo "CDK MCP Server started with PID $!"
  fi
}

# Function to start CloudFormation MCP Server
start_cfn_mcp() {
  if check_port_available $AWS_MCP_CFN_PORT; then
    echo "Starting CloudFormation MCP Server on port $AWS_MCP_CFN_PORT..."
    python -m cfn_mcp_server.main --port $AWS_MCP_CFN_PORT --aws-region $AWS_REGION &
    echo "CloudFormation MCP Server started with PID $!"
  fi
}

# Function to start CloudWatch Logs MCP Server
start_cloudwatch_logs_mcp() {
  if check_port_available $AWS_MCP_CLOUDWATCH_LOGS_PORT; then
    echo "Starting CloudWatch Logs MCP Server on port $AWS_MCP_CLOUDWATCH_LOGS_PORT..."
    python -m cloudwatch_logs_mcp_server.main --port $AWS_MCP_CLOUDWATCH_LOGS_PORT --aws-region $AWS_REGION &
    echo "CloudWatch Logs MCP Server started with PID $!"
  fi
}

# Function to start Cost Analysis MCP Server
start_cost_analysis_mcp() {
  if check_port_available $AWS_MCP_COST_ANALYSIS_PORT; then
    echo "Starting Cost Analysis MCP Server on port $AWS_MCP_COST_ANALYSIS_PORT..."
    python -m cost_analysis_mcp_server.main --port $AWS_MCP_COST_ANALYSIS_PORT --aws-region $AWS_REGION &
    echo "Cost Analysis MCP Server started with PID $!"
  fi
}

# Function to start Cost Explorer MCP Server
start_cost_explorer_mcp() {
  if check_port_available $AWS_MCP_COST_EXPLORER_PORT; then
    echo "Starting Cost Explorer MCP Server on port $AWS_MCP_COST_EXPLORER_PORT..."
    python -m cost_explorer_mcp_server.main --port $AWS_MCP_COST_EXPLORER_PORT --aws-region $AWS_REGION &
    echo "Cost Explorer MCP Server started with PID $!"
  fi
}

# Function to start DynamoDB MCP Server
start_dynamodb_mcp() {
  if check_port_available $AWS_MCP_DYNAMODB_PORT; then
    echo "Starting DynamoDB MCP Server on port $AWS_MCP_DYNAMODB_PORT..."
    python -m dynamodb_mcp_server.main --port $AWS_MCP_DYNAMODB_PORT --aws-region $AWS_REGION &
    echo "DynamoDB MCP Server started with PID $!"
  fi
}

# Function to start ECS MCP Server
start_ecs_mcp() {
  if check_port_available $AWS_MCP_ECS_PORT; then
    echo "Starting ECS MCP Server on port $AWS_MCP_ECS_PORT..."
    python -m ecs_mcp_server.main --port $AWS_MCP_ECS_PORT --aws-region $AWS_REGION &
    echo "ECS MCP Server started with PID $!"
  fi
}

# Function to start EKS MCP Server
start_eks_mcp() {
  if check_port_available $AWS_MCP_EKS_PORT; then
    echo "Starting EKS MCP Server on port $AWS_MCP_EKS_PORT..."
    python -m eks_mcp_server.main --port $AWS_MCP_EKS_PORT --aws-region $AWS_REGION &
    echo "EKS MCP Server started with PID $!"
  fi
}

# Function to start IAM MCP Server
start_iam_mcp() {
  if check_port_available $AWS_MCP_IAM_PORT; then
    echo "Starting IAM MCP Server on port $AWS_MCP_IAM_PORT..."
    python -m iam_mcp_server.main --port $AWS_MCP_IAM_PORT --aws-region $AWS_REGION &
    echo "IAM MCP Server started with PID $!"
  fi
}

# Function to start Step Functions MCP Server
start_stepfunctions_mcp() {
  if check_port_available $AWS_MCP_STEPFUNCTIONS_PORT; then
    echo "Starting Step Functions MCP Server on port $AWS_MCP_STEPFUNCTIONS_PORT..."
    python -m stepfunctions_tool_mcp_server.main --port $AWS_MCP_STEPFUNCTIONS_PORT --aws-region $AWS_REGION &
    echo "Step Functions MCP Server started with PID $!"
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
  KENDRA_ENABLED=$(grep -o '"kendra":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  KEYSPACES_ENABLED=$(grep -o '"keyspaces":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  NEPTUNE_ENABLED=$(grep -o '"neptune":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  QINDEX_ENABLED=$(grep -o '"qindex":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  REKOGNITION_ENABLED=$(grep -o '"rekognition":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  BEDROCK_DATA_ENABLED=$(grep -o '"bedrock-data":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  DIAGRAM_ENABLED=$(grep -o '"diagram":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  DOCUMENTATION_ENABLED=$(grep -o '"documentation":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  HEALTHOMICS_ENABLED=$(grep -o '"healthomics":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  LOCATION_ENABLED=$(grep -o '"location":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  SERVERLESS_ENABLED=$(grep -o '"serverless":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  SUPPORT_ENABLED=$(grep -o '"support":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  BEDROCK_KB_ENABLED=$(grep -o '"bedrock-kb":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  CDK_ENABLED=$(grep -o '"cdk":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  CFN_ENABLED=$(grep -o '"cfn":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  CLOUDWATCH_LOGS_ENABLED=$(grep -o '"cloudwatch-logs":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  COST_ANALYSIS_ENABLED=$(grep -o '"cost-analysis":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  COST_EXPLORER_ENABLED=$(grep -o '"cost-explorer":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  DYNAMODB_ENABLED=$(grep -o '"dynamodb":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  ECS_ENABLED=$(grep -o '"ecs":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  EKS_ENABLED=$(grep -o '"eks":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  IAM_ENABLED=$(grep -o '"iam":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
  STEPFUNCTIONS_ENABLED=$(grep -o '"stepfunctions":\s*{\s*"enabled":\s*true' "$CONFIG_FILE" | wc -l)
else
  echo "Config file not found, using default settings"
  LAMBDA_ENABLED=1
  MESSAGING_ENABLED=1
  MQ_ENABLED=1
  KENDRA_ENABLED=1
  KEYSPACES_ENABLED=1
  NEPTUNE_ENABLED=1
  QINDEX_ENABLED=1
  REKOGNITION_ENABLED=1
  BEDROCK_DATA_ENABLED=1
  DIAGRAM_ENABLED=1
  DOCUMENTATION_ENABLED=1
  HEALTHOMICS_ENABLED=1
  LOCATION_ENABLED=1
  SERVERLESS_ENABLED=1
  SUPPORT_ENABLED=1
  BEDROCK_KB_ENABLED=1
  CDK_ENABLED=1
  CFN_ENABLED=1
  CLOUDWATCH_LOGS_ENABLED=1
  COST_ANALYSIS_ENABLED=1
  COST_EXPLORER_ENABLED=1
  DYNAMODB_ENABLED=1
  ECS_ENABLED=1
  EKS_ENABLED=1
  IAM_ENABLED=1
  STEPFUNCTIONS_ENABLED=1
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
  
  if [ "$KENDRA_ENABLED" -gt 0 ]; then
    start_kendra_mcp
  fi
  
  if [ "$KEYSPACES_ENABLED" -gt 0 ]; then
    start_keyspaces_mcp
  fi
  
  if [ "$NEPTUNE_ENABLED" -gt 0 ]; then
    start_neptune_mcp
  fi
  
  if [ "$QINDEX_ENABLED" -gt 0 ]; then
    start_qindex_mcp
  fi
  
  if [ "$REKOGNITION_ENABLED" -gt 0 ]; then
    start_rekognition_mcp
  fi
  
  if [ "$BEDROCK_DATA_ENABLED" -gt 0 ]; then
    start_bedrock_data_mcp
  fi
  
  if [ "$DIAGRAM_ENABLED" -gt 0 ]; then
    start_diagram_mcp
  fi
  
  if [ "$DOCUMENTATION_ENABLED" -gt 0 ]; then
    start_documentation_mcp
  fi
  
  if [ "$HEALTHOMICS_ENABLED" -gt 0 ]; then
    start_healthomics_mcp
  fi
  
  if [ "$LOCATION_ENABLED" -gt 0 ]; then
    start_location_mcp
  fi
  
  if [ "$SERVERLESS_ENABLED" -gt 0 ]; then
    start_serverless_mcp
  fi
  
  if [ "$SUPPORT_ENABLED" -gt 0 ]; then
    start_support_mcp
  fi
  
  if [ "$BEDROCK_KB_ENABLED" -gt 0 ]; then
    start_bedrock_kb_mcp
  fi
  
  if [ "$CDK_ENABLED" -gt 0 ]; then
    start_cdk_mcp
  fi
  
  if [ "$CFN_ENABLED" -gt 0 ]; then
    start_cfn_mcp
  fi
  
  if [ "$CLOUDWATCH_LOGS_ENABLED" -gt 0 ]; then
    start_cloudwatch_logs_mcp
  fi
  
  if [ "$COST_ANALYSIS_ENABLED" -gt 0 ]; then
    start_cost_analysis_mcp
  fi
  
  if [ "$COST_EXPLORER_ENABLED" -gt 0 ]; then
    start_cost_explorer_mcp
  fi
  
  if [ "$DYNAMODB_ENABLED" -gt 0 ]; then
    start_dynamodb_mcp
  fi
  
  if [ "$ECS_ENABLED" -gt 0 ]; then
    start_ecs_mcp
  fi
  
  if [ "$EKS_ENABLED" -gt 0 ]; then
    start_eks_mcp
  fi
  
  if [ "$IAM_ENABLED" -gt 0 ]; then
    start_iam_mcp
  fi
  
  if [ "$STEPFUNCTIONS_ENABLED" -gt 0 ]; then
    start_stepfunctions_mcp
  fi
elif [ "$1" = "lambda" ]; then
  start_lambda_mcp
elif [ "$1" = "messaging" ]; then
  start_messaging_mcp
elif [ "$1" = "mq" ]; then
  start_mq_mcp
elif [ "$1" = "kendra" ]; then
  start_kendra_mcp
elif [ "$1" = "keyspaces" ]; then
  start_keyspaces_mcp
elif [ "$1" = "neptune" ]; then
  start_neptune_mcp
elif [ "$1" = "qindex" ]; then
  start_qindex_mcp
elif [ "$1" = "rekognition" ]; then
  start_rekognition_mcp
elif [ "$1" = "bedrock-data" ]; then
  start_bedrock_data_mcp
elif [ "$1" = "diagram" ]; then
  start_diagram_mcp
elif [ "$1" = "documentation" ]; then
  start_documentation_mcp
elif [ "$1" = "healthomics" ]; then
  start_healthomics_mcp
elif [ "$1" = "location" ]; then
  start_location_mcp
elif [ "$1" = "serverless" ]; then
  start_serverless_mcp
elif [ "$1" = "support" ]; then
  start_support_mcp
elif [ "$1" = "bedrock-kb" ]; then
  start_bedrock_kb_mcp
elif [ "$1" = "cdk" ]; then
  start_cdk_mcp
elif [ "$1" = "cfn" ]; then
  start_cfn_mcp
elif [ "$1" = "cloudwatch-logs" ]; then
  start_cloudwatch_logs_mcp
elif [ "$1" = "cost-analysis" ]; then
  start_cost_analysis_mcp
elif [ "$1" = "cost-explorer" ]; then
  start_cost_explorer_mcp
elif [ "$1" = "dynamodb" ]; then
  start_dynamodb_mcp
elif [ "$1" = "ecs" ]; then
  start_ecs_mcp
elif [ "$1" = "eks" ]; then
  start_eks_mcp
elif [ "$1" = "iam" ]; then
  start_iam_mcp
elif [ "$1" = "stepfunctions" ]; then
  start_stepfunctions_mcp
else
  echo "Unknown argument: $1"
  echo "Usage: $0 [all|lambda|messaging|mq]"
  exit 1
fi

echo "All requested AWS MCP servers started."

# Keep container running
echo "Press CTRL+C to stop all servers"
tail -f /dev/null
