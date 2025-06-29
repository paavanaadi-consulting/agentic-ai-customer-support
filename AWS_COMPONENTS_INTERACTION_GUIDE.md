# AWS MCP Wrapper - AWS Components Interaction Guide

## Overview

The AWS MCP Wrapper (`aws_mcp_wrapper.py`) provides a unified interface to interact with various AWS services through external MCP servers from AWS Labs. This document details all AWS components and services it can interact with.

## Architecture

The wrapper operates through three main external MCP servers:

### 1. 🚀 **AWS Lambda Tool MCP Server** (`awslabs.lambda-tool-mcp-server`)
### 2. 🏗️ **AWS Core MCP Server** (`awslabs.core-mcp-server`)  
### 3. 📚 **AWS Documentation MCP Server** (`awslabs.aws-documentation-mcp-server`)

---

## AWS Services & Components Supported

### 🚀 **AWS Lambda**
**Server:** `awslabs.lambda-tool-mcp-server`

#### **Functions Available:**
- **`lambda_invoke`**: Execute Lambda functions with payload
- **`list_lambda_functions`**: List available Lambda functions

#### **Use Cases:**
```python
# Invoke a Lambda function
result = await aws_wrapper.call_tool('lambda_invoke', {
    'function_name': 'customer-support-handler',
    'payload': {
        'customer_id': 'CUST_12345',
        'query': 'How do I reset my password?'
    },
    'invocation_type': 'RequestResponse'
})

# List available functions
functions = await aws_wrapper.call_tool('list_lambda_functions', {})
```

#### **AWS Components:**
- **Lambda Functions**: All user-defined functions in the AWS account
- **Function Configurations**: Runtime, memory, timeout settings
- **Execution Roles**: IAM roles for function execution
- **Environment Variables**: Function-specific environment configuration

---

### 🗂️ **Amazon S3**
**Server:** `awslabs.core-mcp-server`

#### **Functions Available:**
- **`s3_upload_file`**: Upload files to S3 buckets
- **`s3_download_file`**: Download files from S3 buckets
- **`s3_list_objects`**: List objects in S3 buckets
- **`s3_delete_object`**: Delete objects from S3 buckets

#### **Use Cases:**
```python
# Upload a file
result = await aws_wrapper.call_tool('s3_upload_file', {
    'bucket': 'customer-support-archive',
    'key': 'responses/2024/12/response_123.json',
    'content': json.dumps(response_data),
    'content_type': 'application/json'
})

# Download a file
file_data = await aws_wrapper.call_tool('s3_download_file', {
    'bucket': 'customer-support-archive',
    'key': 'responses/2024/12/response_123.json'
})

# List objects
objects = await aws_wrapper.call_tool('s3_list_objects', {
    'bucket': 'customer-support-archive',
    'prefix': 'responses/2024/',
    'max_keys': 100
})

# Delete an object
result = await aws_wrapper.call_tool('s3_delete_object', {
    'bucket': 'customer-support-archive',
    'key': 'old_response.json'
})
```

#### **AWS Components:**
- **S3 Buckets**: All buckets in the AWS account
- **S3 Objects**: Files and data stored in buckets
- **Object Metadata**: Content type, last modified, ETag
- **Bucket Policies**: Access control and permissions
- **Versioning**: Object version management

---

### 🔧 **AWS Systems Manager (SSM)**
**Server:** `awslabs.core-mcp-server`

#### **Functions Available:**
- **`get_parameter_store_value`**: Retrieve values from Parameter Store

#### **Use Cases:**
```python
# Get a configuration parameter
param = await aws_wrapper.call_tool('get_parameter_store_value', {
    'parameter_name': '/customer-support/api-keys/openai',
    'with_decryption': True
})

# Get application settings
settings = await aws_wrapper.call_tool('get_parameter_store_value', {
    'parameter_name': '/customer-support/config/max-retries',
    'with_decryption': False
})
```

#### **AWS Components:**
- **Parameter Store**: Secure storage for configuration data
- **Encrypted Parameters**: KMS-encrypted sensitive data
- **Parameter Hierarchies**: Organized parameter namespaces
- **Parameter Policies**: Advanced parameter features

---

### 📚 **AWS Documentation & API References**
**Server:** `awslabs.aws-documentation-mcp-server`

#### **Functions Available:**
- **`search_aws_docs`**: Search official AWS documentation
- **`get_aws_api_reference`**: Get AWS API references and guides

#### **Use Cases:**
```python
# Search AWS documentation
docs = await aws_wrapper.call_tool('search_aws_docs', {
    'query': 'Lambda error handling best practices',
    'service': 'lambda',
    'max_results': 5
})

# Get API reference
api_ref = await aws_wrapper.call_tool('get_aws_api_reference', {
    'service': 's3',
    'operation': 'put_object'
})
```

