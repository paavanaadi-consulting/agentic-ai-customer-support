"""
AWS MCP Client
Provides optimized AWS service operations via MCP with support for multiple AWS services.
Enables access to Lambda, SNS, SQS, S3, MQ, and other AWS services with consistent error handling
and performance optimization strategies. Uses official AWS MCP servers when available.
"""
import asyncio
import json
import time
import logging
import os
import sys
import subprocess
import importlib
import pkg_resources
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
import base64
import aiohttp

from .mcp_client_interface import MCPClientInterface

# Try to import AWS SDK packages
try:
    import boto3
    import botocore
    from boto3.session import Session
    from botocore.exceptions import ClientError, BotoCoreError
    AWS_SDK_AVAILABLE = True
except ImportError:
    AWS_SDK_AVAILABLE = False
    # Create placeholder types for type hints
    class Session:
        pass
    class ClientError(Exception):
        pass
    class BotoCoreError(Exception):
        pass

# Try to import official AWS Lambda Tool MCP Server package
try:
    from awslabs.lambda_tool_mcp_client import LambdaToolMCPClient
    LAMBDA_TOOL_MCP_AVAILABLE = True
except ImportError:
    LAMBDA_TOOL_MCP_AVAILABLE = False
    
# Try to import official AWS Messaging (SNS/SQS) MCP Server package
try:
    from aws.messaging_mcp_client import MessagingMCPClient
    MESSAGING_MCP_AVAILABLE = True
except ImportError:
    MESSAGING_MCP_AVAILABLE = False

# Try to import official Amazon MQ MCP Server package  
try:
    from amazon.mq_mcp_client import MQMCPClient
    MQ_MCP_AVAILABLE = True
except ImportError:
    MQ_MCP_AVAILABLE = False

logger = logging.getLogger(__name__)


class AWSClientError(Exception):
    """Custom exception for AWS MCP client errors."""
    pass


