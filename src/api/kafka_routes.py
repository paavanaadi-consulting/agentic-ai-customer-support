"""
Kafka/Streaming API routes for real-time customer support operations.
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
import json

from .schemas import (
    KafkaMessageRequest, KafkaMessageResponse,
    KafkaTopicRequest, KafkaTopicResponse,
    KafkaConsumeRequest, KafkaConsumeResponse,
    StreamingQueryRequest, StreamingQueryResponse,
    QueryRequest, QueryResponse,
    TopicMetadataResponse, ClusterInfoResponse, TopicListResponse,
    CustomerQueryRequest, AgentResponseRequest,
    ConsumerRequest, ConsumerResponse,
    HealthCheckResponse, ActiveConsumersResponse,
    CustomerSupportSetupResponse, RecentQueriesResponse, RecentResponsesResponse,
    ConsumerStartRequest, ConsumerStartResponse, ConsumerStatusResponse,
    TableSetupResponse, TestInsertResponse, DatabaseQueryResponse
)
from .dependencies import get_kafka_client_dep, get_query_service_dep
from ..mcp.kafka_mcp_client import OptimizedKafkaMCPClient
from ..services.query_service import QueryService

router = APIRouter(prefix="/streaming", tags=["Kafka/Streaming"])
logger = logging.getLogger(__name__)


@router.post("/publish", response_model=KafkaMessageResponse, summary="Publish message to Kafka topic")
async def publish_message(
    request: KafkaMessageRequest,
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Publish a message to a Kafka topic.
    
    This endpoint allows publishing arbitrary messages to Kafka topics
    for real-time event processing.
    """
    try:
        result = await kafka_client.call_tool("publish_message", {
            'topic': request.topic,
            'message': request.message,
            'key': request.key
        })
        
        if result.get('success'):
            result_data = result.get('result', {})
            return KafkaMessageResponse(
                success=True,
                topic=result_data.get('topic', request.topic),
                partition=result_data.get('partition'),
                offset=result_data.get('offset'),
                timestamp=datetime.utcnow()
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to publish message'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish message: {str(e)}")


@router.post("/consume", response_model=KafkaConsumeResponse, summary="Consume messages from Kafka topic")
async def consume_messages(
    request: KafkaConsumeRequest,
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Consume messages from a Kafka topic.
    
    This endpoint retrieves recent messages from the specified topic.
    """
    try:
        result = await kafka_client.call_tool("consume_messages", {
            'topic': request.topic,
            'max_messages': request.max_messages,
            'timeout_ms': request.timeout_ms
        })
        
        if result.get('success'):
            result_data = result.get('result', {})
            return KafkaConsumeResponse(
                success=True,
                messages=result_data.get('messages', []),
                count=result_data.get('count', 0)
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to consume messages'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to consume messages: {str(e)}")


@router.post("/topics", response_model=KafkaTopicResponse, summary="Create Kafka topic")
async def create_topic(
    request: KafkaTopicRequest,
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Create a new Kafka topic.
    
    This endpoint creates a new topic with the specified configuration.
    """
    try:
        result = await kafka_client.call_tool("create_topic", {
            'topic': request.topic,
            'num_partitions': request.num_partitions,
            'replication_factor': request.replication_factor
        })
        
        if result.get('success'):
            result_data = result.get('result', {})
            return KafkaTopicResponse(
                success=True,
                topic=result_data.get('topic', request.topic),
                partitions=result_data.get('partitions', request.num_partitions),
                replication_factor=result_data.get('replication_factor', request.replication_factor)
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to create topic'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create topic: {str(e)}")


@router.get("/topics", response_model=TopicListResponse, summary="List all Kafka topics")
async def list_topics(
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    List all available Kafka topics.
    
    This endpoint returns all topics currently available in the Kafka cluster.
    """
    try:
        result = await kafka_client.call_tool("list_topics", {})
        
        if result.get('success'):
            result_data = result.get('result', {})
            return {
                "success": True,
                "topics": result_data.get('topics', []),
                "count": len(result_data.get('topics', []))
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to list topics'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list topics: {str(e)}")


@router.get("/topics/{topic_name}/metadata", response_model=TopicMetadataResponse, summary="Get topic metadata")
async def get_topic_metadata(
    topic_name: str,
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Get detailed metadata for a specific topic.
    
    This endpoint returns partition count, replication factor, and other topic details.
    """
    try:
        result = await kafka_client.call_tool("get_topic_metadata", {
            'topic': topic_name
        })
        
        if result.get('success'):
            return {
                "success": True,
                "topic": topic_name,
                "metadata": result.get('result', {})
            }
        else:
            raise HTTPException(status_code=404, detail=f"Topic '{topic_name}' not found or error: {result.get('error')}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get topic metadata: {str(e)}")


@router.delete("/topics/{topic_name}", summary="Delete Kafka topic")
async def delete_topic(
    topic_name: str,
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Delete a Kafka topic.
    
    Warning: This permanently deletes the topic and all its data.
    """
    try:
        result = await kafka_client.call_tool("delete_topic", {
            'topic': topic_name
        })
        
        if result.get('success'):
            return {
                "success": True,
                "message": f"Topic '{topic_name}' deleted successfully"
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to delete topic'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete topic: {str(e)}")


@router.get("/cluster/info", response_model=ClusterInfoResponse, summary="Get Kafka cluster information")
async def get_cluster_info(
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Get Kafka cluster information including brokers and configuration.
    """
    try:
        result = await kafka_client.call_tool("describe_cluster", {})
        
        if result.get('success'):
            return {
                "success": True,
                "cluster": result.get('result', {})
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to get cluster info'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cluster info: {str(e)}")


@router.post("/query/publish", response_model=KafkaMessageResponse, summary="Publish customer query to stream")
async def publish_customer_query(
    request: QueryRequest,
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Publish a customer query to the streaming pipeline.
    
    This endpoint publishes customer queries to Kafka for real-time processing
    by the agentic AI system.
    """
    try:
        query_data = {
            'query_id': f"query_{datetime.utcnow().isoformat()}_{request.customer_id}",
            'customer_id': request.customer_id,
            'query_text': request.query,
            'priority': request.priority.value if request.priority else 'medium',
            'category': request.query_type.value if request.query_type else 'general',
            'context': request.context,
            'metadata': request.metadata,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        result = await kafka_client.publish_customer_query(query_data)
        
        if result.get('success'):
            result_data = result.get('result', {})
            return KafkaMessageResponse(
                success=True,
                topic=result_data.get('topic', 'customer-support-queries'),
                partition=result_data.get('partition'),
                offset=result_data.get('offset'),
                timestamp=datetime.utcnow()
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to publish query'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish query: {str(e)}")


@router.post("/query/streaming", response_model=StreamingQueryResponse, summary="Process query with streaming")
async def process_streaming_query(
    request: StreamingQueryRequest,
    background_tasks: BackgroundTasks,
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep),
    query_service: QueryService = Depends(get_query_service_dep)
):
    """
    Process a customer query with real-time streaming capabilities.
    
    This endpoint initiates query processing and returns a stream identifier
    for real-time updates.
    """
    try:
        # Generate unique query ID
        query_id = f"stream_query_{datetime.utcnow().isoformat()}_{request.customer_id}"
        
        # Publish query to Kafka for processing
        query_data = {
            'query_id': query_id,
            'customer_id': request.customer_id,
            'query_text': request.query,
            'stream_response': request.stream_response,
            'callback_url': request.callback_url,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Publish to Kafka
        await kafka_client.publish_customer_query(query_data)
        
        # If streaming is enabled, start background processing
        if request.stream_response:
            background_tasks.add_task(_process_streaming_query_background, query_id, request, query_service, kafka_client)
        
        return StreamingQueryResponse(
            query_id=query_id,
            status="processing",
            stream_id=f"stream_{query_id}" if request.stream_response else None,
            estimated_completion=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate streaming query: {str(e)}")


@router.get("/query/{query_id}/stream", summary="Stream query processing updates")
async def stream_query_updates(
    query_id: str,
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Stream real-time updates for a query being processed.
    
    This endpoint provides Server-Sent Events (SSE) for real-time updates
    on query processing status.
    """
    async def event_stream():
        try:
            # Monitor the responses topic for updates on this query
            while True:
                result = await kafka_client.call_tool("consume_messages", {
                    'topic': 'customer-support-responses',
                    'max_messages': 10,
                    'timeout_ms': 1000
                })
                
                if result.get('success'):
                    messages = result.get('result', {}).get('messages', [])
                    for message in messages:
                        message_data = message.get('value', {})
                        if message_data.get('query_id') == query_id:
                            yield f"data: {json.dumps(message_data)}\n\n"
                
                await asyncio.sleep(1)  # Poll every second
                
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/plain")


@router.post("/setup", response_model=CustomerSupportSetupResponse, summary="Setup customer support topics")
async def setup_customer_support_topics(
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Setup standard customer support Kafka topics.
    
    This endpoint creates the standard topics needed for customer support streaming.
    """
    try:
        result = await kafka_client.create_customer_support_topics()
        
        if result.get('success'):
            return {
                "success": True,
                "message": "Customer support topics created successfully",
                "topics": [
                    f"{kafka_client.topic_prefix}-queries",
                    f"{kafka_client.topic_prefix}-responses", 
                    f"{kafka_client.topic_prefix}-tickets",
                    f"{kafka_client.topic_prefix}-analytics"
                ]
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create topics")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to setup topics: {str(e)}")


# Background task for processing streaming queries
async def _process_streaming_query_background(
    query_id: str,
    request: StreamingQueryRequest,
    query_service: QueryService,
    kafka_client: OptimizedKafkaMCPClient
):
    """Background task to process streaming queries and publish responses."""
    try:
        # Convert to QueryRequest for processing
        query_request = QueryRequest(
            query=request.query,
            customer_id=request.customer_id,
            query_type="general",
            priority="medium"
        )
        
        # Process the query
        response = await query_service.process_query(query_request)
        
        # Publish response to Kafka
        response_data = {
            'query_id': query_id,
            'agent_id': 'streaming_agent',
            'response_text': response.response,
            'confidence': response.confidence,
            'processing_time': response.processing_time,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await kafka_client.publish_agent_response(response_data)
        
        # If callback URL provided, notify
        if request.callback_url:
            # TODO: Implement webhook callback
            pass
            
    except Exception as e:
        # Publish error response
        error_data = {
            'query_id': query_id,
            'agent_id': 'streaming_agent',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        await kafka_client.publish_agent_response(error_data)


@router.post("/customer-support/query", summary="Publish customer query to Kafka")
async def publish_customer_query(
    query_data: Dict[str, Any],
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Publish a customer query to the appropriate Kafka topic for processing.
    
    This endpoint publishes customer queries to the streaming pipeline.
    """
    try:
        result = await kafka_client.publish_customer_query(query_data)
        
        if result.get('success'):
            return {
                "success": True,
                "message": "Customer query published successfully",
                "result": result.get('result', {})
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to publish query'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish customer query: {str(e)}")


@router.post("/customer-support/response", summary="Publish agent response to Kafka")
async def publish_agent_response(
    response_data: Dict[str, Any],
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Publish an agent response to the appropriate Kafka topic.
    
    This endpoint publishes agent responses to the streaming pipeline.
    """
    try:
        result = await kafka_client.publish_agent_response(response_data)
        
        if result.get('success'):
            return {
                "success": True,
                "message": "Agent response published successfully",
                "result": result.get('result', {})
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to publish response'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish agent response: {str(e)}")


@router.get("/customer-support/queries", summary="Get recent customer queries")
async def get_recent_queries(
    limit: int = 10,
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Get recent customer queries from the Kafka topic.
    """
    try:
        result = await kafka_client.call_tool("consume_messages", {
            'topic': f"{kafka_client.topic_prefix}-queries",
            'max_messages': limit,
            'timeout_ms': 5000
        })
        
        if result.get('success'):
            result_data = result.get('result', {})
            messages = result_data.get('messages', [])
            
            return {
                "success": True,
                "queries": [msg.get('value', {}) for msg in messages],
                "count": len(messages)
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to get queries'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent queries: {str(e)}")


@router.get("/customer-support/responses", summary="Get recent agent responses")
async def get_recent_responses(
    limit: int = 10,
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Get recent agent responses from the Kafka topic.
    """
    try:
        result = await kafka_client.call_tool("consume_messages", {
            'topic': f"{kafka_client.topic_prefix}-responses",
            'max_messages': limit,
            'timeout_ms': 5000
        })
        
        if result.get('success'):
            result_data = result.get('result', {})
            messages = result_data.get('messages', [])
            
            return {
                "success": True,
                "responses": [msg.get('value', {}) for msg in messages],
                "count": len(messages)
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to get responses'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent responses: {str(e)}")


@router.get("/health", response_model=HealthCheckResponse, summary="Check Kafka MCP client health")
async def health_check(
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Check the health status of the Kafka MCP client and connection.
    """
    try:
        # Test connection by listing topics
        result = await kafka_client.call_tool("list_topics", {})
        
        return {
            "status": "healthy" if result.get('success') else "unhealthy",
            "connected": kafka_client.connected,
            "client_type": "OptimizedKafkaMCPClient",
            "bootstrap_servers": kafka_client.bootstrap_servers,
            "topic_prefix": kafka_client.topic_prefix,
            "test_result": result
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


# Advanced streaming operations
@router.post("/stream/start-consumer", summary="Start a background consumer")
async def start_background_consumer(
    topic: str,
    consumer_id: str,
    background_tasks: BackgroundTasks,
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Start a background consumer for real-time message processing.
    
    This creates a long-running consumer that can process messages asynchronously.
    """
    try:
        # Register the consumer
        if consumer_id in kafka_client.active_consumers:
            raise HTTPException(status_code=400, detail=f"Consumer '{consumer_id}' already exists")
        
        # Add background task to start consumer
        background_tasks.add_task(_start_consumer_background, topic, consumer_id, kafka_client)
        
        return {
            "success": True,
            "message": f"Background consumer '{consumer_id}' started for topic '{topic}'"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start consumer: {str(e)}")


@router.post("/stream/stop-consumer/{consumer_id}", summary="Stop a background consumer")
async def stop_background_consumer(
    consumer_id: str,
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Stop a background consumer.
    """
    try:
        if consumer_id not in kafka_client.active_consumers:
            raise HTTPException(status_code=404, detail=f"Consumer '{consumer_id}' not found")
        
        # Stop the consumer
        consumer = kafka_client.active_consumers.pop(consumer_id)
        if hasattr(consumer, 'close'):
            consumer.close()
        
        return {
            "success": True,
            "message": f"Consumer '{consumer_id}' stopped successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop consumer: {str(e)}")


@router.get("/stream/consumers", summary="List active consumers")
async def list_active_consumers(
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    List all active background consumers.
    """
    return {
        "success": True,
        "active_consumers": list(kafka_client.active_consumers.keys()),
        "count": len(kafka_client.active_consumers)
    }


# Background task functions
async def _start_consumer_background(topic: str, consumer_id: str, kafka_client: OptimizedKafkaMCPClient):
    """Background task to run a Kafka consumer."""
    try:
        # This is a simplified implementation
        # In a real scenario, you'd want more sophisticated consumer management
        kafka_client.active_consumers[consumer_id] = {
            'topic': topic,
            'started_at': datetime.utcnow().isoformat(),
            'status': 'running'
        }
        
        # Simulate consumer running
        while consumer_id in kafka_client.active_consumers:
            # Consume messages and process them
            result = await kafka_client.call_tool("consume_messages", {
                'topic': topic,
                'max_messages': 5,
                'timeout_ms': 1000
            })
            
            if result.get('success'):
                messages = result.get('result', {}).get('messages', [])
                for message in messages:
                    # Process message (could call other services, emit events, etc.)
                    logger.info(f"Consumer {consumer_id} processed message: {message.get('value', {})}")
            
            await asyncio.sleep(2)  # Poll interval
            
    except Exception as e:
        logger.error(f"Consumer {consumer_id} error: {e}")
        if consumer_id in kafka_client.active_consumers:
            kafka_client.active_consumers.pop(consumer_id)


# Add new endpoints for Postgres-Kafka consumer management

@router.post("/consumer/start", response_model=ConsumerStartResponse, summary="Start Postgres-Kafka consumer")
async def start_postgres_consumer(
    topics: Optional[List[str]] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Start the Postgres-Kafka consumer to automatically insert Kafka messages into PostgreSQL tables.
    
    This endpoint initializes and starts a consumer that bridges Kafka streaming data
    with persistent PostgreSQL storage.
    """
    try:
        from ..services.postgres_kafka_consumer import create_postgres_kafka_consumer
        from ..services.service_factory import get_postgres_client
        
        # Get PostgreSQL client
        postgres_client = get_postgres_client()
        if not postgres_client:
            raise HTTPException(status_code=503, detail="PostgreSQL MCP client not available")
        
        # Create consumer
        consumer = await create_postgres_kafka_consumer(kafka_client, postgres_client)
        
        # Store consumer reference globally (in production, use proper state management)
        if not hasattr(kafka_client, 'postgres_consumer'):
            kafka_client.postgres_consumer = consumer
        
        # Start consuming
        background_tasks.add_task(consumer.start_consuming, topics)
        
        return {
            "success": True,
            "message": "Postgres-Kafka consumer started successfully",
            "topics": topics or list(consumer.table_mappings.keys()),
            "table_mappings": {topic: mapping.table for topic, mapping in consumer.table_mappings.items()}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start Postgres consumer: {str(e)}")


@router.post("/consumer/stop", summary="Stop Postgres-Kafka consumer")
async def stop_postgres_consumer(
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Stop the Postgres-Kafka consumer.
    """
    try:
        consumer = getattr(kafka_client, 'postgres_consumer', None)
        if not consumer:
            raise HTTPException(status_code=404, detail="No active Postgres consumer found")
        
        await consumer.stop_consuming()
        
        return {
            "success": True,
            "message": "Postgres-Kafka consumer stopped successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop Postgres consumer: {str(e)}")


@router.get("/consumer/status", response_model=ConsumerStatusResponse, summary="Get Postgres-Kafka consumer status")
async def get_postgres_consumer_status(
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Get the status and statistics of the Postgres-Kafka consumer.
    """
    try:
        consumer = getattr(kafka_client, 'postgres_consumer', None)
        if not consumer:
            return {
                "success": True,
                "running": False,
                "message": "No Postgres consumer active"
            }
        
        stats = consumer.get_stats()
        return {
            "success": True,
            **stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get consumer status: {str(e)}")


@router.post("/consumer/setup-tables", response_model=TableSetupResponse, summary="Setup database tables for Kafka consumer")
async def setup_consumer_tables(
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Create the necessary database tables for the Postgres-Kafka consumer.
    
    This creates tables for:
    - customer_queries
    - agent_responses  
    - support_tickets
    - analytics_events
    """
    try:
        from ..services.postgres_kafka_consumer import create_postgres_kafka_consumer
        from ..services.service_factory import get_postgres_client
        
        # Get PostgreSQL client
        postgres_client = get_postgres_client()
        if not postgres_client:
            raise HTTPException(status_code=503, detail="PostgreSQL MCP client not available")
        
        # Create consumer (just for table creation)
        consumer = await create_postgres_kafka_consumer(kafka_client, postgres_client)
        
        return {
            "success": True,
            "message": "Database tables created successfully",
            "tables": [
                "customer_queries",
                "agent_responses", 
                "support_tickets",
                "analytics_events"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to setup tables: {str(e)}")


@router.post("/consumer/test-insert", response_model=TestInsertResponse, summary="Test inserting a sample record")
async def test_consumer_insert(
    table: str = "customer_queries",
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Test the consumer by inserting a sample record into the specified table.
    """
    try:
        # Sample test data for different tables
        test_data = {
            "customer_queries": {
                "query_id": f"test-query-{datetime.utcnow().isoformat()}",
                "customer_id": "test-customer-001",
                "query_text": "This is a test query from the API",
                "priority": "normal",
                "category": "test"
            },
            "agent_responses": {
                "query_id": "test-query-001",
                "agent_id": "test-agent",
                "response_text": "This is a test response",
                "confidence": 0.95
            },
            "support_tickets": {
                "ticket_id": f"test-ticket-{datetime.utcnow().isoformat()}",
                "customer_id": "test-customer-001",
                "title": "Test Ticket",
                "description": "This is a test ticket",
                "status": "open"
            },
            "analytics_events": {
                "event_type": "test_event",
                "customer_id": "test-customer-001",
                "event_data": {"source": "api_test"}
            }
        }
        
        if table not in test_data:
            raise HTTPException(status_code=400, detail=f"Unknown table: {table}")
        
        # Publish test message to Kafka
        topic_mapping = {
            "customer_queries": "customer-support-queries",
            "agent_responses": "customer-support-responses",
            "support_tickets": "customer-support-tickets",
            "analytics_events": "customer-support-analytics"
        }
        
        topic = topic_mapping.get(table)
        if not topic:
            raise HTTPException(status_code=400, detail=f"No topic mapping for table: {table}")
        
        # Publish test message
        result = await kafka_client.call_tool("publish_message", {
            'topic': topic,
            'message': test_data[table],
            'key': f"test-{table}"
        })
        
        if result.get('success'):
            return {
                "success": True,
                "message": f"Test message published to {topic} for table {table}",
                "test_data": test_data[table],
                "kafka_result": result.get('result', {})
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to publish test message: {result.get('error')}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test insert: {str(e)}")


@router.get("/consumer/query-database", response_model=DatabaseQueryResponse, summary="Query consumer database tables")
async def query_consumer_tables(
    table: str = "customer_queries",
    limit: int = 10,
    kafka_client: OptimizedKafkaMCPClient = Depends(get_kafka_client_dep)
):
    """
    Query the consumer database tables to see inserted records.
    """
    try:
        from ..services.service_factory import get_postgres_client
        
        # Get PostgreSQL client
        postgres_client = get_postgres_client()
        if not postgres_client:
            raise HTTPException(status_code=503, detail="PostgreSQL MCP client not available")
        
        # Valid tables
        valid_tables = ["customer_queries", "agent_responses", "support_tickets", "analytics_events"]
        if table not in valid_tables:
            raise HTTPException(status_code=400, detail=f"Invalid table. Must be one of: {valid_tables}")
        
        # Query the table
        sql = f'SELECT * FROM "{table}" ORDER BY created_at DESC LIMIT %s'
        result = await postgres_client.call_tool("execute_query", {
            'sql': sql,
            'params': [limit]
        })
        
        if result.get('success'):
            rows = result.get('result', {}).get('rows', [])
            return {
                "success": True,
                "table": table,
                "count": len(rows),
                "records": rows
            }
        else:
            raise HTTPException(status_code=500, detail=f"Database query failed: {result.get('error')}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query database: {str(e)}")