#### **AWS Components:**
- **AWS Service Documentation**: Official service guides
- **API References**: Complete API documentation
- **Best Practices**: AWS-recommended patterns
- **Code Examples**: Official AWS code samples
- **Troubleshooting Guides**: Error resolution documentation

---

## Legacy Tool Mapping

The wrapper provides backward compatibility by mapping legacy tool names:

```python
# Legacy tool mapping
legacy_tool_map = {
    "s3_upload_file": "s3_operations",      # → Core MCP Server
    "s3_download_file": "s3_operations",    # → Core MCP Server
    "s3_list_objects": "s3_operations",     # → Core MCP Server
    "s3_delete_object": "s3_operations",    # → Core MCP Server
    "lambda_invoke": "lambda_invoke",       # → Lambda Tool MCP Server
    "get_parameter_store_value": "get_parameter_store_value"  # → Core MCP Server
}
```

## AWS Authentication & Authorization

### **Authentication Methods:**
1. **AWS Profiles** (Default)
   - Uses AWS CLI profiles (`~/.aws/credentials`)
   - Configurable via `aws_profile` parameter

2. **Environment Variables**
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_SESSION_TOKEN` (for temporary credentials)

3. **IAM Roles**
   - EC2 instance profiles
   - ECS task roles
   - Lambda execution roles

### **Required Permissions:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction",
                "lambda:ListFunctions",
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "ssm:GetParameter",
                "ssm:GetParameters"
            ],
            "Resource": "*"
        }
    ]
}
```

## Configuration

### **Environment Variables:**
```bash
# AWS Credentials and Region
AWS_PROFILE=default
AWS_REGION=us-east-1

# MCP Wrapper Configuration
AWS_MCP_USE_EXTERNAL=true
AWS_MCP_USE_UVX=true
AWS_MCP_FALLBACK_TO_CUSTOM=false

# Server-specific Configuration
LAMBDA_TOOL_MCP_ENABLED=true
CORE_MCP_ENABLED=true
DOCUMENTATION_MCP_ENABLED=true
```

### **Application Configuration:**
```python
from mcp.aws_mcp_wrapper import AWSMCPWrapper, ExternalMCPConfig

config = ExternalMCPConfig(
    lambda_tool_enabled=True,       # Enable Lambda operations
    core_enabled=True,              # Enable S3 and SSM operations
    documentation_enabled=True,     # Enable documentation access
    aws_profile='default',          # AWS profile to use
    aws_region='us-east-1',         # AWS region
    use_uvx=True,                   # Use uvx for package management
    fallback_to_custom=False        # No custom fallback available
)

aws_wrapper = AWSMCPWrapper(config)
await aws_wrapper.initialize()
```

## Customer Support Use Cases

### **1. Document Storage & Retrieval**
```python
# Store customer interaction
await aws_wrapper.call_tool('s3_upload_file', {
    'bucket': 'customer-interactions',
    'key': f'interactions/{customer_id}/{timestamp}.json',
    'content': json.dumps(interaction_data)
})
```

### **2. Serverless Processing**
```python
# Process customer query via Lambda
result = await aws_wrapper.call_tool('lambda_invoke', {
    'function_name': 'query-processor',
    'payload': {'query': customer_query, 'context': customer_context}
})
```

### **3. Configuration Management**
```python
# Get API keys and configuration
api_key = await aws_wrapper.call_tool('get_parameter_store_value', {
    'parameter_name': '/app/openai/api-key',
    'with_decryption': True
})
```

### **4. Knowledge Base Access**
```python
# Search AWS best practices
docs = await aws_wrapper.call_tool('search_aws_docs', {
    'query': 'customer service automation patterns'
})
```

## Error Handling & Fallback

### **External Package Requirements:**
- External MCP servers must be installed via uvx
- AWS credentials must be properly configured
- Network access to AWS APIs required

### **Fallback Behavior:**
```python
# Custom fallback has been removed
# If external packages fail, clear error messages guide users:
# "Custom AWS MCP server fallback removed. External AWS MCP packages required for AWS functionality."
```

### **Installation Command:**
```bash
# Install required external packages
uvx install awslabs.lambda-tool-mcp-server
uvx install awslabs.core-mcp-server  
uvx install awslabs.aws-documentation-mcp-server
```

## Summary

The AWS MCP Wrapper provides comprehensive access to AWS services essential for customer support operations:

- **🚀 Lambda**: Serverless processing and function execution
- **🗂️ S3**: Document storage, archival, and retrieval
- **🔧 SSM**: Secure configuration and parameter management
- **📚 Documentation**: Real-time access to AWS knowledge base

All interactions are handled through official AWS Labs MCP servers, ensuring reliability, security, and access to the latest AWS features.
