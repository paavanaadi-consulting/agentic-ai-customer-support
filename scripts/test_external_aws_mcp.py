"""
Test script for AWS MCP client with external AWS MCP server integration.
This script demonstrates how to use the AWS MCP client with official external AWS MCP servers.
"""
import os
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
import sys
import argparse

# Add parent directory to sys.path to allow importing from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mcp.aws_mcp_client import OptimizedAWSMCPClient
from src.mcp.mcp_client_manager import MCPClientManager
from config.settings import CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("aws_external_mcp_test")

async def test_lambda_with_external_mcp(function_name: str = None):
    """Test Lambda operations using AWS Lambda Tool MCP Server."""
    logger.info("=== Testing Lambda with Lambda Tool MCP Server ===")
    
    # Get AWS configuration from settings
    aws_config = CONFIG.get("mcp_aws", {})
    aws_access_key_id = aws_config.get("aws_access_key_id")
    aws_secret_access_key = aws_config.get("aws_secret_access_key")
    region_name = aws_config.get("region_name", "us-east-1")
    
    # Create MCP client manager
    manager = MCPClientManager()
    
    try:
        # Add AWS client with Lambda Tool MCP Server
        logger.info("Adding AWS client with Lambda Tool MCP Server...")
        await manager.add_aws_client(
            server_id="aws-lambda-mcp",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            use_external_mcp_servers=True,
            service_types=["lambda"]
        )
        
        # Get the AWS client
        aws_client = manager.get_client("aws-lambda-mcp")
        if not aws_client:
            logger.error("Failed to get AWS client")
            return
        
        # List Lambda functions
        logger.info("Listing Lambda functions...")
        functions = await aws_client.list_lambda_functions()
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
                "message": "Test from AWS Lambda Tool MCP Server",
                "source": "mcp_external_test_script"
            }
            
            response = await aws_client.invoke_lambda(
                function_name=function_name,
                payload=payload
            )
            
            logger.info(f"Lambda invocation status code: {response.get('StatusCode')}")
            logger.info(f"Response payload: {response.get('Payload')}")
        else:
            logger.warning("No Lambda function available to test invocation")
    
    except Exception as e:
        logger.error(f"Lambda operations failed: {e}")
    
    finally:
        # Clean up
        await manager.disconnect_all()
        logger.info("Lambda test completed")

