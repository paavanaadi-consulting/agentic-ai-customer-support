#!/bin/bash
# Script to test external AWS MCP server integration

# Set the AWS region if not provided
AWS_REGION=${AWS_REGION:-us-east-1}

# Function to show usage
show_usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  --lambda <function-name>  Specify Lambda function to test"
  echo "  --topic <topic-arn>       Specify SNS topic ARN to test"
  echo "  --queue <queue-url>       Specify SQS queue URL to test"
  echo "  --broker <broker-id>      Specify MQ broker ID to test"
  echo "  --test <service>          Specify service to test (lambda, messaging, mq, all)"
  echo "  --region <region>         Specify AWS region (default: $AWS_REGION)"
  echo "  --help                    Show this help message"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --lambda)
      LAMBDA_FUNCTION="$2"
      shift 2
      ;;
    --topic)
      SNS_TOPIC="$2"
      shift 2
      ;;
    --queue)
      SQS_QUEUE="$2"
      shift 2
      ;;
    --broker)
      MQ_BROKER="$2"
      shift 2
      ;;
    --test)
      TEST_SERVICE="$2"
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

# Set environment variables for the test
export AWS_REGION

# Build the command
CMD="python scripts/test_external_aws_mcp.py"

if [[ -n "$LAMBDA_FUNCTION" ]]; then
  CMD="$CMD --lambda $LAMBDA_FUNCTION"
fi

if [[ -n "$SNS_TOPIC" ]]; then
  CMD="$CMD --topic $SNS_TOPIC"
fi

if [[ -n "$SQS_QUEUE" ]]; then
  CMD="$CMD --queue $SQS_QUEUE"
fi

if [[ -n "$MQ_BROKER" ]]; then
  CMD="$CMD --broker $MQ_BROKER"
fi

if [[ -n "$TEST_SERVICE" ]]; then
  CMD="$CMD --test $TEST_SERVICE"
fi

# Run the test
echo "Running test with command: $CMD"
eval $CMD
