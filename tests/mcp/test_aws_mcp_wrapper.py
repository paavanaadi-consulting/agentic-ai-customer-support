"""
Comprehensive test suite for aws_mcp_wrapper.py
Tests the AWS MCP wrapper that provides a unified interface for external AWS MCP servers
"""
import pytest
import asyncio
import logging
import os
from unittest.mock import AsyncMock, MagicMock, patch, call
from typing import Dict, Any

from src.mcp.aws_mcp_wrapper import AWSMCPWrapper, ExternalMCPConfig


class TestExternalMCPConfig:
    """Test the ExternalMCPConfig dataclass"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = ExternalMCPConfig()
        
        assert config.lambda_tool_enabled is True
        assert config.core_enabled is True
        assert config.documentation_enabled is True
        assert config.aws_profile == "default"
        assert config.aws_region == "us-east-1"
        assert config.use_uvx is True
        assert config.fallback_to_custom is True
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = ExternalMCPConfig(
            lambda_tool_enabled=False,
            core_enabled=False,
            documentation_enabled=False,
            aws_profile="prod",
            aws_region="us-west-2",
            use_uvx=False,
            fallback_to_custom=False
        )
        
        assert config.lambda_tool_enabled is False
        assert config.core_enabled is False
        assert config.documentation_enabled is False
        assert config.aws_profile == "prod"
        assert config.aws_region == "us-west-2"
        assert config.use_uvx is False
        assert config.fallback_to_custom is False


class TestAWSMCPWrapper:
    """Test the AWSMCPWrapper class"""
    
    @pytest.fixture
    def config(self):
        """Fixture for test configuration"""
        return ExternalMCPConfig(
            aws_profile="test",
            aws_region="us-east-1"
        )
    
    @pytest.fixture
    def wrapper(self, config):
        """Fixture for AWS MCP wrapper instance"""
        return AWSMCPWrapper(config)
    
    def test_initialization_with_default_config(self):
        """Test wrapper initialization with default config"""
        wrapper = AWSMCPWrapper()
        
        assert wrapper.config is not None
        assert wrapper.config.aws_profile == "default"
        assert wrapper.logger is not None
        assert wrapper.external_servers == {}
        assert wrapper.custom_server is None
        assert wrapper.running is False
    
    def test_initialization_with_custom_config(self, config):
        """Test wrapper initialization with custom config"""
        wrapper = AWSMCPWrapper(config)
        
        assert wrapper.config == config
        assert wrapper.config.aws_profile == "test"
        assert wrapper.running is False
    
    def test_server_configurations(self, wrapper):
        """Test server configurations are properly set"""
        configs = wrapper.server_configs
        
        # Check lambda-tool server config
        lambda_config = configs["lambda-tool"]
        assert lambda_config["package"] == "awslabs.lambda-tool-mcp-server"
        assert lambda_config["enabled"] is True
        assert "lambda_invoke" in lambda_config["tools"]
        assert lambda_config["env"]["AWS_PROFILE"] == "test"
        
        # Check core server config
        core_config = configs["core"]
        assert core_config["package"] == "awslabs.core-mcp-server"
        assert core_config["enabled"] is True
        assert "s3_operations" in core_config["tools"]
        
        # Check documentation server config
        doc_config = configs["documentation"]
        assert doc_config["package"] == "awslabs.aws-documentation-mcp-server"
        assert doc_config["enabled"] is True
        assert "search_aws_docs" in doc_config["tools"]
    
    def test_tool_server_mapping(self, wrapper):
        """Test tool to server mapping"""
        assert "lambda_invoke" in wrapper.tool_server_map
        assert "s3_operations" in wrapper.tool_server_map
        assert "search_aws_docs" in wrapper.tool_server_map
        assert wrapper.tool_server_map["lambda_invoke"] == "lambda-tool"
        assert wrapper.tool_server_map["s3_operations"] == "core"
    
    def test_legacy_tool_mapping(self, wrapper):
        """Test legacy tool name mapping"""
        legacy_map = wrapper.legacy_tool_map
        
        assert legacy_map["s3_upload_file"] == "s3_operations"
        assert legacy_map["s3_download_file"] == "s3_operations"
        assert legacy_map["lambda_invoke"] == "lambda_invoke"
        assert legacy_map["get_parameter_store_value"] == "get_parameter_store_value"
    
    def test_disabled_servers_not_in_mapping(self):
        """Test that disabled servers are not included in tool mapping"""
        config = ExternalMCPConfig(lambda_tool_enabled=False)
        wrapper = AWSMCPWrapper(config)
        
        assert "lambda_invoke" not in wrapper.tool_server_map
        assert "s3_operations" in wrapper.tool_server_map  # core still enabled


class TestAWSMCPWrapperInitialization:
    """Test AWS MCP wrapper initialization process"""
    
    @pytest.fixture
    def wrapper(self):
        """Fixture for wrapper instance"""
        return AWSMCPWrapper()
    
    @pytest.mark.asyncio
    async def test_initialize_with_external_packages(self, wrapper):
        """Test initialization when external packages are available"""
        with patch.object(wrapper, '_check_external_packages', return_value=True) as mock_check:
            with patch.object(wrapper, '_initialize_external_servers') as mock_init_external:
                await wrapper.initialize()
                
                mock_check.assert_called_once()
                mock_init_external.assert_called_once()
                assert wrapper.running is True
    
    @pytest.mark.asyncio
    async def test_initialize_fallback_to_custom(self, wrapper):
        """Test initialization with fallback to custom server"""
        with patch.object(wrapper, '_check_external_packages', return_value=False):
            with patch.object(wrapper, '_initialize_custom_server') as mock_init_custom:
                await wrapper.initialize()
                
                mock_init_custom.assert_called_once()
                assert wrapper.running is True
    
    @pytest.mark.asyncio
    async def test_initialize_no_fallback_raises_error(self):
        """Test initialization without fallback raises error"""
        config = ExternalMCPConfig(fallback_to_custom=False)
        wrapper = AWSMCPWrapper(config)
        
        with patch.object(wrapper, '_check_external_packages', return_value=False):
            with pytest.raises(RuntimeError, match="External AWS MCP packages not available"):
                await wrapper.initialize()
    
    @pytest.mark.asyncio
    async def test_initialize_exception_handling(self, wrapper):
        """Test initialization exception handling"""
        with patch.object(wrapper, '_check_external_packages', side_effect=Exception("Test error")):
            with pytest.raises(Exception, match="Test error"):
                await wrapper.initialize()


class TestExternalPackageChecking:
    """Test external package availability checking"""
    
    @pytest.fixture
    def wrapper(self):
        """Fixture for wrapper with uvx enabled"""
        config = ExternalMCPConfig(use_uvx=True)
        return AWSMCPWrapper(config)
    
    @pytest.fixture
    def wrapper_no_uvx(self):
        """Fixture for wrapper without uvx"""
        config = ExternalMCPConfig(use_uvx=False)
        return AWSMCPWrapper(config)
    
    @pytest.mark.asyncio
    async def test_check_external_packages_uvx_available(self, wrapper):
        """Test checking external packages when uvx is available"""
        # Mock uvx --version command success
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.wait = AsyncMock(return_value=None)
        
        # Mock package check success
        mock_package_process = AsyncMock()
        mock_package_process.returncode = 0
        mock_package_process.wait = AsyncMock(return_value=None)
        
        with patch('asyncio.create_subprocess_exec', side_effect=[mock_process, mock_package_process]):
            result = await wrapper._check_external_packages()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_external_packages_uvx_not_available(self, wrapper):
        """Test checking external packages when uvx is not available"""
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.wait = AsyncMock(return_value=None)
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            result = await wrapper._check_external_packages()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_external_packages_no_packages_found(self, wrapper):
        """Test checking when no external packages are found"""
        # Mock uvx --version success but package check fails
        mock_uvx_process = AsyncMock()
        mock_uvx_process.returncode = 0
        mock_uvx_process.wait = AsyncMock(return_value=None)
        
        mock_package_process = AsyncMock()
        mock_package_process.returncode = 1
        mock_package_process.wait = AsyncMock(return_value=None)
        
        with patch('asyncio.create_subprocess_exec', side_effect=[mock_uvx_process, mock_package_process, mock_package_process, mock_package_process]):
            result = await wrapper._check_external_packages()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_external_packages_without_uvx(self, wrapper_no_uvx):
        """Test checking external packages without uvx (import method)"""
        # Mock successful import
        with patch('importlib.import_module') as mock_import:
            result = await wrapper_no_uvx._check_external_packages()
            assert result is True
            mock_import.assert_called()
    
    @pytest.mark.asyncio
    async def test_check_external_packages_import_error(self, wrapper_no_uvx):
        """Test checking external packages with import errors"""
        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            result = await wrapper_no_uvx._check_external_packages()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_external_packages_exception(self, wrapper):
        """Test checking external packages with exception"""
        with patch('asyncio.create_subprocess_exec', side_effect=Exception("Subprocess error")):
            result = await wrapper._check_external_packages()
            assert result is False


class TestExternalServerInitialization:
    """Test external server initialization"""
    
    @pytest.fixture
    def wrapper(self):
        """Fixture for wrapper instance"""
        return AWSMCPWrapper()
    
    @pytest.mark.asyncio
    async def test_initialize_external_servers_success(self, wrapper):
        """Test successful external server initialization"""
        await wrapper._initialize_external_servers()
        
        # Check that all enabled servers are initialized
        assert "lambda-tool" in wrapper.external_servers
        assert "core" in wrapper.external_servers
        assert "documentation" in wrapper.external_servers
        
        # Check server availability
        for server_name in wrapper.external_servers:
            server_info = wrapper.external_servers[server_name]
            assert server_info["available"] is True
            assert "config" in server_info
    
    @pytest.mark.asyncio
    async def test_initialize_external_servers_with_disabled_server(self):
        """Test initialization with some servers disabled"""
        config = ExternalMCPConfig(lambda_tool_enabled=False)
        wrapper = AWSMCPWrapper(config)
        
        await wrapper._initialize_external_servers()
        
        # Only core and documentation should be initialized
        assert "core" in wrapper.external_servers
        assert "documentation" in wrapper.external_servers
        assert len(wrapper.external_servers) == 2


class TestCustomServerInitialization:
    """Test custom server initialization (fallback)"""
    
    @pytest.fixture
    def wrapper(self):
        """Fixture for wrapper instance"""
        return AWSMCPWrapper()
    
    @pytest.mark.asyncio
    async def test_initialize_custom_server_raises_error(self, wrapper):
        """Test that custom server initialization raises error (feature removed)"""
        with pytest.raises(RuntimeError, match="Custom AWS MCP server fallback removed"):
            await wrapper._initialize_custom_server()


class TestToolCalling:
    """Test tool calling functionality"""
    
    @pytest.fixture
    def wrapper(self):
        """Fixture for initialized wrapper"""
        wrapper = AWSMCPWrapper()
        # Mock initialized external servers
        wrapper.external_servers = {
            "lambda-tool": {"available": True, "config": wrapper.server_configs["lambda-tool"]},
            "core": {"available": True, "config": wrapper.server_configs["core"]}
        }
        return wrapper
    
    @pytest.mark.asyncio
    async def test_call_tool_external_server(self, wrapper):
        """Test calling tool using external server"""
        with patch.object(wrapper, '_call_external_tool', return_value={"success": True, "result": "test"}) as mock_call:
            result = await wrapper.call_tool("lambda_invoke", {"function_name": "test"})
            
            mock_call.assert_called_once_with("lambda-tool", "lambda_invoke", {"function_name": "test"})
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_call_tool_legacy_mapping(self, wrapper):
        """Test calling tool with legacy name mapping"""
        with patch.object(wrapper, '_call_external_tool', return_value={"success": True}) as mock_call:
            await wrapper.call_tool("s3_upload_file", {"bucket": "test"})
            
            mock_call.assert_called_once_with("core", "s3_operations", {"bucket": "test"})
    
    @pytest.mark.asyncio
    async def test_call_tool_fallback_to_custom(self, wrapper):
        """Test calling tool with fallback to custom server"""
        # Remove external server availability
        wrapper.external_servers["lambda-tool"]["available"] = False
        
        # Mock custom server
        mock_custom_server = AsyncMock()
        mock_custom_server.call_tool.return_value = {"success": True, "custom": True}
        wrapper.custom_server = mock_custom_server
        
        result = await wrapper.call_tool("lambda_invoke", {"function_name": "test"})
        
        mock_custom_server.call_tool.assert_called_once_with("lambda_invoke", {"function_name": "test"})
        assert result["custom"] is True
    
    @pytest.mark.asyncio
    async def test_call_tool_not_available(self, wrapper):
        """Test calling tool that's not available"""
        result = await wrapper.call_tool("unknown_tool", {})
        
        assert result["success"] is False
        assert "not available" in result["error"]
    
    @pytest.mark.asyncio
    async def test_call_tool_exception(self, wrapper):
        """Test tool calling with exception"""
        with patch.object(wrapper, '_call_external_tool', side_effect=Exception("Tool error")):
            result = await wrapper.call_tool("lambda_invoke", {})
            
            assert result["success"] is False
            assert "Tool error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_call_external_tool_success(self, wrapper):
        """Test external tool calling success"""
        result = await wrapper._call_external_tool("lambda-tool", "lambda_invoke", {"function_name": "test"})
        
        assert result["success"] is True
        assert result["tool"] == "lambda_invoke"
        assert result["server"] == "lambda-tool"
        assert result["arguments"]["function_name"] == "test"
    
    @pytest.mark.asyncio
    async def test_call_external_tool_exception(self, wrapper):
        """Test external tool calling with exception"""
        # Make server config invalid to trigger exception
        wrapper.external_servers["lambda-tool"]["config"]["command"] = None
        
        result = await wrapper._call_external_tool("lambda-tool", "lambda_invoke", {})
        
        assert result["success"] is False
        assert "error" in result


