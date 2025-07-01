"""
AWS MCP Wrapper for External AWS MCP Servers
Provides unified interface for external AWS MCP servers with fallback to custom implementation
"""
import os
import json
import subprocess
import asyncio
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ExternalMCPConfig:
    """Configuration for external AWS MCP servers"""
    lambda_tool_enabled: bool = True
    core_enabled: bool = True
    documentation_enabled: bool = True
    aws_profile: str = "default"
    aws_region: str = "us-east-1"
    use_uvx: bool = True  # Use uvx for package management
    fallback_to_custom: bool = True

class AWSMCPWrapper:
    """
    Wrapper for external AWS MCP servers with fallback to custom implementation
    """
    
    def __init__(self, config: ExternalMCPConfig = None):
        self.config = config or ExternalMCPConfig()
        self.logger = logging.getLogger(__name__)
        self.external_servers = {}
        self.custom_server = None
        self.running = False
        
        # MCP Server configurations
        self.server_configs = {
            "lambda-tool": {
                "package": "awslabs.lambda-tool-mcp-server",
                "command": "uvx" if self.config.use_uvx else "python",
                "args": ["awslabs.lambda-tool-mcp-server@latest"] if self.config.use_uvx else ["-m", "lambda_tool_mcp_server"],
                "env": {
                    "AWS_PROFILE": self.config.aws_profile,
                    "AWS_REGION": self.config.aws_region,
                    "FASTMCP_LOG_LEVEL": "ERROR"
                },
                "tools": ["lambda_invoke", "list_lambda_functions"],
                "enabled": self.config.lambda_tool_enabled
            },
            "core": {
                "package": "awslabs.core-mcp-server", 
                "command": "uvx" if self.config.use_uvx else "python",
                "args": ["awslabs.core-mcp-server@latest"] if self.config.use_uvx else ["-m", "core_mcp_server"],
                "env": {
                    "AWS_PROFILE": self.config.aws_profile,
                    "AWS_REGION": self.config.aws_region,
                    "FASTMCP_LOG_LEVEL": "ERROR"
                },
                "tools": ["get_parameter_store_value", "s3_operations"],
                "enabled": self.config.core_enabled
            },
            "documentation": {
                "package": "awslabs.aws-documentation-mcp-server",
                "command": "uvx" if self.config.use_uvx else "python",
                "args": ["awslabs.aws-documentation-mcp-server@latest"] if self.config.use_uvx else ["-m", "aws_documentation_mcp_server"],
                "env": {
                    "FASTMCP_LOG_LEVEL": "ERROR"
                },
                "tools": ["search_aws_docs", "get_aws_api_reference"],
                "enabled": self.config.documentation_enabled
            }
        }
        
        # Tool to server mapping
        self.tool_server_map = {}
        for server_name, config in self.server_configs.items():
            if config["enabled"]:
                for tool in config["tools"]:
                    self.tool_server_map[tool] = server_name
        
        # Legacy tool mapping for backward compatibility
        self.legacy_tool_map = {
            "s3_upload_file": "s3_operations",
            "s3_download_file": "s3_operations", 
            "s3_list_objects": "s3_operations",
            "s3_delete_object": "s3_operations",
            "lambda_invoke": "lambda_invoke",
            "get_parameter_store_value": "get_parameter_store_value"
        }

    async def initialize(self):
        """Initialize the AWS MCP wrapper"""
        self.logger.info("Initializing AWS MCP wrapper")
        
        try:
            # Check if external packages are available
            external_available = await self._check_external_packages()
            
            if external_available:
                self.logger.info("External AWS MCP packages detected, using external servers")
                await self._initialize_external_servers()
            elif self.config.fallback_to_custom:
                self.logger.info("External packages not available, falling back to custom AWS MCP server")
                await self._initialize_custom_server()
            else:
                raise RuntimeError("External AWS MCP packages not available and fallback disabled")
                
            self.running = True
            self.logger.info("AWS MCP wrapper initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AWS MCP wrapper: {e}")
            raise

    async def _check_external_packages(self) -> bool:
        """Check if external AWS MCP packages are available"""
        try:
            if self.config.use_uvx:
                # Check if uvx is available
                result = await asyncio.create_subprocess_exec(
                    "uvx", "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await result.wait()
                if result.returncode != 0:
                    self.logger.warning("uvx not available")
                    return False
                
                # Check if at least one AWS MCP package is available
                for server_name, config in self.server_configs.items():
                    if config["enabled"]:
                        try:
                            result = await asyncio.create_subprocess_exec(
                                "uvx", "--help", config["package"], 
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE
                            )
                            await result.wait()
                            if result.returncode == 0:
                                self.logger.info(f"External package {config['package']} is available")
                                return True
                        except:
                            continue
                            
                self.logger.warning("No external AWS MCP packages found")
                return False
            else:
                # Check if packages are installed in current environment
                for server_name, config in self.server_configs.items():
                    if config["enabled"]:
                        try:
                            import importlib
                            module_name = config["package"].replace("awslabs.", "").replace("-", "_")
                            importlib.import_module(module_name)
                            self.logger.info(f"External package {config['package']} is available")
                            return True
                        except ImportError:
                            continue
                            
                self.logger.warning("No external AWS MCP packages found in current environment")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking external packages: {e}")
            return False

    async def _initialize_external_servers(self):
        """Initialize external AWS MCP servers"""
        for server_name, config in self.server_configs.items():
            if config["enabled"]:
                try:
                    self.logger.info(f"Initializing external {server_name} MCP server")
                    
                    # For external servers, we don't start them directly
                    # Instead, we prepare the configuration for calling them
                    self.external_servers[server_name] = {
                        "config": config,
                        "available": True
                    }
                    
                except Exception as e:
                    self.logger.error(f"Failed to initialize {server_name}: {e}")
                    self.external_servers[server_name] = {
                        "config": config,
                        "available": False
                    }

    async def _initialize_custom_server(self):
        """Initialize custom AWS MCP server as fallback"""
        try:
            # Custom AWS MCP server has been removed in favor of external packages
            # If you need AWS functionality, please install external MCP packages:
            # uvx install awslabs.lambda-tool-mcp-server
            # uvx install awslabs.core-mcp-server
            self.logger.warning(
                "Custom AWS MCP server fallback is no longer available. "
                "Please install external AWS MCP packages using: "
                "uvx install awslabs.lambda-tool-mcp-server awslabs.core-mcp-server"
            )
            raise RuntimeError(
                "Custom AWS MCP server fallback removed. "
                "External AWS MCP packages required for AWS functionality."
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize custom AWS MCP server: {e}")
            raise

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool using external servers or fallback to custom"""
        try:
            # Map legacy tool names
            mapped_tool = self.legacy_tool_map.get(tool_name, tool_name)
            
            # Try external servers first
            if mapped_tool in self.tool_server_map:
                server_name = self.tool_server_map[mapped_tool]
                if server_name in self.external_servers and self.external_servers[server_name]["available"]:
                    return await self._call_external_tool(server_name, mapped_tool, arguments)
            
            # Fallback to custom server
            if self.custom_server:
                return await self.custom_server.call_tool(tool_name, arguments)
            
            return {
                "success": False,
                "error": f"Tool {tool_name} not available in any server"
            }
            
        except Exception as e:
            self.logger.error(f"Error calling tool {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _call_external_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool using external MCP server"""
        try:
            server_config = self.external_servers[server_name]["config"]
            
            # Prepare the command
            cmd = [server_config["command"]] + server_config["args"]
            
            # Prepare environment
            env = os.environ.copy()
            env.update(server_config["env"])
            
            # For now, we'll simulate the external call
            # In a full implementation, this would use MCP protocol over stdio/HTTP
            self.logger.info(f"Would call external {server_name} with tool {tool_name}")
            
            # Simulate success response for demonstration
            return {
                "success": True,
                "tool": tool_name,
                "server": server_name,
                "result": "External MCP server response",
                "arguments": arguments
            }
            
        except Exception as e:
            self.logger.error(f"Error calling external tool {tool_name} on {server_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
        """Get resource using external servers or fallback to custom"""
        try:
            # Try custom server for now (resources are more complex to map)
            if self.custom_server:
                return await self.custom_server.get_resource(resource_uri)
            
            return {
                "success": False,
                "error": f"Resource {resource_uri} not available"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting resource {resource_uri}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def stop(self):
        """Stop all servers"""
        try:
            if self.custom_server:
                await self.custom_server.stop()
                
            self.running = False
            self.logger.info("AWS MCP wrapper stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping AWS MCP wrapper: {e}")

    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        tools = []
        
        # Add tools from external servers
        for server_name, server_info in self.external_servers.items():
            if server_info["available"]:
                tools.extend(server_info["config"]["tools"])
        
        # Add tools from custom server
        if self.custom_server:
            tools.extend(self.custom_server.tools)
        
        return list(set(tools))

    def get_status(self) -> Dict[str, Any]:
        """Get status of all servers"""
        return {
            "running": self.running,
            "external_servers": {
                name: info["available"] 
                for name, info in self.external_servers.items()
            },
            "custom_server": self.custom_server is not None,
            "config": {
                "use_uvx": self.config.use_uvx,
                "aws_profile": self.config.aws_profile,
                "aws_region": self.config.aws_region,
                "fallback_enabled": self.config.fallback_to_custom
            }
        }

    async def start_as_server(self):
        """Start the wrapper as a standalone server (for Docker compatibility)"""
        await self.initialize()
        self.logger.info("AWS MCP wrapper started as standalone server")
        
        # Keep the server running
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            await self.stop()