class OptimizedAWSMCPClient(MCPClientInterface):
    """
    Optimized AWS MCP Client that provides:
    1. Connection to official AWS MCP servers when available
    2. Direct connection to AWS services (preferred fallback)
    3. HTTP-based MCP communication (secondary fallback)
    4. Advanced error handling and retry mechanisms
    5. Support for Lambda, SNS, SQS, MQ, S3, and other AWS services
    """
    
    def __init__(self, 
                 connection_uri: str = "ws://localhost:8765/ws",
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None,
                 region_name: str = "us-east-1",
                 timeout: int = 30,
                 max_retries: int = 3,
                 use_direct_sdk: bool = True,
                 use_external_mcp_servers: bool = True,
                 mcp_servers: Dict[str, Dict[str, Any]] = None):
        """
        Initialize AWS MCP Client.
        
        Args:
            connection_uri: WebSocket URI for MCP server
            aws_access_key_id: AWS access key ID (optional if using IAM roles)
            aws_secret_access_key: AWS secret access key (optional if using IAM roles)
            region_name: AWS region name
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            use_direct_sdk: Whether to use AWS SDK directly when available
            use_external_mcp_servers: Whether to use official AWS MCP servers when available
            mcp_servers: Configuration for external MCP servers
        """
        self.connection_uri = connection_uri
        self.region_name = region_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_direct_sdk = use_direct_sdk and AWS_SDK_AVAILABLE
        self.use_external_mcp_servers = use_external_mcp_servers
        self.mcp_servers = mcp_servers or {}
        
        # Connection state
        self.connected = False
        self.websocket = None
        self.session_id = None
        
        # AWS session and clients
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.session = None
        self.clients = {}
        
        # External MCP servers
        self.external_servers = {}
        self.external_mcp_processes = {}
        
        # Specialized clients
        self.lambda_client = None
        self.sns_client = None
        self.sqs_client = None
        self.mq_client = None
        
        # Request tracking
        self.pending_requests = {}
        self.request_counter = 0
        
    async def connect(self) -> bool:
        """
        Connect to the AWS MCP server and initialize AWS clients.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            # Step 1: Initialize AWS session if using direct SDK
            if self.use_direct_sdk:
                self._init_aws_session()
            
            # Step 2: Initialize official AWS MCP servers if configured
            if self.use_external_mcp_servers:
                await self._init_external_mcp_servers()
            
            # Step 3: Connect to MCP server (WebSocket connection) as fallback
            if not self.use_direct_sdk and not self.use_external_mcp_servers:
                # Connect to the WebSocket for MCP communication
                self.websocket = await asyncio.wait_for(
                    aiohttp.ClientSession().ws_connect(self.connection_uri),
                    timeout=self.timeout
                )
                
                # Get server info and capabilities
                server_info = await self._call_mcp_method("get_server_info")
                if not server_info or not isinstance(server_info, dict):
                    logger.error("Failed to get server info")
                    return False
                
                self.session_id = server_info.get("session_id")
            
            self.connected = True
            if self.use_external_mcp_servers:
                logger.info(f"Connected to official AWS MCP services: {', '.join(self.external_servers.keys())}")
            else:
                logger.info(f"Connected to AWS MCP service (direct SDK: {self.use_direct_sdk})")
            return True
            
        except (aiohttp.ClientError, asyncio.TimeoutError, Exception) as e:
            logger.error(f"Failed to connect to AWS MCP server: {str(e)}")
            self.connected = False
            return False
            
    async def _init_external_mcp_servers(self) -> None:
        """Initialize official AWS MCP servers based on configuration."""
        # Check and install required packages
        await self._ensure_external_mcp_packages()
        
        # Initialize the specialized MCP servers
        for service_type, config in self.mcp_servers.items():
            try:
                package = config.get("package")
                port = config.get("port", 8765)
                
                # Start the MCP server process if needed
                if not self._is_server_running(port):
                    await self._start_external_mcp_server(service_type, package, port)
                
                # Connect to the MCP server
                await self._connect_to_external_mcp(service_type, port)
                
                logger.info(f"Connected to external AWS MCP server for {service_type}")
            except Exception as e:
                logger.error(f"Failed to initialize external MCP server for {service_type}: {str(e)}")
    
    async def _ensure_external_mcp_packages(self) -> None:
        """Ensure all required external AWS MCP packages are installed."""
        for service_type, config in self.mcp_servers.items():
            package = config.get("package")
            if not package:
                continue
                
            try:
                # Check if package is already installed
                importlib.import_module(package.split(".")[0])
                logger.debug(f"Package {package} is already installed")
            except ImportError:
                # Install the package
                logger.info(f"Installing {package} package")
                try:
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install", package, "--quiet"
                    ])
                    logger.info(f"Successfully installed {package}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to install {package}: {str(e)}")
    
    def _is_server_running(self, port: int) -> bool:
        """Check if a server is already running on the specified port."""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    async def _start_external_mcp_server(self, service_type: str, package: str, port: int) -> None:
        """Start an external AWS MCP server."""
        cmd = [
            sys.executable, "-m", package.replace(".", "_"),
            "--port", str(port),
            "--aws-region", self.region_name
        ]
        
        if self.aws_access_key_id and self.aws_secret_access_key:
            env = os.environ.copy()
            env["AWS_ACCESS_KEY_ID"] = self.aws_access_key_id
            env["AWS_SECRET_ACCESS_KEY"] = self.aws_secret_access_key
            env["AWS_REGION"] = self.region_name
        else:
            env = None
        
        logger.info(f"Starting external MCP server for {service_type} on port {port}")
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Store the process for cleanup
        self.external_mcp_processes[service_type] = process
        
        # Wait for server to start
        for _ in range(10):
            if self._is_server_running(port):
                logger.info(f"External MCP server for {service_type} is running")
                return
            await asyncio.sleep(1)
            
        raise AWSClientError(f"Failed to start external MCP server for {service_type}")
    
    async def _connect_to_external_mcp(self, service_type: str, port: int) -> None:
        """Connect to an external AWS MCP server."""
        if service_type == "lambda" and LAMBDA_TOOL_MCP_AVAILABLE:
            from awslabs.lambda_tool_mcp_client import LambdaToolMCPClient
            self.external_servers[service_type] = LambdaToolMCPClient(
                endpoint=f"ws://localhost:{port}/ws",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            )
            await self.external_servers[service_type].connect()
            
        elif service_type == "messaging" and MESSAGING_MCP_AVAILABLE:
            from aws.messaging_mcp_client import MessagingMCPClient
            self.external_servers[service_type] = MessagingMCPClient(
                endpoint=f"ws://localhost:{port}/ws",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            )
            await self.external_servers[service_type].connect()
            
        elif service_type == "mq" and MQ_MCP_AVAILABLE:
            from amazon.mq_mcp_client import MQMCPClient
            self.external_servers[service_type] = MQMCPClient(
                endpoint=f"ws://localhost:{port}/ws",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            )
            await self.external_servers[service_type].connect()
        else:
            # Use generic MCP client as fallback
            logger.warning(f"No specialized MCP client available for {service_type}, using generic client")
            # Use the MCP client class for fallback
            from .mcp_client import MCPClient
            self.external_servers[service_type] = MCPClient(
                service_type,
                f"ws://localhost:{port}/ws"
            )
            await self.external_servers[service_type].connect()
    
    async def disconnect(self):
        """Disconnect from the AWS MCP server and clean up resources."""
        # Disconnect from WebSocket if connected
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
            
        # Disconnect from external MCP servers
        for service_type, server in self.external_servers.items():
            try:
                await server.disconnect()
                logger.info(f"Disconnected from {service_type} MCP server")
            except Exception as e:
                logger.error(f"Error disconnecting from {service_type} MCP server: {str(e)}")
                
        # Terminate external MCP server processes
        for service_type, process in self.external_mcp_processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"Terminated {service_type} MCP server process")
            except Exception as e:
                logger.error(f"Error terminating {service_type} MCP server process: {str(e)}")
            
        # Clear clients
        self.clients = {}
        self.external_servers = {}
        self.external_mcp_processes = {}
        self.lambda_client = None
        self.sns_client = None
        self.sqs_client = None
        self.mq_client = None
        
        self.connected = False
        logger.info("Disconnected from AWS MCP service")
        
    async def init_lambda_service(self) -> bool:
        """
        Initialize the Lambda service with official AWS Lambda Tool MCP Server if available.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            if "lambda" in self.external_servers:
                logger.info("Using initialized Lambda Tool MCP client")
                # Already initialized via external MCP server
                self.lambda_client = self.external_servers["lambda"]
                return True
            
            if LAMBDA_TOOL_MCP_AVAILABLE and self.use_external_mcp_servers:
                # Dynamic import of Lambda Tool MCP client
                from awslabs.lambda_tool_mcp_client import LambdaToolMCPClient
                
                logger.info("Initializing Lambda service with Lambda Tool MCP client")
                self.lambda_client = LambdaToolMCPClient(
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.region_name
                )
                await self.lambda_client.connect()
                return True
            
            if self.use_direct_sdk:
                # Fallback to direct SDK
                logger.info("Initializing Lambda service with direct AWS SDK")
                self.clients["lambda"] = self._get_client("lambda")
                return True
                
            logger.warning("Lambda service initialization skipped (no client available)")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Lambda service: {str(e)}")
            return False
    
    async def init_sns_service(self) -> bool:
        """
        Initialize the SNS service with official AWS Messaging MCP Server if available.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            if "messaging" in self.external_servers:
                logger.info("Using initialized Messaging MCP client for SNS")
                # Already initialized via external MCP server
                self.sns_client = self.external_servers["messaging"]
                return True
            
            if MESSAGING_MCP_AVAILABLE and self.use_external_mcp_servers:
                # Dynamic import of Messaging MCP client
                from aws.messaging_mcp_client import MessagingMCPClient
                
                logger.info("Initializing SNS service with Messaging MCP client")
                self.sns_client = MessagingMCPClient(
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.region_name,
                    service_type="sns"
                )
                await self.sns_client.connect()
                return True
            
            if self.use_direct_sdk:
                # Fallback to direct SDK
                logger.info("Initializing SNS service with direct AWS SDK")
                self.clients["sns"] = self._get_client("sns")
                return True
                
            logger.warning("SNS service initialization skipped (no client available)")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize SNS service: {str(e)}")
            return False
    
    async def init_sqs_service(self) -> bool:
        """
        Initialize the SQS service with official AWS Messaging MCP Server if available.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            if "messaging" in self.external_servers:
                logger.info("Using initialized Messaging MCP client for SQS")
                # Already initialized via external MCP server - same client handles both SNS and SQS
                self.sqs_client = self.external_servers["messaging"]
                return True
            
            if MESSAGING_MCP_AVAILABLE and self.use_external_mcp_servers:
                # Dynamic import of Messaging MCP client
                from aws.messaging_mcp_client import MessagingMCPClient
                
                logger.info("Initializing SQS service with Messaging MCP client")
                if self.sns_client and isinstance(self.sns_client, MessagingMCPClient):
                    # Reuse the SNS client for SQS (they're the same client)
                    self.sqs_client = self.sns_client
                else:
                    # Create a new client
                    self.sqs_client = MessagingMCPClient(
                        aws_access_key_id=self.aws_access_key_id,
                        aws_secret_access_key=self.aws_secret_access_key,
                        region_name=self.region_name,
                        service_type="sqs"
                    )
                    await self.sqs_client.connect()
                return True
            
            if self.use_direct_sdk:
                # Fallback to direct SDK
                logger.info("Initializing SQS service with direct AWS SDK")
                self.clients["sqs"] = self._get_client("sqs")
                return True
                
            logger.warning("SQS service initialization skipped (no client available)")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize SQS service: {str(e)}")
            return False
    
    async def init_mq_service(self) -> bool:
        """
        Initialize the MQ service with official Amazon MQ MCP Server if available.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            if "mq" in self.external_servers:
                logger.info("Using initialized MQ MCP client")
                # Already initialized via external MCP server
                self.mq_client = self.external_servers["mq"]
                return True
            
            if MQ_MCP_AVAILABLE and self.use_external_mcp_servers:
                # Dynamic import of MQ MCP client
                from amazon.mq_mcp_client import MQMCPClient
                
                logger.info("Initializing MQ service with MQ MCP client")
                self.mq_client = MQMCPClient(
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.region_name
                )
                await self.mq_client.connect()
                return True
            
            if self.use_direct_sdk:
                # Fallback to direct SDK
                logger.info("Initializing MQ service with direct AWS SDK")
                self.clients["mq"] = self._get_client("mq")
                return True
                
            logger.warning("MQ service initialization skipped (no client available)")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize MQ service: {str(e)}")
            return False
    
    async def list_mq_brokers(self, next_token: Optional[str] = None, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        List Amazon MQ brokers.
        
        Args:
            next_token: Token for pagination
            max_results: Maximum number of results to return
            
        Returns:
            List of broker information
        """
        try:
            # Try using initialized MQ client first
            if self.mq_client:
                if hasattr(self.mq_client, "list_brokers"):
                    # Using MQ MCP client
                    logger.info("Listing brokers using MQ MCP client")
                    response = await self.mq_client.list_brokers(
                        next_token=next_token,
                        max_results=max_results
                    )
                    return response.get("Brokers", [])
                elif "mq" in self.external_servers:
                    # Using generic MCP client for MQ
                    logger.info("Listing brokers using generic MCP client")
                    response = await self.external_servers["mq"].call_tool("list_brokers", {
                        "next_token": next_token,
                        "max_results": max_results
                    })
                    return response.get("Brokers", [])
            
            # Fall back to direct SDK
            if self.use_direct_sdk:
                logger.info("Listing brokers using direct AWS SDK")
                mq_client = self._get_client('mq')
                
                kwargs = {'MaxResults': max_results}
                if next_token:
                    kwargs['NextToken'] = next_token
                
                response = mq_client.list_brokers(**kwargs)
                
                # Convert to standard format
                brokers = []
                for broker in response.get('BrokerSummaries', []):
                    brokers.append({
                        'BrokerId': broker.get('BrokerId'),
                        'BrokerName': broker.get('BrokerName'),
                        'BrokerState': broker.get('BrokerState'),
                        'DeploymentMode': broker.get('DeploymentMode'),
                        'HostInstanceType': broker.get('HostInstanceType')
                    })
                
                return brokers
            else:
                # Fall back to standard MCP server
                logger.info("Listing brokers using standard MCP server")
                response = await self._call_mcp_method("list_mq_brokers", {
                    "next_token": next_token,
                    "max_results": max_results
                })
                return response.get("Brokers", [])
        except (ClientError, BotoCoreError, Exception) as e:
            error_msg = f"Failed to list MQ brokers: {str(e)}"
            logger.error(error_msg)
            raise AWSClientError(error_msg)
    
    async def get_mq_broker(self, broker_id: str) -> Dict[str, Any]:
        """
        Get details of an Amazon MQ broker.
        
        Args:
            broker_id: The ID of the broker
            
        Returns:
            Dictionary containing broker details
        """
        try:
            # Try using initialized MQ client first
            if self.mq_client:
                if hasattr(self.mq_client, "describe_broker"):
                    # Using MQ MCP client
                    logger.info(f"Getting broker details using MQ MCP client: {broker_id}")
                    return await self.mq_client.describe_broker(broker_id=broker_id)
                elif "mq" in self.external_servers:
                    # Using generic MCP client for MQ
                    logger.info(f"Getting broker details using generic MCP client: {broker_id}")
                    return await self.external_servers["mq"].call_tool("describe_broker", {
                        "broker_id": broker_id
                    })
            
            # Fall back to direct SDK
            if self.use_direct_sdk:
                logger.info(f"Getting broker details using direct AWS SDK: {broker_id}")
                mq_client = self._get_client('mq')
                
                response = mq_client.describe_broker(BrokerId=broker_id)
                
                # Convert to standard format
                broker_details = {
                    'BrokerId': response.get('BrokerId'),
                    'BrokerName': response.get('BrokerName'),
                    'BrokerState': response.get('BrokerState'),
                    'DeploymentMode': response.get('DeploymentMode'),
                    'EngineType': response.get('EngineType'),
                    'EngineVersion': response.get('EngineVersion'),
                    'HostInstanceType': response.get('HostInstanceType'),
                    'PubliclyAccessible': response.get('PubliclyAccessible', False),
                    'Endpoints': response.get('BrokerInstances', [{}])[0].get('Endpoints', []),
                    'Created': response.get('Created').isoformat() if response.get('Created') else None
                }
                
                # Add information about destinations (queues/topics) if available
                if 'Configurations' in response and response.get('Configurations'):
                    destinations = []
                    for config in response.get('Configurations').values():
                        if isinstance(config, dict) and 'Id' in config:
                            # This is a simplification, in a real implementation you would
                            # make an additional call to get the actual destinations
                            destinations.append({
                                'Name': config.get('Name', 'Unknown'),
                                'Type': config.get('Type', 'queue'),
                                'ConfigId': config.get('Id')
                            })
                    
                    broker_details['Destinations'] = destinations
                
                return broker_details
            else:
                # Fall back to standard MCP server
                logger.info(f"Getting broker details using standard MCP server: {broker_id}")
                return await self._call_mcp_method("get_mq_broker", {
                    "broker_id": broker_id
                })
        except (ClientError, BotoCoreError, Exception) as e:
            error_msg = f"Failed to get MQ broker details: {str(e)}"
            logger.error(error_msg)
            raise AWSClientError(error_msg)
    
    async def send_mq_message(self, 
                             broker_id: str, 
                             destination_type: str, 
                             destination_name: str,
                             message_body: str,
                             message_attributes: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send a message to an Amazon MQ broker.
        
        Args:
            broker_id: The ID of the broker
            destination_type: Type of destination ('queue' or 'topic')
            destination_name: Name of the destination
            message_body: The message content to send
            message_attributes: Optional message attributes
            
        Returns:
            Dictionary containing message ID or status
        """
        try:
            # Try using initialized MQ client first
            if self.mq_client:
                if hasattr(self.mq_client, "send_message"):
                    # Using MQ MCP client
                    logger.info(f"Sending message using MQ MCP client to {destination_type}/{destination_name}")
                    return await self.mq_client.send_message(
                        broker_id=broker_id,
                        destination_type=destination_type,
                        destination_name=destination_name,
                        message_body=message_body,
                        message_attributes=message_attributes or {}
                    )
                elif "mq" in self.external_servers:
                    # Using generic MCP client for MQ
                    logger.info(f"Sending message using generic MCP client to {destination_type}/{destination_name}")
                    return await self.external_servers["mq"].call_tool("send_message", {
                        "broker_id": broker_id,
                        "destination_type": destination_type,
                        "destination_name": destination_name,
                        "message_body": message_body,
                        "message_attributes": message_attributes or {}
                    })
            
            # Fall back to direct SDK - this is complex and would typically require a separate client
            # like stomp.py, so this is a placeholder implementation
            if self.use_direct_sdk:
                logger.info(f"Sending message using direct AWS SDK to {destination_type}/{destination_name}")
                # This would require additional implementation for direct message sending
                # In a real implementation, you might use stomp.py with the broker endpoints
                
                # For demonstration purposes, we'll just log the attempt and return a mock response
                logger.warning("Direct SDK implementation for MQ message sending is a placeholder")
                return {
                    "MessageId": f"mock-{broker_id}-{destination_name}",
                    "Status": "PLACEHOLDER_NOT_ACTUALLY_SENT"
                }
            else:
                # Fall back to standard MCP server
                logger.info(f"Sending message using standard MCP server to {destination_type}/{destination_name}")
                return await self._call_mcp_method("send_mq_message", {
                    "broker_id": broker_id,
                    "destination_type": destination_type,
                    "destination_name": destination_name,
                    "message_body": message_body,
                    "message_attributes": message_attributes or {}
                })
        except (ClientError, BotoCoreError, Exception) as e:
            error_msg = f"Failed to send MQ message: {str(e)}"
            logger.error(error_msg)
            raise AWSClientError(error_msg)
    
    async def receive_mq_messages(self,
                               broker_id: str, 
                               destination_type: str, 
                               destination_name: str,
                               max_messages: int = 10,
                               wait_time_seconds: int = 0) -> List[Dict[str, Any]]:
        """
        Receive messages from an Amazon MQ broker.
        
        Args:
            broker_id: The ID of the broker
            destination_type: Type of destination ('queue' or 'topic')
            destination_name: Name of the destination
            max_messages: Maximum number of messages to receive
            wait_time_seconds: Time to wait for messages in seconds
            
        Returns:
            List of received messages
        """
        try:
            # Try using initialized MQ client first
            if self.mq_client:
                if hasattr(self.mq_client, "receive_messages"):
                    # Using MQ MCP client
                    logger.info(f"Receiving messages using MQ MCP client from {destination_type}/{destination_name}")
                    response = await self.mq_client.receive_messages(
                        broker_id=broker_id,
                        destination_type=destination_type,
                        destination_name=destination_name,
                        max_messages=max_messages,
                        wait_time_seconds=wait_time_seconds
                    )
                    return response.get("Messages", [])
                elif "mq" in self.external_servers:
                    # Using generic MCP client for MQ
                    logger.info(f"Receiving messages using generic MCP client from {destination_type}/{destination_name}")
                    response = await self.external_servers["mq"].call_tool("receive_messages", {
                        "broker_id": broker_id,
                        "destination_type": destination_type,
                        "destination_name": destination_name,
                        "max_messages": max_messages,
                        "wait_time_seconds": wait_time_seconds
                    })
                    return response.get("Messages", [])
            
            # Fall back to direct SDK - this is complex and would typically require a separate client
            if self.use_direct_sdk:
                logger.info(f"Receiving messages using direct AWS SDK from {destination_type}/{destination_name}")
                # This would require additional implementation for direct message receiving
                # In a real implementation, you might use stomp.py with the broker endpoints
                
                # For demonstration purposes, we'll just log the attempt and return an empty list
                logger.warning("Direct SDK implementation for MQ message receiving is a placeholder")
                return []
            else:
                # Fall back to standard MCP server
                logger.info(f"Receiving messages using standard MCP server from {destination_type}/{destination_name}")
                response = await self._call_mcp_method("receive_mq_messages", {
                    "broker_id": broker_id,
                    "destination_type": destination_type,
                    "destination_name": destination_name,
                    "max_messages": max_messages,
                    "wait_time_seconds": wait_time_seconds
                })
                return response.get("Messages", [])
        except (ClientError, BotoCoreError, Exception) as e:
            error_msg = f"Failed to receive MQ messages: {str(e)}"
            logger.error(error_msg)
            raise AWSClientError(error_msg)
    
    # --- Customer operations (required by MCPClientInterface) ---
    async def get_customers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get customers from the database."""
        # This operation would typically be handled by a database MCP client
        # For AWS MCP client, we can implement with DynamoDB if needed
        return []
    
    async def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific customer by ID."""
        # This operation would typically be handled by a database MCP client
        return None
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer."""
        # This operation would typically be handled by a database MCP client
        return {}
    
    async def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer information."""
        # This operation would typically be handled by a database MCP client
        return {}
    
    # Ticket operations
    async def get_tickets(self, limit: int = 100, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get support tickets."""
        # This operation would typically be handled by a database MCP client
        return []
    
    async def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific ticket by ID."""
        # This operation would typically be handled by a database MCP client
        return None
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new support ticket."""
        # This operation would typically be handled by a database MCP client
        return {}
    
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update ticket information."""
        # This operation would typically be handled by a database MCP client
        return {}
    
    # --- AWS-specific operations ---
    
    # Lambda operations
    async def invoke_lambda(self, function_name: str, payload: Dict[str, Any], 
                            invocation_type: str = "RequestResponse",
                            client_context: Optional[Dict[str, Any]] = None,
                            qualifier: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoke an AWS Lambda function.
        
        Args:
            function_name: Name or ARN of the Lambda function
            payload: Function input payload as a dictionary
            invocation_type: RequestResponse (synchronous) or Event (asynchronous)
            client_context: Client context to pass to the Lambda function
            qualifier: Version or alias of the function
        
        Returns:
            Dictionary containing the function response
        """
        try:
            # Try using initialized Lambda client first
            if self.lambda_client:
                if hasattr(self.lambda_client, "invoke_function"):
                    # Using Lambda Tool MCP client
                    logger.info(f"Invoking Lambda function {function_name} using Lambda Tool MCP client")
                    response = await self.lambda_client.invoke_function(
                        function_name=function_name,
                        payload=payload,
                        invocation_type=invocation_type,
                        client_context=client_context,
                        qualifier=qualifier
                    )
                    return response
                elif hasattr(self.lambda_client, "invoke"):
                    # Using official Lambda Tool MCP client with different API
                    logger.info(f"Invoking Lambda function {function_name} using official Lambda Tool MCP client")
                    response = await self.lambda_client.invoke(
                        function_name=function_name,
                        payload=payload,
                        invocation_type=invocation_type,
                        client_context=client_context,
                        qualifier=qualifier
                    )
                    return response
                elif "lambda" in self.external_servers:
                    # Using generic MCP client for Lambda
                    logger.info(f"Invoking Lambda function {function_name} using generic MCP client")
                    return await self.external_servers["lambda"].call_tool("invoke_lambda", {
                        "function_name": function_name,
                        "payload": payload,
                        "invocation_type": invocation_type,
                        "client_context": client_context,
                        "qualifier": qualifier
                    })
            
            # Fall back to direct SDK
            if self.use_direct_sdk:
                logger.info(f"Invoking Lambda function {function_name} using direct AWS SDK")
                lambda_client = self._get_client('lambda')
                payload_bytes = json.dumps(payload).encode('utf-8')
                
                invoke_kwargs = {
                    "FunctionName": function_name,
                    "InvocationType": invocation_type,
                    "Payload": payload_bytes
                }
                
                if client_context:
                    # Encode client context as base64
                    context_json = json.dumps(client_context)
                    context_bytes = context_json.encode('utf-8')
                    invoke_kwargs["ClientContext"] = base64.b64encode(context_bytes).decode('utf-8')
                    
                if qualifier:
                    invoke_kwargs["Qualifier"] = qualifier
                
                response = lambda_client.invoke(**invoke_kwargs)
                
                result = {
                    'StatusCode': response.get('StatusCode'),
                    'ExecutedVersion': response.get('ExecutedVersion'),
                }
                
                if 'Payload' in response:
                    payload_content = response['Payload'].read().decode('utf-8')
                    try:
                        result['Payload'] = json.loads(payload_content)
                    except:
                        result['Payload'] = payload_content
                
                return result
            else:
                # Fall back to standard MCP server
                logger.info(f"Invoking Lambda function {function_name} using standard MCP server")
                return await self._call_mcp_method("invoke_lambda", {
                    "function_name": function_name,
                    "payload": payload,
                    "invocation_type": invocation_type,
                    "client_context": client_context,
                    "qualifier": qualifier
                })
        except (ClientError, BotoCoreError, Exception) as e:
            error_msg = f"Lambda invocation failed: {str(e)}"
            logger.error(error_msg)
            raise AWSClientError(error_msg)
    
    async def list_lambda_functions(self, max_items: int = 50) -> List[Dict[str, Any]]:
        """
        List Lambda functions in the account.
        
        Args:
            max_items: Maximum number of functions to return
        
        Returns:
            List of Lambda function metadata
        """
        try:
            if self.use_direct_sdk:
                lambda_client = self._get_client('lambda')
                response = lambda_client.list_functions(MaxItems=max_items)
                return response.get('Functions', [])
            else:
                return await self._call_mcp_method("list_lambda_functions", {
                    "max_items": max_items
                })
        except (ClientError, BotoCoreError, Exception) as e:
            error_msg = f"Failed to list Lambda functions: {str(e)}"
            logger.error(error_msg)
            raise AWSClientError(error_msg)
    
    # S3 operations
    async def list_s3_buckets(self) -> List[Dict[str, Any]]:
        """
        List S3 buckets in the account.
        
        Returns:
            List of S3 bucket metadata
        """
        try:
            if self.use_direct_sdk:
                s3_client = self._get_client('s3')
                response = s3_client.list_buckets()
                return response.get('Buckets', [])
            else:
                return await self._call_mcp_method("list_s3_buckets")
        except (ClientError, BotoCoreError, Exception) as e:
            error_msg = f"Failed to list S3 buckets: {str(e)}"
            logger.error(error_msg)
            raise AWSClientError(error_msg)
    
    async def list_s3_objects(self, bucket: str, prefix: str = "", max_keys: int = 1000) -> Dict[str, Any]:
        """
        List objects in an S3 bucket.
        
        Args:
            bucket: Name of the S3 bucket
            prefix: Filter objects by prefix
            max_keys: Maximum number of keys to return
        
        Returns:
            Dictionary containing objects metadata
        """
        try:
            if self.use_direct_sdk:
                s3_client = self._get_client('s3')
                response = s3_client.list_objects_v2(
                    Bucket=bucket,
                    Prefix=prefix,
                    MaxKeys=max_keys
                )
                return {
                    'Objects': response.get('Contents', []),
                    'IsTruncated': response.get('IsTruncated', False),
                    'NextContinuationToken': response.get('NextContinuationToken')
                }
            else:
                return await self._call_mcp_method("list_s3_objects", {
                    "bucket": bucket,
                    "prefix": prefix,
                    "max_keys": max_keys
                })
        except (ClientError, BotoCoreError, Exception) as e:
            error_msg = f"Failed to list S3 objects: {str(e)}"
            logger.error(error_msg)
            raise AWSClientError(error_msg)
    
    async def get_s3_object(self, bucket: str, key: str) -> Dict[str, Any]:
        """
        Get an object from an S3 bucket.
        
        Args:
            bucket: Name of the S3 bucket
            key: Object key (path)
        
        Returns:
            Dictionary containing object data and metadata
        """
        try:
            if self.use_direct_sdk:
                s3_client = self._get_client('s3')
                response = s3_client.get_object(Bucket=bucket, Key=key)
                
                body = response['Body'].read()
                content_type = response.get('ContentType', '')
                
                # Decide how to handle the body based on content type
                if 'text/' in content_type or 'application/json' in content_type:
                    try:
                        body_content = body.decode('utf-8')
                    except UnicodeDecodeError:
                        body_content = base64.b64encode(body).decode('ascii')
                else:
                    body_content = base64.b64encode(body).decode('ascii')
                
                return {
                    'Body': body_content,
                    'ContentType': content_type,
                    'ContentLength': response.get('ContentLength'),
                    'LastModified': response.get('LastModified').isoformat() 
                      if response.get('LastModified') else None,
                    'Metadata': response.get('Metadata', {}),
                    'IsBase64Encoded': 'text/' not in content_type and 'application/json' not in content_type
                }
            else:
                return await self._call_mcp_method("get_s3_object", {
                    "bucket": bucket,
                    "key": key
                })
        except (ClientError, BotoCoreError, Exception) as e:
            error_msg = f"Failed to get S3 object: {str(e)}"
            logger.error(error_msg)
            raise AWSClientError(error_msg)
    
    async def put_s3_object(self, bucket: str, key: str, body: Union[str, bytes], 
                           content_type: str = "application/octet-stream",
                           metadata: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Put an object into an S3 bucket.
        
        Args:
            bucket: Name of the S3 bucket
            key: Object key (path)
            body: Object content as string or bytes
            content_type: MIME type of the object
            metadata: Object metadata
        
        Returns:
            Dictionary containing operation result
        """
        try:
            if self.use_direct_sdk:
                s3_client = self._get_client('s3')
                
                # Convert string to bytes if necessary
                if isinstance(body, str):
                    body = body.encode('utf-8')
                
                kwargs = {
                    'Bucket': bucket,
                    'Key': key,
                    'Body': body,
                    'ContentType': content_type
                }
                
                if metadata:
                    kwargs['Metadata'] = metadata
                
                response = s3_client.put_object(**kwargs)
                return {
                    'ETag': response.get('ETag', '').strip('"'),
                    'VersionId': response.get('VersionId')
                }
            else:
                # For MCP server, encode binary data as base64 if needed
                if isinstance(body, bytes):
                    body = base64.b64encode(body).decode('ascii')
                    is_base64 = True
                else:
                    is_base64 = False
                
                return await self._call_mcp_method("put_s3_object", {
                    "bucket": bucket,
                    "key": key,
                    "body": body,
                    "content_type": content_type,
                    "metadata": metadata or {},
                    "is_base64_encoded": is_base64
                })
        except (ClientError, BotoCoreError, Exception) as e:
            error_msg = f"Failed to put S3 object: {str(e)}"
            logger.error(error_msg)
            raise AWSClientError(error_msg)
    
    # SQS operations
    async def send_sqs_message(self, queue_url: str, message_body: str,
                              delay_seconds: int = 0,
                              message_attributes: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send a message to an SQS queue.
        
        Args:
            queue_url: URL of the SQS queue
            message_body: Message body
            delay_seconds: Delay in seconds before message is visible
            message_attributes: Message attributes
        
        Returns:
            Dictionary containing the message ID and MD5 hash
        """
        try:
            if self.use_direct_sdk:
                sqs_client = self._get_client('sqs')
                
                kwargs = {
                    'QueueUrl': queue_url,
                    'MessageBody': message_body
                }
                
                if delay_seconds > 0:
                    kwargs['DelaySeconds'] = delay_seconds
                
                if message_attributes:
                    # Convert message attributes to SQS format
                    formatted_attrs = {}
                    for key, value in message_attributes.items():
                        if isinstance(value, str):
                            attr_type = 'String'
                            attr_value = value
                        elif isinstance(value, (int, float)):
                            attr_type = 'Number'
                            attr_value = str(value)
                        elif isinstance(value, bytes):
                            attr_type = 'Binary'
                            attr_value = value
                        else:
                            continue
                        
                        formatted_attrs[key] = {
                            'DataType': 'String', # SQS requires this
                            attr_type: attr_value
                        }
                    
                    kwargs['MessageAttributes'] = formatted_attrs
                
                response = sqs_client.send_message(**kwargs)
                return {
                    'MessageId': response.get('MessageId'),
                    'MD5OfMessageBody': response.get('MD5OfMessageBody')
                }
            else:
                return await self._call_mcp_method("send_sqs_message", {
                    "queue_url": queue_url,
                    "message_body": message_body,
                    "delay_seconds": delay_seconds,
                    "message_attributes": message_attributes or {}
                })
        except (ClientError, BotoCoreError, Exception) as e:
            error_msg = f"Failed to send SQS message: {str(e)}"
            logger.error(error_msg)
            raise AWSClientError(error_msg)
    
    async def receive_sqs_messages(self, queue_url: str, max_messages: int = 10,
                                  wait_time_seconds: int = 0,
                                  visibility_timeout: int = 30) -> List[Dict[str, Any]]:
        """
        Receive messages from an SQS queue.
        
        Args:
            queue_url: URL of the SQS queue
            max_messages: Maximum number of messages to receive (1-10)
            wait_time_seconds: Long polling wait time (0-20)
            visibility_timeout: Visibility timeout in seconds
        
        Returns:
            List of received messages
        """
        try:
            if self.use_direct_sdk:
                sqs_client = self._get_client('sqs')
                
                response = sqs_client.receive_message(
                    QueueUrl=queue_url,
                    MaxNumberOfMessages=max(1, min(max_messages, 10)),
                    WaitTimeSeconds=max(0, min(wait_time_seconds, 20)),
                    VisibilityTimeout=visibility_timeout,
                    AttributeNames=['All'],
                    MessageAttributeNames=['All']
                )
                
                return response.get('Messages', [])
            else:
                return await self._call_mcp_method("receive_sqs_messages", {
                    "queue_url": queue_url,
                    "max_messages": max_messages,
                    "wait_time_seconds": wait_time_seconds,
                    "visibility_timeout": visibility_timeout
                })
        except (ClientError, BotoCoreError, Exception) as e:
            error_msg = f"Failed to receive SQS messages: {str(e)}"
            logger.error(error_msg)
            raise AWSClientError(error_msg)
    
    async def delete_sqs_message(self, queue_url: str, receipt_handle: str) -> Dict[str, Any]:
        """
        Delete a message from an SQS queue.
        
        Args:
            queue_url: URL of the SQS queue
            receipt_handle: Receipt handle of the message to delete
        
        Returns:
            Dictionary indicating success
        """
        try:
            if self.use_direct_sdk:
                sqs_client = self._get_client('sqs')
                
                sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle
                )
                
                return {"success": True}
            else:
                return await self._call_mcp_method("delete_sqs_message", {
                    "queue_url": queue_url,
                    "receipt_handle": receipt_handle
                })
        except (ClientError, BotoCoreError, Exception) as e:
            error_msg = f"Failed to delete SQS message: {str(e)}"
            logger.error(error_msg)
            raise AWSClientError(error_msg)
    
    # SNS operations
    async def publish_sns_message(self, topic_arn: str, message: str, 
                                 subject: Optional[str] = None,
                                 message_attributes: Dict[str, Any] = None,
                                 message_structure: Optional[str] = None) -> Dict[str, Any]:
        """
        Publish a message to an SNS topic.
        
        Args:
            topic_arn: ARN of the SNS topic
            message: Message content
            subject: Optional subject line
            message_attributes: Message attributes
            message_structure: Structure of the message (json, etc.)
        
        Returns:
            Dictionary containing the message ID
        """
        try:
            # Try using initialized SNS client first
            if self.sns_client:
                if hasattr(self.sns_client, "publish_message"):
                    # Using Messaging MCP client
                    logger.info(f"Publishing SNS message to {topic_arn} using Messaging MCP client")
                    response = await self.sns_client.publish_message(
                        topic_arn=topic_arn,
                        message=message,
                        subject=subject,
                        message_attributes=message_attributes,
                        message_structure=message_structure
                    )
                    return response
                elif "messaging" in self.external_servers:
                    # Using generic MCP client for messaging
                    logger.info(f"Publishing SNS message to {topic_arn} using generic MCP client")
                    return await self.external_servers["messaging"].call_tool("publish_sns_message", {
                        "topic_arn": topic_arn,
                        "message": message,
                        "subject": subject,
                        "message_attributes": message_attributes or {},
                        "message_structure": message_structure
                    })
            
            # Fall back to direct SDK
            if self.use_direct_sdk:
                logger.info(f"Publishing SNS message to {topic_arn} using direct AWS SDK")
                sns_client = self._get_client('sns')
                
                kwargs = {
                    'TopicArn': topic_arn,
                    'Message': message
                }
                
                if subject:
                    kwargs['Subject'] = subject
                    
                if message_structure:
                    kwargs['MessageStructure'] = message_structure
                
                if message_attributes:
                    # Convert message attributes to SNS format
                    formatted_attrs = {}
                    for key, value in message_attributes.items():
                        if isinstance(value, str):
                            attr_type = 'String'
                            attr_value = value
                        elif isinstance(value, (int, float)):
                            attr_type = 'Number'
                            attr_value = str(value)
                        elif isinstance(value, bytes):
                            attr_type = 'Binary'
                            attr_value = value
                        else:
                            continue
                        
                        formatted_attrs[key] = {
                            'DataType': 'String', # SNS requires this
                            attr_type + 'Value': attr_value
                        }
                    
                    kwargs['MessageAttributes'] = formatted_attrs
                
                response = sns_client.publish(**kwargs)
                return {"MessageId": response.get('MessageId')}
            else:
                # Fall back to standard MCP server
                logger.info(f"Publishing SNS message to {topic_arn} using standard MCP server")
                return await self._call_mcp_method("publish_sns_message", {
                    "topic_arn": topic_arn,
                    "message": message,
                    "subject": subject,
                    "message_attributes": message_attributes or {},
                    "message_structure": message_structure
                })
        except (ClientError, BotoCoreError, Exception) as e:
            error_msg = f"Failed to publish SNS message: {str(e)}"
            logger.error(error_msg)
            raise AWSClientError(error_msg)
    
    async def list_sns_topics(self, next_token: Optional[str] = None) -> Dict[str, Any]:
        """
        List SNS topics in the account.
        
        Args:
            next_token: Pagination token for additional results
        
        Returns:
            Dictionary containing topics and next pagination token
        """
        try:
            if self.use_direct_sdk:
                sns_client = self._get_client('sns')
                
                kwargs = {}
                if next_token:
                    kwargs['NextToken'] = next_token
                
                response = sns_client.list_topics(**kwargs)
                
                return {
                    'Topics': response.get('Topics', []),
                    'NextToken': response.get('NextToken')
                }
            else:
                return await self._call_mcp_method("list_sns_topics", {
                    "next_token": next_token
                })
        except (ClientError, BotoCoreError, Exception) as e:
            error_msg = f"Failed to list SNS topics: {str(e)}"
            logger.error(error_msg)
            raise AWSClientError(error_msg)

    # Secret Manager operations
    async def get_secret(self, secret_id: str, version_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a secret from AWS Secrets Manager.
        
        Args:
            secret_id: The ARN or name of the secret
            version_id: The version of the secret (optional)
        
        Returns:
            Dictionary containing the secret value
        """
        try:
            if self.use_direct_sdk:
                secretsmanager_client = self._get_client('secretsmanager')
                
                kwargs = {'SecretId': secret_id}
                if version_id:
                    kwargs['VersionId'] = version_id
                
                response = secretsmanager_client.get_secret_value(**kwargs)
                
                result = {
                    'ARN': response.get('ARN'),
                    'Name': response.get('Name'),
                    'VersionId': response.get('VersionId'),
                    'VersionStages': response.get('VersionStages', []),
                    'CreatedDate': response.get('CreatedDate').isoformat() if response.get('CreatedDate') else None
                }
                
                # Handle the secret data
                if 'SecretString' in response:
                    result['SecretString'] = response['SecretString']
                    try:
                        # Try to parse as JSON
                        result['SecretJson'] = json.loads(response['SecretString'])
                    except:
                        # Not valid JSON, just use as string
                        pass
                elif 'SecretBinary' in response:
                    result['SecretBinary'] = base64.b64encode(response['SecretBinary']).decode('ascii')
                
                return result
            else:
                return await self._call_mcp_method("get_secret", {
                    "secret_id": secret_id,
                    "version_id": version_id
                })
        except (ClientError, BotoCoreError, Exception) as e:
            error_msg = f"Failed to get secret: {str(e)}"
            logger.error(error_msg)
            raise AWSClientError(error_msg)
    
    # DynamoDB operations
    async def dynamodb_get_item(self, table_name: str, key: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get an item from a DynamoDB table.
        
        Args:
            table_name: Name of the DynamoDB table
            key: Key attributes that define the item
        
        Returns:
            Dictionary containing the item attributes
        """
        try:
            if self.use_direct_sdk:
                dynamodb_client = self._get_client('dynamodb')
                
                # Convert Python types to DynamoDB types
                dynamodb_key = {}
                for k, v in key.items():
                    if isinstance(v, str):
                        dynamodb_key[k] = {'S': v}
                    elif isinstance(v, (int, float)):
                        dynamodb_key[k] = {'N': str(v)}
                    elif isinstance(v, bool):
                        dynamodb_key[k] = {'BOOL': v}
                    elif v is None:
                        dynamodb_key[k] = {'NULL': True}
                    elif isinstance(v, bytes):
                        dynamodb_key[k] = {'B': v}
                    elif isinstance(v, list):
                        if all(isinstance(x, str) for x in v):
                            dynamodb_key[k] = {'SS': v}
                        elif all(isinstance(x, (int, float)) for x in v):
                            dynamodb_key[k] = {'NS': [str(x) for x in v]}
                        elif all(isinstance(x, bytes) for x in v):
                            dynamodb_key[k] = {'BS': v}
                        else:
                            dynamodb_key[k] = {'L': self._convert_to_dynamodb(v)}
                    elif isinstance(v, dict):
                        dynamodb_key[k] = {'M': self._convert_to_dynamodb(v)}
                
                response = dynamodb_client.get_item(
                    TableName=table_name,
                    Key=dynamodb_key
                )
                
                if 'Item' in response:
                    # Convert DynamoDB types back to Python types
                    return self._convert_from_dynamodb(response['Item'])
                else:
                    return {}
            else:
                return await self._call_mcp_method("dynamodb_get_item", {
                    "table_name": table_name,
                    "key": key
                })
        except (ClientError, BotoCoreError, Exception) as e:
            error_msg = f"Failed to get DynamoDB item: {str(e)}"
            logger.error(error_msg)
            raise AWSClientError(error_msg)
    
    def _convert_to_dynamodb(self, value: Any) -> Dict[str, Any]:
        """Convert Python value to DynamoDB format."""
        if isinstance(value, str):
            return {'S': value}
        elif isinstance(value, (int, float)):
            return {'N': str(value)}
        elif isinstance(value, bool):
            return {'BOOL': value}
        elif value is None:
            return {'NULL': True}
        elif isinstance(value, bytes):
            return {'B': value}
        elif isinstance(value, list):
            return {'L': [self._convert_to_dynamodb(v) for v in value]}
        elif isinstance(value, dict):
            return {'M': {k: self._convert_to_dynamodb(v) for k, v in value.items()}}
        else:
            return {'S': str(value)}
    
    def _convert_from_dynamodb(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert DynamoDB format to Python values."""
        result = {}
        for k, v in item.items():
            if 'S' in v:
                result[k] = v['S']
            elif 'N' in v:
                # Try to convert to int or float
                try:
                    if '.' in v['N']:
                        result[k] = float(v['N'])
                    else:
                        result[k] = int(v['N'])
                except:
                    result[k] = v['N']
            elif 'BOOL' in v:
                result[k] = v['BOOL']
            elif 'NULL' in v:
                result[k] = None
            elif 'B' in v:
                result[k] = v['B']
            elif 'L' in v:
                result[k] = [self._convert_from_dynamodb({'item': item})[
                    'item'] for item in v['L']]
            elif 'M' in v:
                result[k] = self._convert_from_dynamodb(v['M'])
            elif 'SS' in v:
                result[k] = v['SS']
            elif 'NS' in v:
                result[k] = [float(x) if '.' in x else int(x) for x in v['NS']]
            elif 'BS' in v:
                result[k] = v['BS']
        
        return result