class TestResourceHandling:
    """Test resource handling functionality"""
    
    @pytest.fixture
    def wrapper(self):
        """Fixture for wrapper instance"""
        return AWSMCPWrapper()
    
    @pytest.mark.asyncio
    async def test_get_resource_with_custom_server(self, wrapper):
        """Test getting resource using custom server"""
        mock_custom_server = AsyncMock()
        mock_custom_server.get_resource.return_value = {"success": True, "data": "test"}
        wrapper.custom_server = mock_custom_server
        
        result = await wrapper.get_resource("test://resource")
        
        mock_custom_server.get_resource.assert_called_once_with("test://resource")
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_get_resource_not_available(self, wrapper):
        """Test getting resource when not available"""
        result = await wrapper.get_resource("test://resource")
        
        assert result["success"] is False
        assert "not available" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_resource_exception(self, wrapper):
        """Test getting resource with exception"""
        mock_custom_server = AsyncMock()
        mock_custom_server.get_resource.side_effect = Exception("Resource error")
        wrapper.custom_server = mock_custom_server
        
        result = await wrapper.get_resource("test://resource")
        
        assert result["success"] is False
        assert "Resource error" in result["error"]


class TestWrapperManagement:
    """Test wrapper lifecycle management"""
    
    @pytest.fixture
    def wrapper(self):
        """Fixture for wrapper instance"""
        wrapper = AWSMCPWrapper()
        wrapper.running = True
        return wrapper
    
    @pytest.mark.asyncio
    async def test_stop_wrapper(self, wrapper):
        """Test stopping the wrapper"""
        mock_custom_server = AsyncMock()
        wrapper.custom_server = mock_custom_server
        
        await wrapper.stop()
        
        mock_custom_server.stop.assert_called_once()
        assert wrapper.running is False
    
    @pytest.mark.asyncio
    async def test_stop_wrapper_exception(self, wrapper):
        """Test stopping wrapper with exception"""
        mock_custom_server = AsyncMock()
        mock_custom_server.stop.side_effect = Exception("Stop error")
        wrapper.custom_server = mock_custom_server
        
        # Should not raise exception
        await wrapper.stop()
        assert wrapper.running is False
    
    def test_get_available_tools(self, wrapper):
        """Test getting available tools"""
        # Mock external servers
        wrapper.external_servers = {
            "lambda-tool": {
                "available": True,
                "config": {"tools": ["lambda_invoke", "list_lambda_functions"]}
            },
            "core": {
                "available": False,
                "config": {"tools": ["s3_operations"]}
            }
        }
        
        # Mock custom server
        mock_custom_server = MagicMock()
        mock_custom_server.tools = ["custom_tool"]
        wrapper.custom_server = mock_custom_server
        
        tools = wrapper.get_available_tools()
        
        # Should include tools from available external servers and custom server
        assert "lambda_invoke" in tools
        assert "list_lambda_functions" in tools
        assert "custom_tool" in tools
        assert "s3_operations" not in tools  # server not available
    
    def test_get_available_tools_no_servers(self):
        """Test getting available tools with no servers"""
        wrapper = AWSMCPWrapper()
        tools = wrapper.get_available_tools()
        assert tools == []
    
    def test_get_status(self, wrapper):
        """Test getting wrapper status"""
        # Mock external servers
        wrapper.external_servers = {
            "lambda-tool": {"available": True},
            "core": {"available": False}
        }
        wrapper.custom_server = MagicMock()
        
        status = wrapper.get_status()
        
        assert status["running"] is True
        assert status["external_servers"]["lambda-tool"] is True
        assert status["external_servers"]["core"] is False
        assert status["custom_server"] is True
        assert "config" in status
        assert status["config"]["aws_profile"] == "default"
    
    @pytest.mark.asyncio
    async def test_start_as_server(self, wrapper):
        """Test starting wrapper as standalone server"""
        with patch.object(wrapper, 'initialize') as mock_init:
            with patch('asyncio.sleep', side_effect=KeyboardInterrupt):
                with patch.object(wrapper, 'stop') as mock_stop:
                    await wrapper.start_as_server()
                    
                    mock_init.assert_called_once()
                    mock_stop.assert_called_once()


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases"""
    
    @pytest.mark.asyncio
    async def test_full_initialization_flow_external(self):
        """Test full initialization flow with external packages"""
        wrapper = AWSMCPWrapper()
        
        # Mock external package availability
        with patch.object(wrapper, '_check_external_packages', return_value=True):
            await wrapper.initialize()
            
            assert wrapper.running is True
            assert len(wrapper.external_servers) == 3  # lambda-tool, core, documentation
            
            # Test tool calling
            result = await wrapper.call_tool("lambda_invoke", {"function_name": "test"})
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_partial_server_availability(self):
        """Test handling partial server availability"""
        config = ExternalMCPConfig(
            lambda_tool_enabled=True,
            core_enabled=False,
            documentation_enabled=True
        )
        wrapper = AWSMCPWrapper(config)
        
        await wrapper._initialize_external_servers()
        
        # Only enabled servers should be available
        assert "lambda-tool" in wrapper.external_servers
        assert "documentation" in wrapper.external_servers
        assert "core" not in wrapper.external_servers
        
        # Tool mapping should only include enabled servers
        assert "lambda_invoke" in wrapper.tool_server_map
        assert "search_aws_docs" in wrapper.tool_server_map
        assert "s3_operations" not in wrapper.tool_server_map
    
    @pytest.mark.asyncio
    async def test_environment_variable_handling(self):
        """Test environment variable handling in server configs"""
        config = ExternalMCPConfig(
            aws_profile="production",
            aws_region="eu-west-1"
        )
        wrapper = AWSMCPWrapper(config)
        
        lambda_config = wrapper.server_configs["lambda-tool"]
        assert lambda_config["env"]["AWS_PROFILE"] == "production"
        assert lambda_config["env"]["AWS_REGION"] == "eu-west-1"
        assert lambda_config["env"]["FASTMCP_LOG_LEVEL"] == "ERROR"
    
    def test_logging_configuration(self):
        """Test logging is properly configured"""
        wrapper = AWSMCPWrapper()
        
        assert wrapper.logger is not None
        assert wrapper.logger.name == "src.mcp.aws_mcp_wrapper"
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, wrapper):
        """Test concurrent tool calling"""
        wrapper.external_servers = {
            "lambda-tool": {"available": True, "config": wrapper.server_configs["lambda-tool"]},
            "core": {"available": True, "config": wrapper.server_configs["core"]}
        }
        
        async def call_tool(tool_name, args):
            return await wrapper.call_tool(tool_name, args)
        
        # Call multiple tools concurrently
        tasks = [
            call_tool("lambda_invoke", {"function_name": "test1"}),
            call_tool("s3_operations", {"bucket": "test2"}),
            call_tool("lambda_invoke", {"function_name": "test3"})
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All calls should succeed
        assert all(result["success"] for result in results)
        assert len(results) == 3


if __name__ == "__main__":
    pytest.main([__file__])
