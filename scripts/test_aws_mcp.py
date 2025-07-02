"""
Test script for AWS MCP client and server capabilities.
Demonstrates how to use the AWS MCP client to interact with various AWS services.
"""
import os
import asyncio
import json
import logging
from typing import Dict, Any
import sys
import argparse

# Add parent directory to sys.path to allow importing from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mcp.aws_mcp_client import OptimizedAWSMCPClient, AWSClientError
from src.mcp.aws_mcp_server import AWSMCPServer
from config.settings import CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("aws_mcp_test")

async def test_s3_operations(client: OptimizedAWSMCPClient, bucket_name: str):
    """Test S3 operations using AWS MCP client."""
    logger.info("Testing S3 operations...")
    
    try:
        # List all buckets
        logger.info("Listing S3 buckets...")
        buckets = await client.list_s3_buckets()
        logger.info(f"Found {len(buckets)} buckets")
        
        # Test if the specified bucket exists
        bucket_exists = any(b["Name"] == bucket_name for b in buckets)
        if not bucket_exists:
            logger.warning(f"Bucket '{bucket_name}' not found, skipping further S3 tests")
            return
        
        # Create a test file in the bucket
        test_key = "aws_mcp_test_file.json"
        test_content = {
            "message": "Hello from AWS MCP Client",
            "timestamp": "2025-07-02T12:00:00Z",
            "test": True
        }
        
        logger.info(f"Uploading test file to S3 bucket '{bucket_name}'...")
        upload_result = await client.put_s3_object(
            bucket=bucket_name,
            key=test_key,
            body=json.dumps(test_content),
            content_type="application/json"
        )
        logger.info(f"Upload successful: {upload_result}")
        
        # List objects in the bucket
        logger.info(f"Listing objects in bucket '{bucket_name}'...")
        objects = await client.list_s3_objects(bucket=bucket_name)
        logger.info(f"Found {len(objects.get('Objects', []))} objects")
        
        # Get the uploaded file
        logger.info(f"Getting test file from S3...")
        s3_object = await client.get_s3_object(bucket=bucket_name, key=test_key)
        if s3_object.get('IsBase64Encoded', False):
            logger.info("Content is base64 encoded")
        else:
            content = s3_object.get('Body', '')
            logger.info(f"Retrieved content: {content}")
        
        logger.info("S3 operations completed successfully")
    except AWSClientError as e:
        logger.error(f"S3 operations failed: {e}")

async def test_lambda_operations(client: OptimizedAWSMCPClient, function_name: str = None):
    """Test Lambda operations using AWS MCP client."""
    logger.info("Testing Lambda operations...")
    
    try:
        # List Lambda functions
        logger.info("Listing Lambda functions...")
        functions = await client.list_lambda_functions()
        logger.info(f"Found {len(functions)} Lambda functions")
        
        # If no function name provided, use the first one from the list if available
        if not function_name and functions:
            function_name = functions[0].get('FunctionName')
            logger.info(f"Using first available function: {function_name}")
        
        if function_name:
            # Invoke the Lambda function
            logger.info(f"Invoking Lambda function '{function_name}'...")
            payload = {
                "test": True,
                "message": "Test from AWS MCP Client",
                "source": "mcp_test_script"
            }
            
            response = await client.invoke_lambda(
                function_name=function_name,
                payload=payload
            )
            
            logger.info(f"Lambda invocation status code: {response.get('StatusCode')}")
            logger.info(f"Response payload: {response.get('Payload')}")
        else:
            logger.warning("No Lambda function available to test invocation")
        
        logger.info("Lambda operations completed successfully")
    except AWSClientError as e:
        logger.error(f"Lambda operations failed: {e}")

async def test_sqs_operations(client: OptimizedAWSMCPClient, queue_url: str = None):
    """Test SQS operations using AWS MCP client."""
    if not queue_url:
        logger.warning("No SQS queue URL provided, skipping SQS tests")
        return
    
    logger.info("Testing SQS operations...")
    
    try:
        # Send a message to the queue
        message = {
            "source": "aws_mcp_test",
            "action": "test_message",
            "timestamp": "2025-07-02T12:00:00Z"
        }
        
        logger.info(f"Sending message to SQS queue: {queue_url}")
        send_result = await client.send_sqs_message(
            queue_url=queue_url,
            message_body=json.dumps(message),
            message_attributes={
                "test_attribute": "test_value",
                "numeric_attribute": 123
            }
        )
        logger.info(f"Message sent with ID: {send_result.get('MessageId')}")
        
        # Receive messages from the queue
        logger.info("Receiving messages from SQS queue...")
        messages = await client.receive_sqs_messages(
            queue_url=queue_url,
            max_messages=5,
            wait_time_seconds=5
        )
        
        if messages:
            logger.info(f"Received {len(messages)} messages")
            
            # Delete the received messages
            for message in messages:
                receipt_handle = message.get('ReceiptHandle')
                if receipt_handle:
                    logger.info(f"Deleting message with ID: {message.get('MessageId')}")
                    delete_result = await client.delete_sqs_message(
                        queue_url=queue_url,
                        receipt_handle=receipt_handle
                    )
                    if delete_result.get('success'):
                        logger.info("Message deleted successfully")
        else:
            logger.info("No messages received")
        
        logger.info("SQS operations completed successfully")
    except AWSClientError as e:
        logger.error(f"SQS operations failed: {e}")

