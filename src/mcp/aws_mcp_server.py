"""
AWS MCP Server
Provides AWS service integrations via Model Context Protocol (MCP)
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
import os
import base64

from .base_mcp_server import BaseMCPServer
from .aws_mcp_wrapper import AWSMCPWrapper, ExternalMCPConfig

# Try to import AWS SDK
try:
    import boto3
    import botocore
    from boto3.session import Session
    from botocore.exceptions import ClientError, BotoCoreError
    AWS_SDK_AVAILABLE = True
except ImportError:
    AWS_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)


class AWSMCPServer(BaseMCPServer):
    """
    AWS MCP Server implementation that provides access to AWS services
    through the MCP protocol. It supports Lambda, SNS, SQS, S3, and other services.
    """
    
    def __init__(self,
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None,
                 region_name: str = "us-east-1",
                 use_external_mcp: bool = True,
                 host: str = "0.0.0.0",
                 port: int = 8765):
        """
        Initialize the AWS MCP Server.
        
        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region_name: AWS region name
            use_external_mcp: Whether to use external MCP servers via AWSMCPWrapper
            host: Host address for the MCP server
            port: Port for the MCP server
        """
        super().__init__(host=host, port=port)
        
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self.use_external_mcp = use_external_mcp
        
        # AWS session and clients
        self.session = None
        self.clients = {}
        
        # External MCP wrapper
        self.aws_mcp_wrapper = None
        
        # Register RPC methods
        self._register_rpc_methods()
    
    async def start(self):
        """Start the AWS MCP server."""
        # Initialize AWS session
        self._init_aws_session()
        
        # Initialize external MCP wrapper if needed
        if self.use_external_mcp:
            config = ExternalMCPConfig(
                aws_profile=os.environ.get("AWS_PROFILE", "default"),
                aws_region=self.region_name
            )
            self.aws_mcp_wrapper = AWSMCPWrapper(config)
            
            # Start external MCP servers
            await self.aws_mcp_wrapper.start_servers()
            logger.info("Started external AWS MCP servers")
        
        # Start the MCP server
        await super().start()
    
    async def stop(self):
        """Stop the AWS MCP server."""
        # Stop external MCP wrapper if used
        if self.aws_mcp_wrapper:
            await self.aws_mcp_wrapper.stop_servers()
            logger.info("Stopped external AWS MCP servers")
        
        # Stop the MCP server
        await super().stop()
    
    def _init_aws_session(self):
        """Initialize the AWS session."""
        if not AWS_SDK_AVAILABLE:
            logger.warning("AWS SDK not available, some functionalities may be limited")
            return
        
        try:
            session_kwargs = {"region_name": self.region_name}
            if self.aws_access_key_id and self.aws_secret_access_key:
                session_kwargs.update({
                    "aws_access_key_id": self.aws_access_key_id,
                    "aws_secret_access_key": self.aws_secret_access_key
                })
            
            self.session = Session(**session_kwargs)
            logger.info("AWS session initialized successfully")
        except (BotoCoreError, Exception) as e:
            logger.error(f"Failed to initialize AWS session: {str(e)}")
    
    def _get_client(self, service_name: str):
        """Get or create an AWS service client."""
        if not AWS_SDK_AVAILABLE:
            raise Exception(f"AWS SDK not available, cannot create {service_name} client")
        
        if not self.session:
            raise Exception("AWS session not initialized")
        
        if service_name not in self.clients:
            self.clients[service_name] = self.session.client(service_name)
        
        return self.clients[service_name]
    
    def _register_rpc_methods(self):
        """Register RPC methods for AWS services."""
        
        # Lambda methods
        @self.rpc_method
        async def invoke_lambda(function_name: str, payload: Dict[str, Any],
                               invocation_type: str = "RequestResponse") -> Dict[str, Any]:
            """
            Invoke an AWS Lambda function.
            
            Args:
                function_name: Name or ARN of the Lambda function
                payload: Function input payload
                invocation_type: RequestResponse (synchronous) or Event (asynchronous)
            
            Returns:
                Dictionary containing the function response
            """
            try:
                lambda_client = self._get_client('lambda')
                
                # Convert payload to JSON bytes
                payload_bytes = json.dumps(payload).encode('utf-8')
                
                response = lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType=invocation_type,
                    Payload=payload_bytes
                )
                
                result = {
                    'StatusCode': response.get('StatusCode'),
                    'ExecutedVersion': response.get('ExecutedVersion'),
                }
                
                # Read and decode the payload
                if 'Payload' in response:
                    payload_content = response['Payload'].read().decode('utf-8')
                    try:
                        result['Payload'] = json.loads(payload_content)
                    except:
                        result['Payload'] = payload_content
                
                return result
            except Exception as e:
                logger.error(f"Error invoking Lambda: {str(e)}")
                raise
        
        @self.rpc_method
        async def list_lambda_functions(max_items: int = 50) -> List[Dict[str, Any]]:
            """
            List Lambda functions in the account.
            
            Args:
                max_items: Maximum number of functions to return
            
            Returns:
                List of Lambda function metadata
            """
            try:
                lambda_client = self._get_client('lambda')
                response = lambda_client.list_functions(MaxItems=max_items)
                
                # Convert datetime objects to ISO format strings for JSON serialization
                functions = []
                for function in response.get('Functions', []):
                    func_dict = {}
                    for key, value in function.items():
                        if hasattr(value, 'isoformat'):
                            func_dict[key] = value.isoformat()
                        else:
                            func_dict[key] = value
                    functions.append(func_dict)
                
                return functions
            except Exception as e:
                logger.error(f"Error listing Lambda functions: {str(e)}")
                raise
        
        # S3 methods
        @self.rpc_method
        async def list_s3_buckets() -> List[Dict[str, Any]]:
            """
            List S3 buckets in the account.
            
            Returns:
                List of S3 bucket metadata
            """
            try:
                s3_client = self._get_client('s3')
                response = s3_client.list_buckets()
                
                # Convert datetime objects to ISO format strings
                buckets = []
                for bucket in response.get('Buckets', []):
                    bucket_dict = {}
                    for key, value in bucket.items():
                        if hasattr(value, 'isoformat'):
                            bucket_dict[key] = value.isoformat()
                        else:
                            bucket_dict[key] = value
                    buckets.append(bucket_dict)
                
                return buckets
            except Exception as e:
                logger.error(f"Error listing S3 buckets: {str(e)}")
                raise
        
        @self.rpc_method
        async def list_s3_objects(bucket: str, prefix: str = "", max_keys: int = 1000) -> Dict[str, Any]:
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
                s3_client = self._get_client('s3')
                response = s3_client.list_objects_v2(
                    Bucket=bucket,
                    Prefix=prefix,
                    MaxKeys=max_keys
                )
                
                # Convert datetime objects to ISO format strings
                objects = []
                for obj in response.get('Contents', []):
                    obj_dict = {}
                    for key, value in obj.items():
                        if hasattr(value, 'isoformat'):
                            obj_dict[key] = value.isoformat()
                        else:
                            obj_dict[key] = value
                    objects.append(obj_dict)
                
                return {
                    'Objects': objects,
                    'IsTruncated': response.get('IsTruncated', False),
                    'NextContinuationToken': response.get('NextContinuationToken')
                }
            except Exception as e:
                logger.error(f"Error listing S3 objects: {str(e)}")
                raise
        
        @self.rpc_method
        async def get_s3_object(bucket: str, key: str) -> Dict[str, Any]:
            """
            Get an object from an S3 bucket.
            
            Args:
                bucket: Name of the S3 bucket
                key: Object key (path)
            
            Returns:
                Dictionary containing object data and metadata
            """
            try:
                s3_client = self._get_client('s3')
                response = s3_client.get_object(Bucket=bucket, Key=key)
                
                body = response['Body'].read()
                content_type = response.get('ContentType', '')
                
                # Decide how to handle the body based on content type
                is_base64_encoded = True
                if 'text/' in content_type or 'application/json' in content_type:
                    try:
                        body_content = body.decode('utf-8')
                        is_base64_encoded = False
                    except UnicodeDecodeError:
                        body_content = base64.b64encode(body).decode('ascii')
                else:
                    body_content = base64.b64encode(body).decode('ascii')
                
                result = {
                    'Body': body_content,
                    'ContentType': content_type,
                    'ContentLength': response.get('ContentLength'),
                    'Metadata': response.get('Metadata', {}),
                    'IsBase64Encoded': is_base64_encoded
                }
                
                # Convert datetime objects to ISO format strings
                for key, value in response.items():
                    if hasattr(value, 'isoformat') and key not in result:
                        result[key] = value.isoformat()
                
                return result
            except Exception as e:
                logger.error(f"Error getting S3 object: {str(e)}")
                raise
        
        @self.rpc_method
        async def put_s3_object(bucket: str, key: str, body: str,
                              content_type: str = "application/octet-stream",
                              metadata: Dict[str, str] = None,
                              is_base64_encoded: bool = False) -> Dict[str, Any]:
            """
            Put an object into an S3 bucket.
            
            Args:
                bucket: Name of the S3 bucket
                key: Object key (path)
                body: Object content as string or base64-encoded string
                content_type: MIME type of the object
                metadata: Object metadata
                is_base64_encoded: Whether the body is base64 encoded
            
            Returns:
                Dictionary containing operation result
            """
            try:
                s3_client = self._get_client('s3')
                
                # Decode base64 if necessary
                if is_base64_encoded:
                    body_bytes = base64.b64decode(body)
                else:
                    body_bytes = body.encode('utf-8')
                
                kwargs = {
                    'Bucket': bucket,
                    'Key': key,
                    'Body': body_bytes,
                    'ContentType': content_type
                }
                
                if metadata:
                    kwargs['Metadata'] = metadata
                
                response = s3_client.put_object(**kwargs)
                
                result = {}
                for key, value in response.items():
                    if hasattr(value, 'isoformat'):
                        result[key] = value.isoformat()
                    else:
                        result[key] = value
                
                # ETag comes with quotes, remove them
                if 'ETag' in result:
                    result['ETag'] = result['ETag'].strip('"')
                
                return result
            except Exception as e:
                logger.error(f"Error putting S3 object: {str(e)}")
                raise
        
        # SQS methods
        @self.rpc_method
        async def send_sqs_message(queue_url: str, message_body: str,
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
                        elif isinstance(value, dict) and 'BinaryValue' in value:
                            attr_type = 'Binary'
                            attr_value = base64.b64decode(value['BinaryValue'])
                        else:
                            continue
                        
                        formatted_attrs[key] = {
                            'DataType': 'String',  # SQS requires this
                            attr_type + 'Value': attr_value
                        }
                    
                    kwargs['MessageAttributes'] = formatted_attrs
                
                response = sqs_client.send_message(**kwargs)
                
                return {
                    'MessageId': response.get('MessageId'),
                    'MD5OfMessageBody': response.get('MD5OfMessageBody')
                }
            except Exception as e:
                logger.error(f"Error sending SQS message: {str(e)}")
                raise
        
        @self.rpc_method
        async def receive_sqs_messages(queue_url: str, max_messages: int = 10,
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
                sqs_client = self._get_client('sqs')
                
                response = sqs_client.receive_message(
                    QueueUrl=queue_url,
                    MaxNumberOfMessages=max(1, min(max_messages, 10)),
                    WaitTimeSeconds=max(0, min(wait_time_seconds, 20)),
                    VisibilityTimeout=visibility_timeout,
                    AttributeNames=['All'],
                    MessageAttributeNames=['All']
                )
                
                # Convert binary message attributes to base64
                messages = []
                for msg in response.get('Messages', []):
                    if 'MessageAttributes' in msg:
                        for key, attr in msg['MessageAttributes'].items():
                            if 'BinaryValue' in attr:
                                attr['BinaryValue'] = base64.b64encode(
                                    attr['BinaryValue']).decode('ascii')
                    messages.append(msg)
                
                return messages
            except Exception as e:
                logger.error(f"Error receiving SQS messages: {str(e)}")
                raise
        
        @self.rpc_method
        async def delete_sqs_message(queue_url: str, receipt_handle: str) -> Dict[str, bool]:
            """
            Delete a message from an SQS queue.
            
            Args:
                queue_url: URL of the SQS queue
                receipt_handle: Receipt handle of the message to delete
            
            Returns:
                Dictionary indicating success
            """
            try:
                sqs_client = self._get_client('sqs')
                
                sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle
                )
                
                return {"success": True}
            except Exception as e:
                logger.error(f"Error deleting SQS message: {str(e)}")
                raise
        
        # SNS methods
        @self.rpc_method
        async def publish_sns_message(topic_arn: str, message: str, 
                                    subject: Optional[str] = None,
                                    message_attributes: Dict[str, Any] = None) -> Dict[str, str]:
            """
            Publish a message to an SNS topic.
            
            Args:
                topic_arn: ARN of the SNS topic
                message: Message content
                subject: Optional subject line
                message_attributes: Message attributes
            
            Returns:
                Dictionary containing the message ID
            """
            try:
                sns_client = self._get_client('sns')
                
                kwargs = {
                    'TopicArn': topic_arn,
                    'Message': message
                }
                
                if subject:
                    kwargs['Subject'] = subject
                
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
                        elif isinstance(value, dict) and 'BinaryValue' in value:
                            attr_type = 'Binary'
                            attr_value = base64.b64decode(value['BinaryValue'])
                        else:
                            continue
                        
                        formatted_attrs[key] = {
                            'DataType': 'String',  # SNS requires this
                            attr_type + 'Value': attr_value
                        }
                    
                    kwargs['MessageAttributes'] = formatted_attrs
                
                response = sns_client.publish(**kwargs)
                
                return {"MessageId": response.get('MessageId')}
            except Exception as e:
                logger.error(f"Error publishing SNS message: {str(e)}")
                raise
        
        @self.rpc_method
        async def list_sns_topics(next_token: Optional[str] = None) -> Dict[str, Any]:
            """
            List SNS topics in the account.
            
            Args:
                next_token: Pagination token for additional results
            
            Returns:
                Dictionary containing topics and next pagination token
            """
            try:
                sns_client = self._get_client('sns')
                
                kwargs = {}
                if next_token:
                    kwargs['NextToken'] = next_token
                
                response = sns_client.list_topics(**kwargs)
                
                return {
                    'Topics': response.get('Topics', []),
                    'NextToken': response.get('NextToken')
                }
            except Exception as e:
                logger.error(f"Error listing SNS topics: {str(e)}")
                raise
        
        # Secret Manager methods
        @self.rpc_method
        async def get_secret(secret_id: str, version_id: Optional[str] = None) -> Dict[str, Any]:
            """
            Get a secret from AWS Secrets Manager.
            
            Args:
                secret_id: The ARN or name of the secret
                version_id: The version of the secret (optional)
            
            Returns:
                Dictionary containing the secret value
            """
            try:
                secretsmanager_client = self._get_client('secretsmanager')
                
                kwargs = {'SecretId': secret_id}
                if version_id:
                    kwargs['VersionId'] = version_id
                
                response = secretsmanager_client.get_secret_value(**kwargs)
                
                result = {
                    'ARN': response.get('ARN'),
                    'Name': response.get('Name'),
                    'VersionId': response.get('VersionId'),
                    'VersionStages': response.get('VersionStages', [])
                }
                
                # Convert datetime objects to ISO format
                if 'CreatedDate' in response:
                    result['CreatedDate'] = response['CreatedDate'].isoformat()
                
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
                    binary_data = response['SecretBinary']
                    result['SecretBinary'] = base64.b64encode(binary_data).decode('ascii')
                
                return result
            except Exception as e:
                logger.error(f"Error getting secret: {str(e)}")
                raise
        
        # DynamoDB methods
        @self.rpc_method
        async def dynamodb_get_item(table_name: str, key: Dict[str, Any]) -> Dict[str, Any]:
            """
            Get an item from a DynamoDB table.
            
            Args:
                table_name: Name of the DynamoDB table
                key: Key attributes that define the item
            
            Returns:
                Dictionary containing the item attributes
            """
            try:
                dynamodb_client = self._get_client('dynamodb')
                
                # Convert Python types to DynamoDB types
                dynamodb_key = self._convert_to_dynamodb_format(key)
                
                response = dynamodb_client.get_item(
                    TableName=table_name,
                    Key=dynamodb_key
                )
                
                # Convert DynamoDB types back to Python types
                if 'Item' in response:
                    return self._convert_from_dynamodb_format(response['Item'])
                else:
                    return {}
            except Exception as e:
                logger.error(f"Error getting DynamoDB item: {str(e)}")
                raise
        
        @self.rpc_method
        async def dynamodb_put_item(table_name: str, item: Dict[str, Any]) -> Dict[str, Any]:
            """
            Put an item into a DynamoDB table.
            
            Args:
                table_name: Name of the DynamoDB table
                item: Item attributes to store
            
            Returns:
                Dictionary containing attributes of the new item
            """
            try:
                dynamodb_client = self._get_client('dynamodb')
                
                # Convert Python types to DynamoDB types
                dynamodb_item = self._convert_to_dynamodb_format(item)
                
                response = dynamodb_client.put_item(
                    TableName=table_name,
                    Item=dynamodb_item
                )
                
                return {"success": True}
            except Exception as e:
                logger.error(f"Error putting DynamoDB item: {str(e)}")
                raise
    
    def _convert_to_dynamodb_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Python data types to DynamoDB format.
        
        Args:
            data: Dictionary with Python data types
        
        Returns:
            Dictionary with DynamoDB format
        """
        result = {}
        for key, value in data.items():
            if value is None:
                result[key] = {'NULL': True}
            elif isinstance(value, str):
                result[key] = {'S': value}
            elif isinstance(value, bool):
                result[key] = {'BOOL': value}
            elif isinstance(value, (int, float)):
                result[key] = {'N': str(value)}
            elif isinstance(value, dict):
                result[key] = {'M': self._convert_to_dynamodb_format(value)}
            elif isinstance(value, list):
                if not value:
                    result[key] = {'L': []}
                elif all(isinstance(x, str) for x in value):
                    result[key] = {'SS': value}
                elif all(isinstance(x, (int, float)) for x in value):
                    result[key] = {'NS': [str(x) for x in value]}
                elif all(isinstance(x, bytes) for x in value):
                    result[key] = {'BS': value}
                else:
                    result[key] = {'L': [self._convert_value_to_dynamodb(v) for v in value]}
            elif isinstance(value, bytes):
                result[key] = {'B': value}
            else:
                # Convert to string as fallback
                result[key] = {'S': str(value)}
        
        return result
    
    def _convert_value_to_dynamodb(self, value: Any) -> Dict[str, Any]:
        """Convert a single Python value to DynamoDB format."""
        if value is None:
            return {'NULL': True}
        elif isinstance(value, str):
            return {'S': value}
        elif isinstance(value, bool):
            return {'BOOL': value}
        elif isinstance(value, (int, float)):
            return {'N': str(value)}
        elif isinstance(value, dict):
            return {'M': self._convert_to_dynamodb_format(value)}
        elif isinstance(value, list):
            return {'L': [self._convert_value_to_dynamodb(v) for v in value]}
        elif isinstance(value, bytes):
            return {'B': value}
        else:
            # Convert to string as fallback
            return {'S': str(value)}
    
    def _convert_from_dynamodb_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert DynamoDB format to Python data types.
        
        Args:
            data: Dictionary with DynamoDB format
        
        Returns:
            Dictionary with Python data types
        """
        result = {}
        for key, value in data.items():
            if 'NULL' in value:
                result[key] = None
            elif 'S' in value:
                result[key] = value['S']
            elif 'BOOL' in value:
                result[key] = value['BOOL']
            elif 'N' in value:
                # Convert to int or float as appropriate
                try:
                    if '.' in value['N']:
                        result[key] = float(value['N'])
                    else:
                        result[key] = int(value['N'])
                except ValueError:
                    result[key] = value['N']
            elif 'M' in value:
                result[key] = self._convert_from_dynamodb_format(value['M'])
            elif 'L' in value:
                result[key] = [self._convert_value_from_dynamodb(v) for v in value['L']]
            elif 'SS' in value:
                result[key] = value['SS']
            elif 'NS' in value:
                result[key] = [float(x) if '.' in x else int(x) for x in value['NS']]
            elif 'BS' in value:
                result[key] = value['BS']
            elif 'B' in value:
                result[key] = value['B']
        
        return result
    
    def _convert_value_from_dynamodb(self, value: Dict[str, Any]) -> Any:
        """Convert a single DynamoDB value to Python type."""
        if 'NULL' in value:
            return None
        elif 'S' in value:
            return value['S']
        elif 'BOOL' in value:
            return value['BOOL']
        elif 'N' in value:
            try:
                if '.' in value['N']:
                    return float(value['N'])
                else:
                    return int(value['N'])
            except ValueError:
                return value['N']
        elif 'M' in value:
            return self._convert_from_dynamodb_format(value['M'])
        elif 'L' in value:
            return [self._convert_value_from_dynamodb(v) for v in value['L']]
        elif 'SS' in value:
            return value['SS']
        elif 'NS' in value:
            return [float(x) if '.' in x else int(x) for x in value['NS']]
        elif 'BS' in value:
            return value['BS']
        elif 'B' in value:
            return value['B']
        else:
            return None
