"""
MCP Client Manager
Provides centralized management of multiple MCP client connections.
"""
import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING

from .mcp_client_interface import MCPClientInterface

if TYPE_CHECKING:
    from .mcp_client import MCPClient
    from .aws_mcp_client import OptimizedAWSMCPClient


class MCPClientManager:
    """
    Manager for multiple MCP clients.
    
    Provides centralized management of multiple MCP client connections,
    including lifecycle management, tool routing, and resource access
    across different MCP servers.
    """
    
    def __init__(self):
        """Initialize the MCP client manager."""
        self.clients = {}
        self.logger = logging.getLogger("MCP.ClientManager")
    
    async def add_client(self, server_id: str, connection_uri: str) -> bool:
        """
        Add and connect a new MCP client.
        
        Args:
            server_id: Unique identifier for the server
            connection_uri: WebSocket URI for the server
            
        Returns:
            bool: True if client added successfully, False otherwise
        """
        if server_id in self.clients:
            self.logger.warning(f"Client {server_id} already exists")
            return False
        
        # Import here to avoid circular imports
        from .mcp_client import MCPClient
        
        client = MCPClient(server_id, connection_uri)
        success = await client.connect()
        
        if success:
            self.clients[server_id] = client
            self.logger.info(f"Added MCP client: {server_id}")
            return True
        else:
            self.logger.error(f"Failed to add MCP client: {server_id}")
            return False
    
    async def remove_client(self, server_id: str):
        """
        Remove and disconnect an MCP client.
        
        Args:
            server_id: ID of the client to remove
        """
        if server_id in self.clients:
            await self.clients[server_id].disconnect()
            del self.clients[server_id]
            self.logger.info(f"Removed MCP client: {server_id}")
    
    def get_client(self, server_id: str) -> Optional['MCPClient']:
        """
        Get an MCP client by server ID.
        
        Args:
            server_id: ID of the client to retrieve
            
        Returns:
            MCPClient or None: The client instance if found
        """
        return self.clients.get(server_id)
    
    async def call_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call a tool on a specific MCP server.
        
        Args:
            server_id: ID of the server to call tool on
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            dict: Tool execution result
            
        Raises:
            ValueError: If client not found
        """
        client = self.get_client(server_id)
        if not client:
            raise ValueError(f"MCP client '{server_id}' not found")
        
        return await client.call_tool(tool_name, arguments)
    
    async def get_resource(self, server_id: str, resource_uri: str) -> Dict[str, Any]:
        """
        Get a resource from a specific MCP server.
        
        Args:
            server_id: ID of the server to get resource from
            resource_uri: URI of the resource to retrieve
            
        Returns:
            dict: Resource data
            
        Raises:
            ValueError: If client not found
        """
        client = self.get_client(server_id)
        if not client:
            raise ValueError(f"MCP client '{server_id}' not found")
        
        return await client.get_resource(resource_uri)
    
    def list_clients(self) -> List[Dict[str, Any]]:
        """
        List all connected clients with their information.
        
        Returns:
            list: List of client information dictionaries
        """
        return [client.get_server_info() for client in self.clients.values()]
    
    async def disconnect_all(self):
        """Disconnect all managed clients and clear the client registry."""
        for client in self.clients.values():
            await client.disconnect()
        self.clients.clear()
        self.logger.info("Disconnected all MCP clients")
    
    async def add_aws_client(self, 
                           server_id: str, 
                           connection_uri: str = "ws://localhost:8765/ws",
                           aws_access_key_id: Optional[str] = None,
                           aws_secret_access_key: Optional[str] = None,
                           region_name: str = "us-east-1",
                           use_external_mcp_servers: bool = True,
                           service_types: List[str] = None,
                           mcp_servers: Dict[str, Dict[str, Any]] = None,
                           timeout: int = 30,
                           max_retries: int = 3,
                           use_direct_sdk: bool = True,
                           install_packages: bool = True) -> bool:
        """
        Add and connect an AWS MCP client with support for official external AWS MCP servers.
        
        Args:
            server_id: Unique identifier for the server
            connection_uri: WebSocket URI for the server
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region_name: AWS region name
            use_external_mcp_servers: Whether to use official external AWS MCP servers
            service_types: List of AWS service types to initialize (lambda, sns, sqs, mq)
            mcp_servers: Custom configuration for external MCP servers
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            use_direct_sdk: Whether to use AWS SDK directly when available
            install_packages: Whether to automatically install required packages
            
        Returns:
            bool: True if client added successfully, False otherwise
        """
        if server_id in self.clients:
            self.logger.warning(f"Client {server_id} already exists")
            return False
        
        # Import here to avoid circular imports
        from .aws_mcp_client import OptimizedAWSMCPClient
        
        # Default to all service types if none specified
        if service_types is None:
            service_types = ["lambda", "sns", "sqs", "mq"]
        
        # Configure service-specific MCP servers if not provided
        if mcp_servers is None and use_external_mcp_servers:
            mcp_servers = {}
            # Configure external MCP server connections for each service
            if "lambda" in service_types:
                mcp_servers["lambda"] = {
                    "package": "awslabs.lambda-tool-mcp-server",
                    "port": 8766
                }
            if "sns" in service_types or "sqs" in service_types:
                mcp_servers["messaging"] = {
                    "package": "aws.messaging-mcp-server",
                    "port": 8767
                }
            if "mq" in service_types:
                mcp_servers["mq"] = {
                    "package": "amazon.mq-mcp-server",
                    "port": 8768
                }
        
        self.logger.info(f"Initializing AWS MCP client with external servers: {use_external_mcp_servers}")
        if use_external_mcp_servers and mcp_servers:
            self.logger.info(f"External MCP server configuration: {list(mcp_servers.keys())}")
            
            # Check if packages need to be installed first
            if install_packages:
                import importlib
                import subprocess
                import sys
                
                for service_type, config in mcp_servers.items():
                    package = config.get("package")
                    if not package:
                        continue
                        
                    try:
                        # Check if package is already installed
                        importlib.import_module(package.split(".")[0])
                        self.logger.debug(f"Package {package} is already installed")
                    except ImportError:
                        # Install the package
                        self.logger.info(f"Installing {package} package...")
                        try:
                            subprocess.check_call([
                                sys.executable, "-m", "pip", "install", package, "--quiet"
                            ])
                            self.logger.info(f"Successfully installed {package}")
                        except subprocess.CalledProcessError as e:
                            self.logger.error(f"Failed to install {package}: {str(e)}")
        
        client = OptimizedAWSMCPClient(
            connection_uri=connection_uri,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            use_direct_sdk=use_direct_sdk,
            use_external_mcp_servers=use_external_mcp_servers,
            mcp_servers=mcp_servers,
            timeout=timeout,
            max_retries=max_retries
        )
        
        try:
            self.logger.info(f"Connecting AWS MCP client {server_id}...")
            success = await client.connect()
            
            if success:
                self.clients[server_id] = client
                self.logger.info(f"AWS MCP client {server_id} added successfully")
                
                # Initialize specific services if required
                for service_type in service_types:
                    self.logger.info(f"Initializing {service_type} service for {server_id}...")
                    if service_type == "lambda":
                        await client.init_lambda_service()
                    elif service_type == "sns":
                        await client.init_sns_service()
                    elif service_type == "sqs":
                        await client.init_sqs_service()
                    elif service_type == "mq":
                        await client.init_mq_service()
                
                # Get info about connected external MCP servers
                external_servers = getattr(client, "external_servers", {})
                if external_servers:
                    self.logger.info(f"Connected to external AWS MCP servers: {list(external_servers.keys())}")
                
                return True
            else:
                self.logger.error(f"Failed to connect AWS MCP client {server_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error adding AWS MCP client {server_id}: {str(e)}")
            return False