async def test_sns_operations(client: OptimizedAWSMCPClient, topic_arn: str = None):
    """Test SNS operations using AWS MCP client."""
    logger.info("Testing SNS operations...")
    
    try:
        # List SNS topics
        logger.info("Listing SNS topics...")
        topics_result = await client.list_sns_topics()
        topics = topics_result.get('Topics', [])
        logger.info(f"Found {len(topics)} SNS topics")
        
        # If no topic ARN provided, use the first one from the list if available
        if not topic_arn and topics:
            topic_arn = topics[0].get('TopicArn')
            logger.info(f"Using first available topic: {topic_arn}")
        
        if topic_arn:
            # Publish a message to the topic
            message = {
                "source": "aws_mcp_test",
                "action": "test_notification",
                "timestamp": "2025-07-02T12:00:00Z"
            }
            
            logger.info(f"Publishing message to SNS topic: {topic_arn}")
            publish_result = await client.publish_sns_message(
                topic_arn=topic_arn,
                message=json.dumps(message),
                subject="AWS MCP Test Notification"
            )
            logger.info(f"Message published with ID: {publish_result.get('MessageId')}")
        else:
            logger.warning("No SNS topic available to test publishing")
        
        logger.info("SNS operations completed successfully")
    except AWSClientError as e:
        logger.error(f"SNS operations failed: {e}")

async def run_tests():
    """Run all AWS MCP client tests."""
    # Get AWS configuration from settings
    aws_config = CONFIG.get("mcp_aws", {})
    aws_access_key_id = aws_config.get("aws_access_key_id")
    aws_secret_access_key = aws_config.get("aws_secret_access_key")
    region_name = aws_config.get("region_name", "us-east-1")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test AWS MCP client and server")
    parser.add_argument("--no-server", action="store_true", help="Don't start the MCP server (connect to existing server)")
    parser.add_argument("--bucket", help="S3 bucket name for testing")
    parser.add_argument("--lambda", dest="lambda_function", help="Lambda function name for testing")
    parser.add_argument("--queue", help="SQS queue URL for testing")
    parser.add_argument("--topic", help="SNS topic ARN for testing")
    args = parser.parse_args()
    
    # Create and start AWS MCP server (if not skipped)
    server = None
    if not args.no_server:
        logger.info("Starting AWS MCP server...")
        server = AWSMCPServer(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            use_external_mcp=False  # Use internal implementation for testing
        )
        await server.start()
        logger.info("AWS MCP server started")
    
    try:
        # Create and connect AWS MCP client
        logger.info("Creating AWS MCP client...")
        client = OptimizedAWSMCPClient(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
        logger.info("Connecting to AWS MCP server...")
        connected = await client.connect()
        if not connected:
            logger.error("Failed to connect to AWS MCP server")
            return
        
        logger.info("AWS MCP client connected successfully")
        
        # Run tests
        bucket_name = args.bucket or aws_config.get("default_bucket")
        if bucket_name:
            await test_s3_operations(client, bucket_name)
        else:
            logger.warning("No S3 bucket specified, skipping S3 tests")
        
        lambda_function = args.lambda_function or aws_config.get("default_lambda")
        await test_lambda_operations(client, lambda_function)
        
        queue_url = args.queue or aws_config.get("default_queue")
        await test_sqs_operations(client, queue_url)
        
        topic_arn = args.topic or aws_config.get("default_topic")
        await test_sns_operations(client, topic_arn)
        
    finally:
        # Clean up
        logger.info("Disconnecting AWS MCP client...")
        await client.disconnect()
        
        if server:
            logger.info("Stopping AWS MCP server...")
            await server.stop()
            logger.info("AWS MCP server stopped")
        
        logger.info("Tests completed")

if __name__ == "__main__":
    asyncio.run(run_tests())
