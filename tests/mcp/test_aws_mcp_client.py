"""
Comprehensive test suite for AWS MCP Client.
Tests optimized AWS service operations via MCP with multiple fallback strategies.
"""
import pytest
import asyncio
import json
import os
import base64
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.mcp.aws_mcp_client import OptimizedAWSMCPClient, AWSClientError
from src.mcp.mcp_client_interface import MCPClientInterface


class TestOptimizedAWSMCPClient:
    """Test cases for OptimizedAWSMCPClient class."""

    @pytest.fixture
    def aws_client(self):
        """Create an AWS MCP client instance for testing."""
        return OptimizedAWSMCPClient(
            connection_uri="ws://localhost:8765/ws",
            aws_access_key_id="test_access_key",
            aws_secret_access_key="test_secret_key",
            region_name="us-west-2",
            use_direct_sdk=True,
            use_external_mcp_servers=True
        )

    @pytest.fixture
    def aws_client_sdk_only(self):
        """Create an AWS MCP client configured for direct SDK only."""
        return OptimizedAWSMCPClient(
            aws_access_key_id="test_access_key",
            aws_secret_access_key="test_secret_key",
            region_name="us-east-1",
            use_direct_sdk=True,
            use_external_mcp_servers=False
        )

    @pytest.fixture
    def mock_boto3_session(self):
        """Create a mock boto3 session for testing."""
        session = Mock()
        session.client.return_value = Mock()
        return session

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock websocket for testing."""
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        ws.receive_json = AsyncMock()
        ws.close = AsyncMock()
        return ws

    def test_aws_client_initialization(self, aws_client):
        """Test AWS MCP client initialization."""
        assert aws_client.connection_uri == "ws://localhost:8765/ws"
        assert aws_client.aws_access_key_id == "test_access_key"
        assert aws_client.aws_secret_access_key == "test_secret_key"
        assert aws_client.region_name == "us-west-2"
        assert aws_client.timeout == 30
        assert aws_client.max_retries == 3
        assert aws_client.use_direct_sdk is True
        assert aws_client.use_external_mcp_servers is True
        assert aws_client.connected is False
        assert isinstance(aws_client.clients, dict)
        assert isinstance(aws_client.external_servers, dict)

    def test_aws_client_implements_interface(self, aws_client):
        """Test that AWS client implements MCPClientInterface."""
        assert isinstance(aws_client, MCPClientInterface)

    @pytest.mark.asyncio
    async def test_connect_direct_sdk_success(self, aws_client_sdk_only):
        """Test successful connection using direct AWS SDK."""
        with patch('src.mcp.aws_mcp_client.AWS_SDK_AVAILABLE', True):
            with patch('boto3.Session') as MockSession:
                mock_session = Mock()
                MockSession.return_value = mock_session
                
                result = await aws_client_sdk_only.connect()
                
                assert result is True
                assert aws_client_sdk_only.connected is True
                MockSession.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_external_mcp_servers(self, aws_client):
        """Test connection with external MCP servers."""
        # Configure external servers
        aws_client.mcp_servers = {
            "lambda": {"package": "awslabs.lambda-tool-mcp-server", "port": 8766},
            "messaging": {"package": "aws.messaging-mcp-server", "port": 8767}
        }
        
        with patch.object(aws_client, '_ensure_external_mcp_packages'):
            with patch.object(aws_client, '_is_server_running', return_value=True):
                with patch.object(aws_client, '_connect_to_external_mcp'):
                    result = await aws_client.connect()
                    
                    assert result is True
                    assert aws_client.connected is True

    @pytest.mark.asyncio
    async def test_connect_websocket_fallback(self, aws_client):
        """Test WebSocket fallback when other methods are disabled."""
        aws_client.use_direct_sdk = False
        aws_client.use_external_mcp_servers = False
        
        with patch('aiohttp.ClientSession') as MockSession:
            mock_session = Mock()
            mock_ws = AsyncMock()
            mock_session.return_value.ws_connect.return_value = mock_ws
            MockSession.return_value = mock_session
            
            # Mock server info response
            with patch.object(aws_client, '_call_mcp_method', return_value={"session_id": "test_session"}):
                result = await aws_client.connect()
                
                assert result is True
                assert aws_client.connected is True
                assert aws_client.websocket == mock_ws

    @pytest.mark.asyncio
    async def test_connect_failure(self, aws_client):
        """Test connection failure scenarios."""
        aws_client.use_direct_sdk = False
        aws_client.use_external_mcp_servers = False
        
        with patch('aiohttp.ClientSession') as MockSession:
            MockSession.side_effect = Exception("Connection failed")
            
            result = await aws_client.connect()
            
            assert result is False
            assert aws_client.connected is False

    @pytest.mark.asyncio
    async def test_disconnect(self, aws_client):
        """Test disconnection from AWS MCP services."""
        # Set up connected state
        aws_client.connected = True
        aws_client.websocket = AsyncMock()
        mock_external_server = AsyncMock()
        aws_client.external_servers["lambda"] = mock_external_server
        
        await aws_client.disconnect()
        
        assert aws_client.connected is False
        assert aws_client.websocket is None
        aws_client.websocket.close.assert_called_once()
        mock_external_server.disconnect.assert_called_once()


class TestAWSClientLambdaOperations:
    """Test AWS Lambda operations via MCP client."""

    @pytest.fixture
    def connected_aws_client(self):
        """Create a connected AWS MCP client for testing."""
        client = OptimizedAWSMCPClient()
        client.connected = True
        client.use_direct_sdk = True
        client.session = Mock()
        client.clients["lambda"] = Mock()
        return client

    @pytest.mark.asyncio
    async def test_list_lambda_functions(self, connected_aws_client):
        """Test listing Lambda functions."""
        mock_lambda_client = connected_aws_client.clients["lambda"]
        mock_lambda_client.list_functions.return_value = {
            "Functions": [
                {
                    "FunctionName": "test-function-1",
                    "Runtime": "python3.9",
                    "Handler": "lambda_function.lambda_handler",
                    "CodeSize": 1024,
                    "LastModified": "2024-01-01T00:00:00.000+0000"
                },
                {
                    "FunctionName": "test-function-2",
                    "Runtime": "nodejs18.x",
                    "Handler": "index.handler",
                    "CodeSize": 2048,
                    "LastModified": "2024-01-02T00:00:00.000+0000"
                }
            ]
        }
        
        result = await connected_aws_client.list_lambda_functions()
        
        assert len(result) == 2
        assert result[0]["FunctionName"] == "test-function-1"
        assert result[1]["Runtime"] == "nodejs18.x"
        mock_lambda_client.list_functions.assert_called_once()

    @pytest.mark.asyncio
    async def test_invoke_lambda_function(self, connected_aws_client):
        """Test invoking a Lambda function."""
        mock_lambda_client = connected_aws_client.clients["lambda"]
        mock_response = {
            "StatusCode": 200,
            "LogResult": base64.b64encode(b"Log output").decode(),
            "Payload": json.dumps({"result": "success", "data": "test output"}).encode()
        }
        mock_lambda_client.invoke.return_value = mock_response
        
        payload = {"input": "test data"}
        result = await connected_aws_client.invoke_lambda_function("test-function", payload)
        
        assert result["StatusCode"] == 200
        assert "LogResult" in result
        mock_lambda_client.invoke.assert_called_once_with(
            FunctionName="test-function",
            Payload=json.dumps(payload)
        )

    @pytest.mark.asyncio
    async def test_get_lambda_function_info(self, connected_aws_client):
        """Test getting Lambda function information."""
        mock_lambda_client = connected_aws_client.clients["lambda"]
        mock_lambda_client.get_function.return_value = {
            "Configuration": {
                "FunctionName": "test-function",
                "Runtime": "python3.9",
                "Handler": "lambda_function.lambda_handler",
                "Description": "Test Lambda function",
                "Timeout": 30,
                "MemorySize": 128,
                "Environment": {"Variables": {"ENV": "test"}}
            },
            "Code": {
                "Location": "https://example.com/code.zip"
            }
        }
        
        result = await connected_aws_client.get_lambda_function_info("test-function")
        
        assert result["Configuration"]["FunctionName"] == "test-function"
        assert result["Configuration"]["Runtime"] == "python3.9"
        assert result["Configuration"]["Timeout"] == 30

    @pytest.mark.asyncio
    async def test_create_lambda_function(self, connected_aws_client):
        """Test creating a Lambda function."""
        mock_lambda_client = connected_aws_client.clients["lambda"]
        mock_lambda_client.create_function.return_value = {
            "FunctionName": "new-test-function",
            "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:new-test-function",
            "Runtime": "python3.9",
            "Handler": "lambda_function.lambda_handler",
            "State": "Active"
        }
        
        function_config = {
            "FunctionName": "new-test-function",
            "Runtime": "python3.9",
            "Role": "arn:aws:iam::123456789012:role/lambda-execution-role",
            "Handler": "lambda_function.lambda_handler",
            "Code": {"ZipFile": b"dummy code"},
            "Description": "New test function"
        }
        
        result = await connected_aws_client.create_lambda_function(function_config)
        
        assert result["FunctionName"] == "new-test-function"
        assert result["State"] == "Active"
        mock_lambda_client.create_function.assert_called_once_with(**function_config)


class TestAWSClientSNSOperations:
    """Test AWS SNS operations via MCP client."""

    @pytest.fixture
    def connected_aws_client(self):
        """Create a connected AWS MCP client for testing."""
        client = OptimizedAWSMCPClient()
        client.connected = True
        client.use_direct_sdk = True
        client.session = Mock()
        client.clients["sns"] = Mock()
        return client

    @pytest.mark.asyncio
    async def test_list_sns_topics(self, connected_aws_client):
        """Test listing SNS topics."""
        mock_sns_client = connected_aws_client.clients["sns"]
        mock_sns_client.list_topics.return_value = {
            "Topics": [
                {"TopicArn": "arn:aws:sns:us-east-1:123456789012:customer-notifications"},
                {"TopicArn": "arn:aws:sns:us-east-1:123456789012:system-alerts"}
            ]
        }
        
        result = await connected_aws_client.list_sns_topics()
        
        assert len(result) == 2
        assert "customer-notifications" in result[0]["TopicArn"]
        assert "system-alerts" in result[1]["TopicArn"]

    @pytest.mark.asyncio
    async def test_publish_sns_message(self, connected_aws_client):
        """Test publishing message to SNS topic."""
        mock_sns_client = connected_aws_client.clients["sns"]
        mock_sns_client.publish.return_value = {
            "MessageId": "12345678-1234-1234-1234-123456789012"
        }
        
        topic_arn = "arn:aws:sns:us-east-1:123456789012:customer-notifications"
        message = "Customer support ticket created"
        subject = "New Support Ticket"
        
        result = await connected_aws_client.publish_sns_message(topic_arn, message, subject)
        
        assert result["MessageId"] == "12345678-1234-1234-1234-123456789012"
        mock_sns_client.publish.assert_called_once_with(
            TopicArn=topic_arn,
            Message=message,
            Subject=subject
        )

    @pytest.mark.asyncio
    async def test_create_sns_topic(self, connected_aws_client):
        """Test creating SNS topic."""
        mock_sns_client = connected_aws_client.clients["sns"]
        mock_sns_client.create_topic.return_value = {
            "TopicArn": "arn:aws:sns:us-east-1:123456789012:new-topic"
        }
        
        result = await connected_aws_client.create_sns_topic("new-topic")
        
        assert "new-topic" in result["TopicArn"]
        mock_sns_client.create_topic.assert_called_once_with(Name="new-topic")


class TestAWSClientSQSOperations:
    """Test AWS SQS operations via MCP client."""

    @pytest.fixture
    def connected_aws_client(self):
        """Create a connected AWS MCP client for testing."""
        client = OptimizedAWSMCPClient()
        client.connected = True
        client.use_direct_sdk = True
        client.session = Mock()
        client.clients["sqs"] = Mock()
        return client

    @pytest.mark.asyncio
    async def test_list_sqs_queues(self, connected_aws_client):
        """Test listing SQS queues."""
        mock_sqs_client = connected_aws_client.clients["sqs"]
        mock_sqs_client.list_queues.return_value = {
            "QueueUrls": [
                "https://sqs.us-east-1.amazonaws.com/123456789012/customer-support-queue",
                "https://sqs.us-east-1.amazonaws.com/123456789012/notification-queue"
            ]
        }
        
        result = await connected_aws_client.list_sqs_queues()
        
        assert len(result) == 2
        assert "customer-support-queue" in result[0]
        assert "notification-queue" in result[1]

    @pytest.mark.asyncio
    async def test_send_sqs_message(self, connected_aws_client):
        """Test sending message to SQS queue."""
        mock_sqs_client = connected_aws_client.clients["sqs"]
        mock_sqs_client.send_message.return_value = {
            "MessageId": "12345678-1234-1234-1234-123456789012",
            "MD5OfBody": "d41d8cd98f00b204e9800998ecf8427e"
        }
        
        queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/customer-support-queue"
        message_body = json.dumps({"ticket_id": "456", "priority": "high"})
        
        result = await connected_aws_client.send_sqs_message(queue_url, message_body)
        
        assert result["MessageId"] == "12345678-1234-1234-1234-123456789012"
        mock_sqs_client.send_message.assert_called_once_with(
            QueueUrl=queue_url,
            MessageBody=message_body
        )

    @pytest.mark.asyncio
    async def test_receive_sqs_messages(self, connected_aws_client):
        """Test receiving messages from SQS queue."""
        mock_sqs_client = connected_aws_client.clients["sqs"]
        mock_sqs_client.receive_message.return_value = {
            "Messages": [
                {
                    "MessageId": "msg-1",
                    "Body": json.dumps({"ticket_id": "456", "priority": "high"}),
                    "ReceiptHandle": "receipt-handle-1"
                },
                {
                    "MessageId": "msg-2",
                    "Body": json.dumps({"ticket_id": "457", "priority": "medium"}),
                    "ReceiptHandle": "receipt-handle-2"
                }
            ]
        }
        
        queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/customer-support-queue"
        result = await connected_aws_client.receive_sqs_messages(queue_url, max_messages=10)
        
        assert len(result["Messages"]) == 2
        assert result["Messages"][0]["MessageId"] == "msg-1"
        mock_sqs_client.receive_message.assert_called_once_with(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10
        )


class TestAWSClientCustomerSupportIntegration:
    """Test customer support specific functionality integration."""

    @pytest.fixture
    def connected_aws_client(self):
        """Create a connected AWS MCP client for testing."""
        client = OptimizedAWSMCPClient()
        client.connected = True
        client.use_direct_sdk = True
        client.session = Mock()
        # Mock clients for different services
        client.clients = {
            "lambda": Mock(),
            "sns": Mock(),
            "sqs": Mock(),
            "dynamodb": Mock()
        }
        return client

    @pytest.mark.asyncio
    async def test_get_customers_via_lambda(self, connected_aws_client):
        """Test getting customers via Lambda function."""
        mock_lambda_client = connected_aws_client.clients["lambda"]
        mock_response = {
            "StatusCode": 200,
            "Payload": json.dumps([
                {"id": "1", "name": "Customer 1", "email": "customer1@example.com"},
                {"id": "2", "name": "Customer 2", "email": "customer2@example.com"}
            ]).encode()
        }
        mock_lambda_client.invoke.return_value = mock_response
        
        result = await connected_aws_client.get_customers(limit=100)
        
        assert len(result) == 2
        assert result[0]["name"] == "Customer 1"
        mock_lambda_client.invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_customer_by_id_lambda(self, connected_aws_client):
        """Test getting customer by ID via Lambda function."""
        mock_lambda_client = connected_aws_client.clients["lambda"]
        customer_data = {"id": "123", "name": "Test Customer", "email": "test@example.com"}
        mock_response = {
            "StatusCode": 200,
            "Payload": json.dumps(customer_data).encode()
        }
        mock_lambda_client.invoke.return_value = mock_response
        
        result = await connected_aws_client.get_customer_by_id("123")
        
        assert result["id"] == "123"
        assert result["name"] == "Test Customer"

    @pytest.mark.asyncio
    async def test_create_customer_lambda(self, connected_aws_client):
        """Test creating customer via Lambda function."""
        mock_lambda_client = connected_aws_client.clients["lambda"]
        customer_data = {"name": "New Customer", "email": "new@example.com"}
        created_customer = {"id": "new_123", **customer_data}
        mock_response = {
            "StatusCode": 200,
            "Payload": json.dumps(created_customer).encode()
        }
        mock_lambda_client.invoke.return_value = mock_response
        
        result = await connected_aws_client.create_customer(customer_data)
        
        assert result["id"] == "new_123"
        assert result["name"] == "New Customer"

    @pytest.mark.asyncio
    async def test_get_tickets_lambda(self, connected_aws_client):
        """Test getting tickets via Lambda function."""
        mock_lambda_client = connected_aws_client.clients["lambda"]
        tickets_data = [
            {"id": "1", "title": "Ticket 1", "status": "open", "priority": "high"},
            {"id": "2", "title": "Ticket 2", "status": "closed", "priority": "medium"}
        ]
        mock_response = {
            "StatusCode": 200,
            "Payload": json.dumps(tickets_data).encode()
        }
        mock_lambda_client.invoke.return_value = mock_response
        
        result = await connected_aws_client.get_tickets(limit=100, status="open")
        
        assert len(result) == 2
        assert result[0]["title"] == "Ticket 1"

    @pytest.mark.asyncio
    async def test_search_knowledge_base_lambda(self, connected_aws_client):
        """Test searching knowledge base via Lambda function."""
        mock_lambda_client = connected_aws_client.clients["lambda"]
        search_results = [
            {
                "id": "1",
                "title": "How to reset password",
                "content": "Step 1: Click forgot password...",
                "relevance_score": 0.95
            },
            {
                "id": "2",
                "title": "Password requirements",
                "content": "Passwords must be at least 8 characters...",
                "relevance_score": 0.87
            }
        ]
        mock_response = {
            "StatusCode": 200,
            "Payload": json.dumps(search_results).encode()
        }
        mock_lambda_client.invoke.return_value = mock_response
        
        result = await connected_aws_client.search_knowledge_base("password reset", limit=10)
        
        assert len(result) == 2
        assert "password" in result[0]["title"].lower()

    @pytest.mark.asyncio
    async def test_get_analytics_lambda(self, connected_aws_client):
        """Test getting analytics via Lambda function."""
        mock_lambda_client = connected_aws_client.clients["lambda"]
        analytics_data = {
            "period_days": 30,
            "total_tickets": 150,
            "resolved_tickets": 120,
            "open_tickets": 25,
            "average_resolution_time": "4.5 hours",
            "customer_satisfaction": 4.2
        }
        mock_response = {
            "StatusCode": 200,
            "Payload": json.dumps(analytics_data).encode()
        }
        mock_lambda_client.invoke.return_value = mock_response
        
        result = await connected_aws_client.get_analytics(days=30)
        
        assert result["period_days"] == 30
        assert result["total_tickets"] == 150
        assert result["customer_satisfaction"] == 4.2


class TestAWSClientErrorHandling:
    """Test error handling in AWS MCP client."""

    @pytest.fixture
    def connected_aws_client(self):
        """Create a connected AWS MCP client for testing."""
        client = OptimizedAWSMCPClient()
        client.connected = True
        client.use_direct_sdk = True
        client.session = Mock()
        client.clients["lambda"] = Mock()
        return client

    @pytest.mark.asyncio
    async def test_aws_service_error_handling(self, connected_aws_client):
        """Test handling of AWS service errors."""
        from botocore.exceptions import ClientError
        
        mock_lambda_client = connected_aws_client.clients["lambda"]
        error = ClientError(
            error_response={
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "Function not found: test-function"
                }
            },
            operation_name="GetFunction"
        )
        mock_lambda_client.get_function.side_effect = error
        
        with pytest.raises(AWSClientError, match="Function not found"):
            await connected_aws_client.get_lambda_function_info("test-function")

    @pytest.mark.asyncio
    async def test_permission_denied_error(self, connected_aws_client):
        """Test handling of permission denied errors."""
        from botocore.exceptions import ClientError
        
        mock_lambda_client = connected_aws_client.clients["lambda"]
        error = ClientError(
            error_response={
                "Error": {
                    "Code": "AccessDeniedException",
                    "Message": "User is not authorized to perform action"
                }
            },
            operation_name="ListFunctions"
        )
        mock_lambda_client.list_functions.side_effect = error
        
        with pytest.raises(AWSClientError, match="not authorized"):
            await connected_aws_client.list_lambda_functions()

    @pytest.mark.asyncio
    async def test_rate_limiting_retry(self, connected_aws_client):
        """Test retry logic for rate limiting errors."""
        from botocore.exceptions import ClientError
        
        mock_lambda_client = connected_aws_client.clients["lambda"]
        
        # First two calls fail with throttling, third succeeds
        throttle_error = ClientError(
            error_response={
                "Error": {
                    "Code": "TooManyRequestsException",
                    "Message": "Rate exceeded"
                }
            },
            operation_name="ListFunctions"
        )
        
        success_response = {"Functions": []}
        mock_lambda_client.list_functions.side_effect = [
            throttle_error,
            throttle_error,
            success_response
        ]
        
        with patch('asyncio.sleep'):  # Mock sleep to speed up test
            result = await connected_aws_client.list_lambda_functions()
            
            assert result == []
            assert mock_lambda_client.list_functions.call_count == 3

    @pytest.mark.asyncio
    async def test_connection_timeout(self, connected_aws_client):
        """Test handling of connection timeouts."""
        import socket
        
        mock_lambda_client = connected_aws_client.clients["lambda"]
        mock_lambda_client.list_functions.side_effect = socket.timeout("Connection timed out")
        
        with pytest.raises(AWSClientError, match="timed out"):
            await connected_aws_client.list_lambda_functions()

    @pytest.mark.asyncio
    async def test_invalid_credentials_error(self, connected_aws_client):
        """Test handling of invalid credentials."""
        from botocore.exceptions import ClientError
        
        mock_lambda_client = connected_aws_client.clients["lambda"]
        error = ClientError(
            error_response={
                "Error": {
                    "Code": "InvalidUserID.NotFound",
                    "Message": "The AWS Access Key Id you provided does not exist"
                }
            },
            operation_name="ListFunctions"
        )
        mock_lambda_client.list_functions.side_effect = error
        
        with pytest.raises(AWSClientError, match="Access Key"):
            await connected_aws_client.list_lambda_functions()


class TestAWSClientConfiguration:
    """Test various configuration scenarios for AWS MCP client."""

    def test_default_configuration(self):
        """Test default configuration values."""
        client = OptimizedAWSMCPClient()
        
        assert client.connection_uri == "ws://localhost:8765/ws"
        assert client.region_name == "us-east-1"
        assert client.timeout == 30
        assert client.max_retries == 3
        assert client.use_direct_sdk is False  # False when AWS SDK not available
        assert client.use_external_mcp_servers is True

    def test_custom_configuration(self):
        """Test custom configuration values."""
        client = OptimizedAWSMCPClient(
            connection_uri="ws://custom.aws.example.com:9000/ws",
            aws_access_key_id="custom_key",
            aws_secret_access_key="custom_secret",
            region_name="eu-west-1",
            timeout=60,
            max_retries=5,
            use_direct_sdk=False,
            use_external_mcp_servers=False
        )
        
        assert "custom.aws.example.com" in client.connection_uri
        assert client.aws_access_key_id == "custom_key"
        assert client.region_name == "eu-west-1"
        assert client.timeout == 60
        assert client.max_retries == 5
        assert client.use_direct_sdk is False
        assert client.use_external_mcp_servers is False

    def test_external_mcp_servers_configuration(self):
        """Test external MCP servers configuration."""
        mcp_servers = {
            "lambda": {"package": "awslabs.lambda-tool-mcp-server", "port": 8766},
            "messaging": {"package": "aws.messaging-mcp-server", "port": 8767},
            "mq": {"package": "amazon.mq-mcp-server", "port": 8768}
        }
        
        client = OptimizedAWSMCPClient(
            use_external_mcp_servers=True,
            mcp_servers=mcp_servers
        )
        
        assert client.mcp_servers == mcp_servers
        assert "lambda" in client.mcp_servers
        assert client.mcp_servers["lambda"]["port"] == 8766

    def test_aws_credentials_from_environment(self):
        """Test AWS credentials from environment variables."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'env_access_key',
            'AWS_SECRET_ACCESS_KEY': 'env_secret_key',
            'AWS_DEFAULT_REGION': 'us-west-1'
        }):
            client = OptimizedAWSMCPClient()
            
            # Client should use environment variables when not explicitly provided
            assert client.aws_access_key_id is None  # Not set in constructor
            assert client.region_name == "us-east-1"  # Default from constructor