async def test_messaging_with_external_mcp(topic_arn: str = None, queue_url: str = None):
    """Test SNS and SQS operations using AWS Messaging MCP Server."""
    logger.info("=== Testing SNS/SQS with Messaging MCP Server ===")
    
    # Get AWS configuration from settings
    aws_config = CONFIG.get("mcp_aws", {})
    aws_access_key_id = aws_config.get("aws_access_key_id")
    aws_secret_access_key = aws_config.get("aws_secret_access_key")
    region_name = aws_config.get("region_name", "us-east-1")
    
    # Create MCP client manager
    manager = MCPClientManager()
    
    try:
        # Add AWS client with Messaging MCP Server
        logger.info("Adding AWS client with Messaging MCP Server...")
        await manager.add_aws_client(
            server_id="aws-messaging-mcp",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            use_external_mcp_servers=True,
            service_types=["sns", "sqs"]
        )
        
        # Get the AWS client
        aws_client = manager.get_client("aws-messaging-mcp")
        if not aws_client:
            logger.error("Failed to get AWS client")
            return
        
        # Test SNS if topic ARN is provided
        if topic_arn:
            logger.info("=== Testing SNS operations ===")
            
            # Publish a message to the topic
            message = {
                "source": "aws_external_mcp_test",
                "action": "test_notification",
                "timestamp": "2023-07-02T12:00:00Z"
            }
            
            logger.info(f"Publishing message to SNS topic: {topic_arn}")
            publish_result = await aws_client.publish_sns_message(
                topic_arn=topic_arn,
                message=json.dumps(message),
                subject="AWS External MCP Test Notification"
            )
            logger.info(f"Message published with ID: {publish_result.get('MessageId')}")
        else:
            logger.info("No SNS topic ARN provided, listing topics instead")
            topics_result = await aws_client.list_sns_topics()
            topics = topics_result.get('Topics', [])
            logger.info(f"Found {len(topics)} SNS topics")
        
        # Test SQS if queue URL is provided
        if queue_url:
            logger.info("=== Testing SQS operations ===")
            
            # Send a message to the queue
            message = {
                "source": "aws_external_mcp_test",
                "action": "test_message",
                "timestamp": "2023-07-02T12:00:00Z"
            }
            
            logger.info(f"Sending message to SQS queue: {queue_url}")
            send_result = await aws_client.send_sqs_message(
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
            messages = await aws_client.receive_sqs_messages(
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
                        delete_result = await aws_client.delete_sqs_message(
                            queue_url=queue_url,
                            receipt_handle=receipt_handle
                        )
                        if delete_result.get('success'):
                            logger.info("Message deleted successfully")
            else:
                logger.info("No messages received")
    
    except Exception as e:
        logger.error(f"Messaging operations failed: {e}")
    
    finally:
        # Clean up
        await manager.disconnect_all()
        logger.info("Messaging test completed")

async def test_mq_with_external_mcp(broker_id: str = None):
    """Test Amazon MQ operations using MQ MCP Server."""
    logger.info("=== Testing Amazon MQ with MQ MCP Server ===")
    
    # Get AWS configuration from settings
    aws_config = CONFIG.get("mcp_aws", {})
    aws_access_key_id = aws_config.get("aws_access_key_id")
    aws_secret_access_key = aws_config.get("aws_secret_access_key")
    region_name = aws_config.get("region_name", "us-east-1")
    
    # Create MCP client manager
    manager = MCPClientManager()
    
    try:
        # Add AWS client with MQ MCP Server
        logger.info("Adding AWS client with MQ MCP Server...")
        await manager.add_aws_client(
            server_id="aws-mq-mcp",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            use_external_mcp_servers=True,
            service_types=["mq"]
        )
        
        # Get the AWS client
        aws_client = manager.get_client("aws-mq-mcp")
        if not aws_client:
            logger.error("Failed to get AWS client")
            return
        
        # List MQ brokers if broker ID not provided
        if not broker_id:
            logger.info("Listing Amazon MQ brokers...")
            brokers = await aws_client.list_mq_brokers()
            logger.info(f"Found {len(brokers)} Amazon MQ brokers")
            
            # Use first broker if available
            if brokers:
                broker_id = brokers[0].get('BrokerId')
                logger.info(f"Using first available broker: {broker_id}")
        
        if broker_id:
            # Get broker details
            logger.info(f"Getting details for broker: {broker_id}")
            broker_details = await aws_client.get_mq_broker(broker_id)
            logger.info(f"Broker name: {broker_details.get('BrokerName')}")
            
            # Check if we have queue information available
            destinations = broker_details.get("Destinations", [])
            if destinations:
                queue_name = destinations[0].get("Name")
                
                # Send a test message
                logger.info(f"Sending test message to queue: {queue_name}")
                message = {
                    "source": "aws_external_mcp_test",
                    "action": "test_mq_message",
                    "timestamp": "2023-07-02T12:00:00Z"
                }
                
                await aws_client.send_mq_message(
                    broker_id=broker_id,
                    destination_type="queue",
                    destination_name=queue_name,
                    message_body=json.dumps(message)
                )
                logger.info("Message sent to Amazon MQ broker")
    
    except Exception as e:
        logger.error(f"MQ operations failed: {e}")
    
    finally:
        # Clean up
        await manager.disconnect_all()
        logger.info("MQ test completed")

async def test_all_external_mcp_services():
    """Test all external AWS MCP servers together."""
    logger.info("=== Testing All External AWS MCP Servers Together ===")
    
    # Get AWS configuration from settings
    aws_config = CONFIG.get("mcp_aws", {})
    aws_access_key_id = aws_config.get("aws_access_key_id")
    aws_secret_access_key = aws_config.get("aws_secret_access_key")
    region_name = aws_config.get("region_name", "us-east-1")
    
    # Create MCP client manager
    manager = MCPClientManager()
    
    try:
        # Add AWS client with all external MCP servers
        logger.info("Adding AWS client with all external MCP servers...")
        await manager.add_aws_client(
            server_id="aws-external-mcp",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            use_external_mcp_servers=True,
            service_types=["lambda", "sns", "sqs", "mq"]
        )
        
        # Get the AWS client
        aws_client = manager.get_client("aws-external-mcp")
        if not aws_client:
            logger.error("Failed to get AWS client")
            return
        
        # Get service availability
        logger.info("Checking external MCP server availability...")
        external_servers = getattr(aws_client, "external_servers", {})
        
        logger.info(f"Available external servers: {', '.join(external_servers.keys())}")
        
        # Test basic operations for each available service
        if "lambda" in external_servers:
            logger.info("Testing Lambda list operation...")
            functions = await aws_client.list_lambda_functions(limit=5)
            logger.info(f"Found {len(functions)} Lambda functions (limited to 5)")
        
        if "messaging" in external_servers:
            logger.info("Testing SNS list operation...")
            topics = await aws_client.list_sns_topics()
            logger.info(f"Found {len(topics.get('Topics', []))} SNS topics")
    
    except Exception as e:
        logger.error(f"External MCP operations failed: {e}")
    
    finally:
        # Clean up
        await manager.disconnect_all()
        logger.info("All external MCP tests completed")

async def run_tests():
    """Run all AWS external MCP server tests."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test AWS external MCP servers")
    parser.add_argument("--lambda", dest="lambda_function", help="Lambda function name for testing")
    parser.add_argument("--topic", help="SNS topic ARN for testing")
    parser.add_argument("--queue", help="SQS queue URL for testing")
    parser.add_argument("--broker", help="Amazon MQ broker ID for testing")
    parser.add_argument("--test", choices=["lambda", "messaging", "mq", "all"], 
                        default="all", help="Which services to test")
    args = parser.parse_args()
    
    # Run requested tests
    if args.test == "lambda" or args.test == "all":
        await test_lambda_with_external_mcp(args.lambda_function)
    
    if args.test == "messaging" or args.test == "all":
        await test_messaging_with_external_mcp(args.topic, args.queue)
    
    if args.test == "mq" or args.test == "all":
        await test_mq_with_external_mcp(args.broker)
    
    if args.test == "all":
        await test_all_external_mcp_services()

if __name__ == "__main__":
    asyncio.run(run_tests())
