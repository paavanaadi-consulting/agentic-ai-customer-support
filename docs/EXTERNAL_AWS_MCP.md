# External AWS MCP Integration Guide

This document explains how to use external AWS MCP servers from AWS Labs instead of the custom AWS MCP implementation.

## Overview

The repository now supports using official AWS Labs MCP servers for AWS operations, with automatic fallback to the custom implementation if external servers are not available.

### Supported External AWS MCP Servers

1. **AWS Lambda Tool MCP Server** (`awslabs.lambda-tool-mcp-server`)
   - Execute Lambda functions as AI tools
   - Access private AWS resources through Lambda
   - Enhanced function invocation capabilities

2. **AWS Core MCP Server** (`awslabs.core-mcp-server`)
   - Intelligent planning and MCP server orchestration
   - S3 operations and general AWS resource management
   - Parameter Store access

3. **AWS Documentation MCP Server** (`awslabs.aws-documentation-mcp-server`)
   - Real-time access to official AWS documentation
   - Latest AWS API references
   - AWS service guidance and best practices

## Installation

### Prerequisites

1. **Install uvx** (recommended method):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Configure AWS credentials**:
   ```bash
   aws configure
   # OR set environment variables
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_REGION=us-east-1
   ```

### Automated Installation

Run the installation script:
```bash
./scripts/install_external_mcp.sh
```

### Manual Installation

Install AWS MCP packages via uvx:
```bash
# Lambda Tool MCP Server
uvx install awslabs.lambda-tool-mcp-server@latest

# Core MCP Server  
uvx install awslabs.core-mcp-server@latest

# Documentation MCP Server
uvx install awslabs.aws-documentation-mcp-server@latest
```

Verify installation:
```bash
uvx list | grep awslabs
```

## Configuration

### Environment Variables

Copy and configure the AWS MCP environment file:
```bash
cp config/aws_mcp.env.example config/aws_mcp.env
```

Edit `config/aws_mcp.env`:
```bash
# AWS Credentials and Region
AWS_PROFILE=default
AWS_REGION=us-east-1

# AWS MCP Server Settings
AWS_MCP_USE_EXTERNAL=true
AWS_MCP_USE_UVX=true
AWS_MCP_FALLBACK_TO_CUSTOM=true

# Lambda Tool Configuration
LAMBDA_TOOL_MCP_ENABLED=true
FUNCTION_PREFIX=customer-support
FUNCTION_TAG_KEY=Environment
FUNCTION_TAG_VALUE=development

# Core MCP Configuration
CORE_MCP_ENABLED=true

# Documentation MCP Configuration
DOCUMENTATION_MCP_ENABLED=true

# Logging
FASTMCP_LOG_LEVEL=ERROR
```

### Application Configuration

The wrapper automatically detects and uses external MCP servers if available. Configuration options:

- `AWS_MCP_USE_EXTERNAL=true`: Enable external MCP servers
- `AWS_MCP_USE_UVX=true`: Use uvx for package management
- `AWS_MCP_FALLBACK_TO_CUSTOM=true`: Fall back to custom implementation if external not available

## Usage

### In Your Application

The `AWSMCPWrapper` provides a unified interface:

```python
from mcp.aws_mcp_wrapper import AWSMCPWrapper, ExternalMCPConfig

# Initialize with configuration
config = ExternalMCPConfig(
    aws_profile='default',
    aws_region='us-east-1',
    use_uvx=True,
    fallback_to_custom=True
)

aws_wrapper = AWSMCPWrapper(config)
await aws_wrapper.initialize()

# Use the same interface as before
result = await aws_wrapper.call_tool('lambda_invoke', {
    'function_name': 'my-function',
    'payload': {'key': 'value'}
})
```

### Available Tools

The wrapper supports all original tools with enhanced capabilities:

- `lambda_invoke`: Execute Lambda functions
- `s3_upload_file`: Upload files to S3
- `s3_download_file`: Download files from S3  
- `s3_list_objects`: List S3 objects
- `s3_delete_object`: Delete S3 objects
- `get_parameter_store_value`: Get SSM parameters
- `search_aws_docs`: Search AWS documentation (new)
- `get_aws_api_reference`: Get API references (new)

### Testing

Run the test script to verify the setup:
```bash
python scripts/test_native.py
```

## Architecture

```
┌─────────────────────────────────────────┐
│            Application Layer            │
├─────────────────────────────────────────┤
│          AWSMCPWrapper                  │
│  ┌─────────────────┬─────────────────┐  │
│  │  External MCPs  │  Custom Fallback │  │
│  │                 │                  │  │
│  │ • Lambda Tool   │ • aws_mcp_server │  │
│  │ • Core Server   │                  │  │
│  │ • Documentation │                  │  │
│  └─────────────────┴─────────────────┘  │
├─────────────────────────────────────────┤
│               uvx/pip                   │
├─────────────────────────────────────────┤
│             AWS Services                │
└─────────────────────────────────────────┘
```

## Benefits of External MCP Servers

### 1. **Official Support**
- Maintained by AWS Labs
- Regular updates with latest AWS features
- Follows AWS best practices

### 2. **Enhanced Capabilities**
- More comprehensive AWS service coverage
- Advanced Lambda execution features
- Real-time documentation access

### 3. **Better Performance**
- Optimized for AWS service integration
- Efficient resource management
- Improved error handling

### 4. **Future-Proof**
- Automatic updates via uvx
- New AWS services automatically supported
- Community-driven improvements

## Troubleshooting

### External Packages Not Found

```bash
# Check uvx installation
uvx --version

# Check available packages
uvx list | grep awslabs

# Reinstall if needed
uvx uninstall awslabs.lambda-tool-mcp-server
uvx install awslabs.lambda-tool-mcp-server@latest
```

### AWS Credential Issues

```bash
# Test AWS credentials
aws sts get-caller-identity

# Check environment variables
env | grep AWS

# Verify profile
aws configure list --profile default
```

### Fallback to Custom Server

If external servers fail, the wrapper automatically falls back to the custom implementation:

```python
# Check status
status = aws_wrapper.get_status()
print(f"Using custom server: {status['custom_server']}")
print(f"External servers: {status['external_servers']}")
```

### Debug Mode

Enable debug logging:
```bash
export FASTMCP_LOG_LEVEL=DEBUG
python scripts/test_native.py
```

## Migration Notes

### From Custom to External

The wrapper provides backward compatibility:
- All existing tool names work unchanged
- Same method signatures and return values
- Automatic detection and switching

### Configuration Changes

Update your configuration files:
1. Copy `config/aws_mcp.env.example` to `config/aws_mcp.env`
2. Update environment variables in your deployment
3. Ensure AWS credentials are properly configured

### Testing Migration

1. Run existing tests to ensure compatibility:
   ```bash
   pytest tests/mcp_servers/test_aws_mcp.py -v
   ```

2. Test with external servers:
   ```bash
   AWS_MCP_USE_EXTERNAL=true python scripts/test_native.py
   ```

3. Test fallback behavior:
   ```bash
   AWS_MCP_FALLBACK_TO_CUSTOM=false python scripts/test_native.py
   ```

## Reference

- [AWS MCP Servers Repository](https://github.com/awslabs/mcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [uvx Documentation](https://docs.astral.sh/uv/guides/tools/)
- [AWS CLI Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
