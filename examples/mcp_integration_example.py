"""
Example demonstrating MCP integration with Customer Support AI system
"""
import asyncio
import os
import json
import logging
from typing import Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import MCP components
# from mcp.postgres_mcp_wrapper import PostgresMCPWrapper  # REMOVED - use postgres_mcp_client instead
from src.mcp.postgres_mcp_client import OptimizedPostgreSQLMCPClient
from mcp.kafka_mcp_wrapper import KafkaMCPWrapper, ExternalKafkaMCPConfig
from mcp.aws_mcp_wrapper import AWSMCPWrapper, ExternalMCPConfig
from src.mcp.mcp_client_manager import MCPClientManager

# Import data sources
from src.data_sources.rdbms_connector import RDBMSConnector


class CustomerSupportMCPOrchestrator:
    """Orchestrates customer support operations using MCP servers"""
    
    def __init__(self):
        self.mcp_manager = MCPClientManager()
        self.db_server = None
        self.kafka_server = None
        self.aws_server = None
    
    async def initialize_servers(self):
        """Initialize all MCP servers"""
        logger.info("Initializing MCP servers...")
        
        try:
            # Initialize Database MCP Wrapper
            db_connection_string = os.getenv("DATABASE_URL", "postgresql://admin:password@localhost:5432/customer_support")
            self.db_server = OptimizedPostgreSQLMCPClient(connection_string=db_connection_string)
            await self.db_server.initialize()
            logger.info("Database MCP wrapper started")
            
            # Initialize Kafka MCP Server
            kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
            kafka_config = ExternalKafkaMCPConfig(
                bootstrap_servers=kafka_servers,
                topic_name="example-topic",
                group_id="example-group"
            )
            self.kafka_server = KafkaMCPWrapper(kafka_config)
            await self.kafka_server.initialize()
            logger.info("Kafka MCP server started")
            
            # Initialize AWS MCP Wrapper
            aws_config = ExternalMCPConfig(
                aws_profile=os.getenv("AWS_PROFILE", "default"),
                aws_region=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
            )
            self.aws_server = AWSMCPWrapper(aws_config)
            await self.aws_server.initialize()
            logger.info("AWS MCP wrapper started")
            
            # Set up MCP client connections
            await self.setup_client_connections()
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP servers: {e}")
            raise
    
    async def setup_client_connections(self):
        """Set up MCP client connections to servers"""
        # Note: In a real implementation, these would be WebSocket connections
        # For this example, we'll directly use the server instances
        self.mcp_manager.clients["mcp_database"] = self.db_server
        self.mcp_manager.clients["mcp_kafka"] = self.kafka_server
        self.mcp_manager.clients["mcp_aws"] = self.aws_server
        
        logger.info("MCP client connections established")
    
    async def process_customer_query(self, customer_id: str, query: str) -> Dict[str, Any]:
        """Process a customer query using MCP services"""
        logger.info(f"Processing query for customer {customer_id}: {query}")
        
        try:
            # Step 1: Get customer context from database
            customer_context = await self.db_server.call_tool("get_customer_context", {
                "customer_id": customer_id
            })
            
            if not customer_context.get("success"):
                logger.error(f"Failed to get customer context: {customer_context.get('error')}")
                return {"success": False, "error": "Customer not found"}
            
            # Step 2: Search knowledge base for relevant articles
            knowledge_search = await self.db_server.call_tool("search_knowledge_base", {
                "search_term": query,
                "limit": 5
            })
            
            # Step 3: Publish query to Kafka for async processing
            kafka_message = {
                "customer_id": customer_id,
                "query": query,
                "customer_context": customer_context.get("customer_context"),
                "knowledge_articles": knowledge_search.get("articles", []),
                "timestamp": datetime.now().isoformat()
            }
            
            await self.kafka_server.call_tool("publish_message", {
                "topic": "customer-queries",
                "message": kafka_message,
                "key": f"customer-{customer_id}"
            })
            
            # Step 4: Save interaction to database
            interaction_data = {
                "query_id": f"q-{customer_id}-{int(datetime.now().timestamp())}",
                "customer_id": customer_id,
                "query_text": query,
                "agent_response": "Query received and being processed",
                "created_at": datetime.now().isoformat()
            }
            
            await self.db_server.call_tool("save_interaction", {
                "interaction_data": interaction_data
            })
            
            return {
                "success": True,
                "query_id": interaction_data["query_id"],
                "customer_context": customer_context.get("customer_context"),
                "relevant_articles": knowledge_search.get("articles", []),
                "status": "processing"
            }
            
        except Exception as e:
            logger.error(f"Error processing customer query: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_response(self, query_id: str, response_text: str) -> Dict[str, Any]:
        """Generate and store a response to a customer query"""
        logger.info(f"Generating response for query {query_id}")
        
        try:
            # Step 1: Update interaction with response
            update_query = """
                UPDATE query_interactions 
                SET agent_response = %s, updated_at = %s 
                WHERE query_id = %s
            """
            
            await self.db_server.call_tool("query_database", {
                "query": update_query,
                "params": [response_text, datetime.now().isoformat(), query_id]
            })
            
            # Step 2: Publish response to Kafka
            response_message = {
                "query_id": query_id,
                "response": response_text,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.kafka_server.call_tool("publish_message", {
                "topic": "agent-responses",
                "message": response_message,
                "key": query_id
            })
            
            # Step 3: Store response in S3 for archival (optional)
            s3_key = f"responses/{datetime.now().strftime('%Y/%m/%d')}/{query_id}.json"
            
            await self.aws_server.call_tool("s3_upload_file", {
                "bucket": "customer-support-archive",
                "key": s3_key,
                "content": json.dumps(response_message, indent=2),
                "content_type": "application/json"
            })
            
            return {
                "success": True,
                "query_id": query_id,
                "response_stored": True,
                "archive_location": f"s3://customer-support-archive/{s3_key}"
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_analytics(self, time_period: str = "7 days") -> Dict[str, Any]:
        """Get system analytics using MCP services"""
        logger.info(f"Retrieving analytics for {time_period}")
        
        try:
            # Get analytics from database
            analytics = await self.db_server.call_tool("get_analytics", {
                "time_period": time_period
            })
            
            # Get Kafka topic information
            topics_result = await self.kafka_server.call_tool("list_topics", {})
            topic_count = len(topics_result.get("result", {}).get("topics", [])) if topics_result.get("success") else 0
            
            # Combine analytics
            combined_analytics = {
                "database_analytics": analytics.get("analytics", {}),
                "kafka_topics": topic_count,
                "timestamp": datetime.now().isoformat()
            }
            
            return {"success": True, "analytics": combined_analytics}
            
        except Exception as e:
            logger.error(f"Error retrieving analytics: {e}")
            return {"success": False, "error": str(e)}
    
    async def backup_data(self) -> Dict[str, Any]:
        """Backup customer data to S3"""
        logger.info("Starting data backup")
        
        try:
            # Export customer data
            customers_data = await self.db_server.get_resource("db://customers")
            interactions_data = await self.db_server.get_resource("db://interactions")
            
            # Upload to S3
            backup_date = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup customers
            await self.aws_server.call_tool("s3_upload_file", {
                "bucket": "customer-support-backups",
                "key": f"backups/{backup_date}/customers.json",
                "content": customers_data["contents"][0]["text"],
                "content_type": "application/json"
            })
            
            # Backup interactions
            await self.aws_server.call_tool("s3_upload_file", {
                "bucket": "customer-support-backups",
                "key": f"backups/{backup_date}/interactions.json",
                "content": interactions_data["contents"][0]["text"],
                "content_type": "application/json"
            })
            
            return {
                "success": True,
                "backup_location": f"s3://customer-support-backups/backups/{backup_date}/",
                "files_backed_up": ["customers.json", "interactions.json"]
            }
            
        except Exception as e:
            logger.error(f"Error during backup: {e}")
            return {"success": False, "error": str(e)}
    
    async def shutdown(self):
        """Shutdown all MCP servers"""
        logger.info("Shutting down MCP servers...")
        
        if self.mcp_manager:
            await self.mcp_manager.disconnect_all()
        
        logger.info("MCP servers shut down successfully")


async def main():
    """Main example function"""
    orchestrator = CustomerSupportMCPOrchestrator()
    
    try:
        # Initialize MCP servers
        await orchestrator.initialize_servers()
        
        # Example 1: Process a customer query
        print("\n=== Example 1: Processing Customer Query ===")
        query_result = await orchestrator.process_customer_query(
            customer_id="CUST_12345",
            query="How do I reset my password?"
        )
        print(f"Query Result: {query_result}")
        
        # Example 2: Generate a response
        if query_result.get("success"):
            print("\n=== Example 2: Generating Response ===")
            response_result = await orchestrator.generate_response(
                query_id=query_result["query_id"],
                response_text="To reset your password, please visit the login page and click 'Forgot Password'. Follow the instructions sent to your email."
            )
            print(f"Response Result: {response_result}")
        
        # Example 3: Get analytics
        print("\n=== Example 3: Getting Analytics ===")
        analytics_result = await orchestrator.get_analytics("30 days")
        print(f"Analytics: {analytics_result}")
        
        # Example 4: Backup data
        print("\n=== Example 4: Backing Up Data ===")
        backup_result = await orchestrator.backup_data()
        print(f"Backup Result: {backup_result}")
        
    except Exception as e:
        logger.error(f"Example execution failed: {e}")
    
    finally:
        # Cleanup
        await orchestrator.shutdown()


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the example
    asyncio.run(main())
