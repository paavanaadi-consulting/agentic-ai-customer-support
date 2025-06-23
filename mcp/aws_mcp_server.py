"""
MCP server for AWS operations
"""
import json
import boto3
from typing import Dict, Any, List, Optional
from mcp.base_mcp_server import BaseMCPServer

class AWSMCPServer(BaseMCPServer):
    """MCP server for AWS operations"""
    
    def __init__(self, aws_access_key_id: str = None, aws_secret_access_key: str = None, region_name: str = 'us-east-1'):
        tools = [
            's3_upload_file',
            's3_download_file',
            's3_list_objects',
            's3_delete_object',
            'lambda_invoke',
            'get_parameter_store_value'
        ]
        
        resources = [
            'aws://s3/buckets',
            'aws://lambda/functions',
            'aws://ssm/parameters'
        ]
        
        super().__init__(
            server_id="mcp_aws",
            name="AWS MCP Server",
            capabilities=['tools', 'resources', 'storage'],
            tools=tools,
            resources=resources
        )
        
        # Initialize AWS clients
        session_kwargs = {'region_name': region_name}
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs.update({
                'aws_access_key_id': aws_access_key_id,
                'aws_secret_access_key': aws_secret_access_key
            })
        
        self.session = boto3.Session(**session_kwargs)
        self.s3_client = None
        self.lambda_client = None
        self.ssm_client = None
    
    async def start(self):
        """Start the AWS MCP server"""
        try:
            self.s3_client = self.session.client('s3')
            self.lambda_client = self.session.client('lambda')
            self.ssm_client = self.session.client('ssm')
            self.running = True
            self.logger.info("AWS MCP server started")
        except Exception as e:
            self.logger.error(f"Failed to start AWS MCP server: {e}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AWS operations"""
        try:
            if tool_name == 's3_upload_file':
                bucket = arguments.get('bucket')
                key = arguments.get('key')
                file_content = arguments.get('content')
                content_type = arguments.get('content_type', 'application/octet-stream')
                
                response = self.s3_client.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=file_content,
                    ContentType=content_type
                )
                
                return {
                    'success': True,
                    'bucket': bucket,
                    'key': key,
                    'etag': response.get('ETag'),
                    'version_id': response.get('VersionId')
                }
                
            elif tool_name == 's3_download_file':
                bucket = arguments.get('bucket')
                key = arguments.get('key')
                
                response = self.s3_client.get_object(Bucket=bucket, Key=key)
                content = response['Body'].read()
                
                return {
                    'success': True,
                    'bucket': bucket,
                    'key': key,
                    'content': content.decode('utf-8') if content else '',
                    'content_type': response.get('ContentType'),
                    'last_modified': response.get('LastModified').isoformat() if response.get('LastModified') else None
                }
                
            elif tool_name == 's3_list_objects':
                bucket = arguments.get('bucket')
                prefix = arguments.get('prefix', '')
                max_keys = arguments.get('max_keys', 100)
                
                response = self.s3_client.list_objects_v2(
                    Bucket=bucket,
                    Prefix=prefix,
                    MaxKeys=max_keys
                )
                
                objects = []
                for obj in response.get('Contents', []):
                    objects.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'etag': obj['ETag']
                    })
                
                return {
                    'success': True,
                    'bucket': bucket,
                    'objects': objects,
                    'count': len(objects),
                    'is_truncated': response.get('IsTruncated', False)
                }
                
            elif tool_name == 's3_delete_object':
                bucket = arguments.get('bucket')
                key = arguments.get('key')
                
                response = self.s3_client.delete_object(Bucket=bucket, Key=key)
                
                return {
                    'success': True,
                    'bucket': bucket,
                    'key': key,
                    'delete_marker': response.get('DeleteMarker', False)
                }
                
            elif tool_name == 'lambda_invoke':
                function_name = arguments.get('function_name')
                payload = arguments.get('payload', {})
                invocation_type = arguments.get('invocation_type', 'RequestResponse')
                
                response = self.lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType=invocation_type,
                    Payload=json.dumps(payload)
                )
                
                result = {
                    'success': True,
                    'function_name': function_name,
                    'status_code': response['StatusCode'],
                    'execution_result': response.get('ExecutedVersion')
                }
                
                if 'Payload' in response:
                    payload_data = response['Payload'].read()
                    if payload_data:
                        result['response'] = json.loads(payload_data.decode('utf-8'))
                
                return result
                
            elif tool_name == 'get_parameter_store_value':
                parameter_name = arguments.get('parameter_name')
                with_decryption = arguments.get('with_decryption', True)
                
                response = self.ssm_client.get_parameter(
                    Name=parameter_name,
                    WithDecryption=with_decryption
                )
                
                parameter = response['Parameter']
                return {
                    'success': True,
                    'name': parameter['Name'],
                    'value': parameter['Value'],
                    'type': parameter['Type'],
                    'version': parameter['Version'],
                    'last_modified_date': parameter['LastModifiedDate'].isoformat()
                }
                
            else:
                return {
                    'success': False,
                    'error': f'Unknown tool: {tool_name}'
                }
                
        except Exception as e:
            self.logger.error(f"AWS tool error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
        """Get AWS resource"""
        try:
            if resource_uri == 'aws://s3/buckets':
                response = self.s3_client.list_buckets()
                buckets = [
                    {
                        'name': bucket['Name'],
                        'creation_date': bucket['CreationDate'].isoformat()
                    }
                    for bucket in response['Buckets']
                ]
                
                return {
                    'success': True,
                    'contents': [
                        {
                            'uri': resource_uri,
                            'mimeType': 'application/json',
                            'text': json.dumps(buckets, indent=2)
                        }
                    ]
                }
                
            elif resource_uri == 'aws://lambda/functions':
                response = self.lambda_client.list_functions()
                functions = [
                    {
                        'function_name': func['FunctionName'],
                        'runtime': func['Runtime'],
                        'handler': func['Handler'],
                        'code_size': func['CodeSize'],
                        'last_modified': func['LastModified']
                    }
                    for func in response['Functions']
                ]
                
                return {
                    'success': True,
                    'contents': [
                        {
                            'uri': resource_uri,
                            'mimeType': 'application/json',
                            'text': json.dumps(functions, indent=2)
                        }
                    ]
                }
                
            else:
                return {
                    'success': False,
                    'error': f'Unknown resource: {resource_uri}'
                }
                
        except Exception as e:
            self.logger.error(f"AWS resource error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _get_tool_definition(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed tool definitions"""
        definitions = {
            's3_upload_file': {
                "name": "s3_upload_file",
                "description": "Upload a file to S3 bucket",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "bucket": {"type": "string", "description": "S3 bucket name"},
                        "key": {"type": "string", "description": "Object key"},
                        "content": {"type": "string", "description": "File content"},
                        "content_type": {"type": "string", "description": "Content type"}
                    },
                    "required": ["bucket", "key", "content"]
                }
            },
            's3_download_file': {
                "name": "s3_download_file",
                "description": "Download a file from S3 bucket",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "bucket": {"type": "string", "description": "S3 bucket name"},
                        "key": {"type": "string", "description": "Object key"}
                    },
                    "required": ["bucket", "key"]
                }
            },
            'lambda_invoke': {
                "name": "lambda_invoke",
                "description": "Invoke a Lambda function",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "function_name": {"type": "string", "description": "Lambda function name"},
                        "payload": {"type": "object", "description": "Function payload"},
                        "invocation_type": {"type": "string", "description": "Invocation type"}
                    },
                    "required": ["function_name"]
                }
            }
        }
        
        return definitions.get(tool_name, await super()._get_tool_definition(tool_name))