class TestAWSClientPerformance:
    """Test performance characteristics of AWS MCP client."""

    @pytest.fixture
    def connected_aws_client(self):
        """Create a connected AWS MCP client for testing."""
        client = OptimizedAWSMCPClient()
        client.connected = True
        client.use_direct_sdk = True
        client.session = Mock()
        client.clients["lambda"] = Mock()
        return client

    @pytest.mark.asyncio
    async def test_concurrent_lambda_invocations(self, connected_aws_client):
        """Test concurrent Lambda function invocations."""
        mock_lambda_client = connected_aws_client.clients["lambda"]
        mock_response = {
            "StatusCode": 200,
            "Payload": json.dumps({"result": "success"}).encode()
        }
        mock_lambda_client.invoke.return_value = mock_response
        
        # Make multiple concurrent invocations
        tasks = [
            connected_aws_client.invoke_lambda_function(f"function-{i}", {"input": f"data-{i}"})
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(result["StatusCode"] == 200 for result in results)
        assert mock_lambda_client.invoke.call_count == 5

    @pytest.mark.asyncio
    async def test_connection_pooling(self, connected_aws_client):
        """Test that AWS clients are reused efficiently."""
        # First call should create the client
        await connected_aws_client.list_lambda_functions()
        first_client = connected_aws_client.clients.get("lambda")
        
        # Second call should reuse the same client
        await connected_aws_client.list_lambda_functions()
        second_client = connected_aws_client.clients.get("lambda")
        
        assert first_client is second_client

    @pytest.mark.asyncio
    async def test_batch_operations(self, connected_aws_client):
        """Test batch operations for better performance."""
        mock_sqs_client = Mock()
        connected_aws_client.clients["sqs"] = mock_sqs_client
        
        # Mock batch send response
        mock_sqs_client.send_message_batch.return_value = {
            "Successful": [
                {"Id": "msg1", "MessageId": "id1"},
                {"Id": "msg2", "MessageId": "id2"}
            ],
            "Failed": []
        }
        
        messages = [
            {"Id": "msg1", "MessageBody": "Message 1"},
            {"Id": "msg2", "MessageBody": "Message 2"}
        ]
        
        result = await connected_aws_client.send_sqs_messages_batch("queue-url", messages)
        
        assert len(result["Successful"]) == 2
        assert len(result["Failed"]) == 0
        mock_sqs_client.send_message_batch.assert_called_once()


class TestAWSClientMCPIntegration:
    """Test integration with external MCP servers."""

    @pytest.fixture
    def aws_client_with_mcp(self):
        """Create AWS client configured for external MCP servers."""
        return OptimizedAWSMCPClient(
            use_external_mcp_servers=True,
            mcp_servers={
                "lambda": {"package": "awslabs.lambda-tool-mcp-server", "port": 8766}
            }
        )

    @pytest.mark.asyncio
    async def test_external_mcp_server_communication(self, aws_client_with_mcp):
        """Test communication with external MCP servers."""
        mock_external_server = AsyncMock()
        mock_external_server.list_functions.return_value = [
            {"FunctionName": "external-function", "Runtime": "python3.9"}
        ]
        aws_client_with_mcp.external_servers["lambda"] = mock_external_server
        aws_client_with_mcp.connected = True
        
        result = await aws_client_with_mcp.list_lambda_functions()
        
        assert len(result) == 1
        assert result[0]["FunctionName"] == "external-function"
        mock_external_server.list_functions.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_to_direct_sdk(self, aws_client_with_mcp):
        """Test fallback to direct SDK when external MCP servers fail."""
        # External server fails
        mock_external_server = AsyncMock()
        mock_external_server.list_functions.side_effect = Exception("MCP server error")
        aws_client_with_mcp.external_servers["lambda"] = mock_external_server
        
        # Direct SDK should be used as fallback
        with patch('boto3.Session') as MockSession:
            mock_session = Mock()
            mock_lambda_client = Mock()
            mock_lambda_client.list_functions.return_value = {"Functions": []}
            mock_session.client.return_value = mock_lambda_client
            MockSession.return_value = mock_session
            
            aws_client_with_mcp.use_direct_sdk = True
            aws_client_with_mcp.session = mock_session
            aws_client_with_mcp.clients["lambda"] = mock_lambda_client
            aws_client_with_mcp.connected = True
            
            result = await aws_client_with_mcp.list_lambda_functions()
            
            assert result == []
            mock_lambda_client.list_functions.assert_called_once()

    @pytest.mark.asyncio
    async def test_mcp_server_installation(self, aws_client_with_mcp):
        """Test automatic installation of MCP server packages."""
        with patch.object(aws_client_with_mcp, '_install_mcp_package') as mock_install:
            with patch.object(aws_client_with_mcp, '_is_package_installed', return_value=False):
                await aws_client_with_mcp._ensure_external_mcp_packages()
                
                mock_install.assert_called_once_with("awslabs.lambda-tool-mcp-server")
