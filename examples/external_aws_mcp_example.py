"""
Example script demonstrating how to use official external AWS MCP servers.
This provides a simplified example that can be copied and modified for your specific needs.
"""
import asyncio
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aws_mcp_example")

async def example_lambda_with_external_mcp():
    """Example of using AWS Lambda Tool MCP Server."""
    # Import the OptimizedAWSMCPClient directly for this example
    from src.mcp.aws_mcp_client import OptimizedAWSMCPClient
    
    # Create the client with external MCP server configuration
    client = OptimizedAWSMCPClient(
        # Use your AWS credentials or configure env vars
        # aws_access_key_id="YOUR_ACCESS_KEY",
        # aws_secret_access_key="YOUR_SECRET_KEY",
        region_name="us-east-1",
        use_external_mcp_servers=True,
        # Configure only Lambda MCP server
        mcp_servers={
            "lambda": {
                "package": "awslabs.lambda-tool-mcp-server",
                "port": 8766
            }
        }
    )
    
    # Connect to the client
    connected = await client.connect()
    if not connected:
        logger.error("Failed to connect to AWS MCP client")
        return
    
    # Initialize Lambda service
    initialized = await client.init_lambda_service()
    if not initialized:
        logger.error("Failed to initialize Lambda service")
        return
    
    # Example Lambda function name
    function_name = "example-function"  # Replace with your function name
    
    # Example payload
    payload = {
        "message": "Hello from AWS Lambda Tool MCP Server",
        "timestamp": "2025-07-02T12:00:00Z"
    }
    
    try:
        # Invoke Lambda function
        logger.info(f"Invoking Lambda function: {function_name}")
        response = await client.invoke_lambda(
            function_name=function_name,
            payload=payload
        )
        
        logger.info(f"Lambda response: {json.dumps(response, indent=2)}")
    except Exception as e:
        logger.error(f"Error invoking Lambda: {str(e)}")
    
    # Disconnect when done
    await client.disconnect()

async def example_messaging_with_external_mcp():
    """Example of using AWS Messaging MCP Server (SNS/SQS)."""
    # Import the OptimizedAWSMCPClient directly for this example
    from src.mcp.aws_mcp_client import OptimizedAWSMCPClient
    
    # Create the client with external MCP server configuration
    client = OptimizedAWSMCPClient(
        # Use your AWS credentials or configure env vars
        # aws_access_key_id="YOUR_ACCESS_KEY",
        # aws_secret_access_key="YOUR_SECRET_KEY",
        region_name="us-east-1",
        use_external_mcp_servers=True,
        # Configure only Messaging MCP server
        mcp_servers={
            "messaging": {
                "package": "aws.messaging-mcp-server",
                "port": 8767
            }
        }
    )
    
    # Connect to the client
    connected = await client.connect()
    if not connected:
        logger.error("Failed to connect to AWS MCP client")
        return
    
    # Initialize SNS and SQS services
    sns_initialized = await client.init_sns_service()
    sqs_initialized = await client.init_sqs_service()
    
    # Example SNS topic and SQS queue
    topic_arn = "arn:aws:sns:us-east-1:123456789012:example-topic"  # Replace with your topic ARN
    queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/example-queue"  # Replace with your queue URL
    
    try:
        # Publish SNS message
        if sns_initialized:
            logger.info(f"Publishing message to SNS topic: {topic_arn}")
            sns_response = await client.publish_sns_message(
                topic_arn=topic_arn,
                message=json.dumps({
                    "message": "Hello from AWS Messaging MCP Server",
                    "timestamp": "2025-07-02T12:00:00Z"
                }),
                subject="Test Message"
            )
            logger.info(f"SNS publish response: {json.dumps(sns_response, indent=2)}")
        
        # Send and receive SQS messages
        if sqs_initialized:
            # Send message
            logger.info(f"Sending message to SQS queue: {queue_url}")
            send_response = await client.send_sqs_message(
                queue_url=queue_url,
                message_body=json.dumps({
                    "message": "Hello from AWS Messaging MCP Server",
                    "timestamp": "2025-07-02T12:00:00Z"
                })
            )
            logger.info(f"SQS send response: {json.dumps(send_response, indent=2)}")
            
            # Receive messages
            logger.info(f"Receiving messages from SQS queue: {queue_url}")
            receive_response = await client.receive_sqs_messages(
                queue_url=queue_url,
                max_messages=5,
                wait_time_seconds=5
            )
            logger.info(f"Received {len(receive_response)} messages")
            
            # Process and delete messages
            for message in receive_response:
                logger.info(f"Message body: {message.get('Body')}")
                
                # Delete the message
                receipt_handle = message.get('ReceiptHandle')
                if receipt_handle:
                    delete_response = await client.delete_sqs_message(
                        queue_url=queue_url,
                        receipt_handle=receipt_handle
                    )
                    logger.info("Message deleted")
    
    except Exception as e:
        logger.error(f"Error in messaging operations: {str(e)}")
    
    # Disconnect when done
    await client.disconnect()

async def example_all_external_mcp():
    """Example of using all external AWS MCP servers together."""
    # Import the MCPClientManager for a more realistic example
    from src.mcp.mcp_client_manager import MCPClientManager
    
    # Create the client manager
    manager = MCPClientManager()
    
    try:
        # Add AWS client with all external MCP servers
        success = await manager.add_aws_client(
            server_id="aws-external",
            # Use your AWS credentials or configure env vars
            # aws_access_key_id="YOUR_ACCESS_KEY",
            # aws_secret_access_key="YOUR_SECRET_KEY",
            region_name="us-east-1",
            use_external_mcp_servers=True,
            service_types=["lambda", "sns", "sqs", "mq"]
        )
        
        if not success:
            logger.error("Failed to add AWS client")
            return
        
        # Get the client from the manager
        client = manager.get_client("aws-external")
        
        # Use the client for various operations
        # ... (your code to use the client) ...
        logger.info("Successfully initialized all external AWS MCP servers")
        
        # List Lambda functions as an example
        functions = await client.list_lambda_functions(limit=5)
        logger.info(f"Found {len(functions)} Lambda functions")
        
        # List SNS topics as an example
        topics = await client.list_sns_topics()
        logger.info(f"Found {len(topics.get('Topics', []))} SNS topics")
        
    except Exception as e:
        logger.error(f"Error in AWS MCP operations: {str(e)}")
    
    finally:
        # Clean up
        await manager.disconnect_all()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AWS External MCP Examples")
    parser.add_argument("--example", choices=["lambda", "messaging", "all"], 
                      default="all", help="Which example to run")
    args = parser.parse_args()
    
    if args.example == "lambda":
        asyncio.run(example_lambda_with_external_mcp())
    elif args.example == "messaging":
        asyncio.run(example_messaging_with_external_mcp())
    else:
        asyncio.run(example_all_external_mcp())
