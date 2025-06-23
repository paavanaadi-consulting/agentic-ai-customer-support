"""
Comprehensive unit tests for AWS MCP Server
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import boto3
from moto import mock_s3, mock_lambda, mock_ssm
from mcp.aws_mcp_server import AWSMCPServer

class TestAWSMCPServer:
    """Test suite for AWS MCP Server"""
    
    @pytest.fixture
    def aws_mcp_server(self):
        return AWSMCPServer(
            aws_access_key_id='test_key',
            aws_secret_access_key='test_secret',
            region_name='us-east-1'
        )
    
    @pytest.mark.asyncio
    async def test_initialization(self, aws_mcp_server):
        """Test server initialization"""
        assert aws_mcp_server.server_id == "mcp_aws"
        assert aws_mcp_server.name == "AWS MCP Server"
        assert 's3_upload_file' in aws_mcp_server.tools
        assert 'lambda_invoke' in aws_mcp_server.tools
        assert 'aws://s3/buckets' in aws_mcp_server.resources
    
    @pytest.mark.asyncio
    @mock_s3
    @mock_lambda
    @mock_ssm
    async def test_start_server(self, aws_mcp_server):
        """Test server startup"""
        await aws_mcp_server.start()
        
        assert aws_mcp_server.running is True
        assert aws_mcp_server.s3_client is not None
        assert aws_mcp_server.lambda_client is not None
        assert aws_mcp_server.ssm_client is not None
    
    @pytest.mark.asyncio
    @mock_s3
    async def test_s3_upload_file_tool(self, aws_mcp_server):
        """Test s3_upload_file tool"""
        # Setup S3 bucket
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        await aws_mcp_server.start()
        
        result = await aws_mcp_server.call_tool('s3_upload_file', {
            'bucket': 'test-bucket',
            'key': 'test-file.txt',
            'content': 'Hello World',
            'content_type': 'text/plain'
        })
        
        assert result['success'] is True
        assert result['bucket'] == 'test-bucket'
        assert result['key'] == 'test-file.txt'
        assert 'etag' in result
    
    @pytest.mark.asyncio
    @mock_s3
    async def test_s3_download_file_tool(self, aws_mcp_server):
        """Test s3_download_file tool"""
        # Setup S3 bucket and object
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        s3_client.put_object(Bucket='test-bucket', Key='test-file.txt', Body='Hello World')
        
        await aws_mcp_server.start()
        
        result = await aws_mcp_server.call_tool('s3_download_file', {
            'bucket': 'test-bucket',
            'key': 'test-file.txt'
        })
        
        assert result['success'] is True
        assert result['content'] == 'Hello World'
        assert result['bucket'] == 'test-bucket'
        assert result['key'] == 'test-file.txt'
    
    @pytest.mark.asyncio
    @mock_s3
    async def test_s3_list_objects_tool(self, aws_mcp_server):
        """Test s3_list_objects tool"""
        # Setup S3 bucket and objects
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        s3_client.put_object(Bucket='test-bucket', Key='file1.txt', Body='Content 1')
        s3_client.put_object(Bucket='test-bucket', Key='file2.txt', Body='Content 2')
        
        await aws_mcp_server.start()
        
        result = await aws_mcp_server.call_tool('s3_list_objects', {
            'bucket': 'test-bucket',
            'prefix': '',
            'max_keys': 10
        })
        
        assert result['success'] is True
        assert result['bucket'] == 'test-bucket'
        assert len(result['objects']) == 2
        assert any(obj['key'] == 'file1.txt' for obj in result['objects'])
        assert any(obj['key'] == 'file2.txt' for obj in result['objects'])
    
    @pytest.mark.asyncio
    @mock_s3
    async def test_s3_delete_object_tool(self, aws_mcp_server):
        """Test s3_delete_object tool"""
        # Setup S3 bucket and object
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        s3_client.put_object(Bucket='test-bucket', Key='test-file.txt', Body='Hello World')
        
        await aws_mcp_server.start()
        
        result = await aws_mcp_server.call_tool('s3_delete_object', {
            'bucket': 'test-bucket',
            'key': 'test-file.txt'
        })
        
        assert result['success'] is True
        assert result['bucket'] == 'test-bucket'
        assert result['key'] == 'test-file.txt'
    
    @pytest.mark.asyncio
    @mock_lambda
    async def test_lambda_invoke_tool(self, aws_mcp_server):
        """Test lambda_invoke tool"""
        # Setup Lambda function
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Create a mock function
        function_name = 'test-function'
        lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.8',
            Role='arn:aws:iam::123456789012:role/test-role',
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': b'fake code'},
        )
        
        await aws_mcp_server.start()
        
        result = await aws_mcp_server.call_tool('lambda_invoke', {
            'function_name': function_name,
            'payload': {'key': 'value'},
            'invocation_type': 'RequestResponse'
        })
        
        assert result['success'] is True
        assert result['function_name'] == function_name
        assert 'status_code' in result
    
    @pytest.mark.asyncio
    @mock_ssm
    async def test_get_parameter_store_value_tool(self, aws_mcp_server):
        """Test get_parameter_store_value tool"""
        # Setup SSM parameter
        ssm_client = boto3.client('ssm', region_name='us-east-1')
        ssm_client.put_parameter(
            Name='test-parameter',
            Value='test-value',
            Type='String'
        )
        
        await aws_mcp_server.start()
        
        result = await aws_mcp_server.call_tool('get_parameter_store_value', {
            'parameter_name': 'test-parameter',
            'with_decryption': True
        })
        
        assert result['success'] is True
        assert result['name'] == 'test-parameter'
        assert result['value'] == 'test-value'
        assert result['type'] == 'String'
    
    @pytest.mark.asyncio
    async def test_unknown_tool(self, aws_mcp_server):
        """Test handling of unknown tools"""
        result = await aws_mcp_server.call_tool('unknown_tool', {})
        
        assert result['success'] is False
        assert 'Unknown tool' in result['error']
    
    @pytest.mark.asyncio
    @mock_s3
    async def test_aws_error_handling(self, aws_mcp_server):
        """Test AWS error handling"""
        await aws_mcp_server.start()
        
        # Try to access non-existent bucket
        result = await aws_mcp_server.call_tool('s3_upload_file', {
            'bucket': 'non-existent-bucket',
            'key': 'test-file.txt',
            'content': 'Hello World'
        })
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    @mock_s3
    async def test_get_resource_s3_buckets(self, aws_mcp_server):
        """Test getting S3 buckets resource"""
        # Setup S3 buckets
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='bucket1')
        s3_client.create_bucket(Bucket='bucket2')
        
        await aws_mcp_server.start()
        
        result = await aws_mcp_server.get_resource('aws://s3/buckets')
        
        assert result['success'] is True
        assert len(result['contents']) == 1
        assert result['contents'][0]['mimeType'] == 'application/json'
    
    @pytest.mark.asyncio
    @mock_lambda
    async def test_get_resource_lambda_functions(self, aws_mcp_server):
        """Test getting Lambda functions resource"""
        # Setup Lambda function
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        lambda_client.create_function(
            FunctionName='test-function',
            Runtime='python3.8',
            Role='arn:aws:iam::123456789012:role/test-role',
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': b'fake code'},
        )
        
        await aws_mcp_server.start()
        
        result = await aws_mcp_server.get_resource('aws://lambda/functions')
        
        assert result['success'] is True
        assert len(result['contents']) == 1
        assert result['contents'][0]['mimeType'] == 'application/json'
    
    @pytest.mark.asyncio
    async def test_get_unknown_resource(self, aws_mcp_server):
        """Test getting unknown resource"""
        result = await aws_mcp_server.get_resource('aws://unknown')
        
        assert result['success'] is False
        assert 'Unknown resource' in result['error']
    
    @pytest.mark.asyncio
    async def test_tool_definitions(self, aws_mcp_server):
        """Test tool definitions"""
        s3_upload_def = await aws_mcp_server._get_tool_definition('s3_upload_file')
        
        assert s3_upload_def is not None
        assert s3_upload_def['name'] == 's3_upload_file'
        assert 'inputSchema' in s3_upload_def
        assert 'bucket' in s3_upload_def['inputSchema']['properties']
        assert 'key' in s3_upload_def['inputSchema']['properties']
